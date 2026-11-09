"""roke mcp: MCP servers managed like services, and what reaches the box."""

import json
import stat
from pathlib import Path

from helpers import env_value


def mcp_file(call):
    """The resolved MCP configuration mounted in the box, if any."""
    for arg in call["args"]:
        if arg.endswith(":/run/roke/mcp.json:ro"):
            return Path(arg.split(":")[0])
    return None


def test_list_shows_the_catalog(env):
    out = env.roke("mcp", cwd=env.project()).out
    for name in ("github", "context7", "fetch"):
        assert f"  {name} " in out


def test_add_and_rm_in_the_project_and_globally(env):
    shop = env.project()
    assert env.roke("mcp", "add", "fetch", cwd=shop).code == 0
    assert env_value(env.project_env(), "ROKE_MCPS") == "fetch"
    assert env.roke("mcp", "add", "context7", "--global", cwd=shop).code == 0
    assert env_value(env.config / "roke.env", "ROKE_MCPS") == "context7"
    lines = env.roke("mcp", cwd=shop).out.splitlines()
    assert any(line.startswith("* fetch") for line in lines)
    assert any(line.startswith("* context7") for line in lines)
    r = env.roke("mcp", "rm", "context7", cwd=shop)
    assert "enabled in every project: roke mcp rm context7 --global" in r.err
    env.roke("mcp", "rm", "fetch", cwd=shop)
    assert env_value(env.project_env(), "ROKE_MCPS") is None


def test_add_validates_every_name_first(env):
    shop = env.project()
    r = env.roke("mcp", "add", "fetch", "nope", cwd=shop)
    assert r.code != 0 and "unknown MCP server" in r.err
    assert not env.project_env().exists() or env_value(env.project_env(), "ROKE_MCPS") is None


def test_missing_secrets_leave_the_server_out(env):
    shop = env.project()
    r = env.roke("mcp", "add", "github", cwd=shop)
    assert "github needs GITHUB_PAT" in r.err
    r = env.roke(cwd=shop)
    assert "MCP github left out: set GITHUB_PAT" in r.err
    assert mcp_file(r.last("run")) is None
    assert "github (left out: needs secrets)" in env.roke("settings", cwd=shop).out


def test_resolved_servers_reach_the_box(env):
    shop = env.project()
    env.append(env.config / "secrets.env", "GITHUB_PAT=ghp_secret\n")
    env.roke("mcp", "add", "github", "fetch", "context7", cwd=shop)
    call = env.roke(cwd=shop).last("run")
    path = mcp_file(call)
    assert path and stat.S_IMODE(path.stat().st_mode) == 0o600
    servers = json.loads(path.read_text())["servers"]
    assert servers["github"] == {
        "type": "remote",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {"Authorization": "Bearer ghp_secret"},
    }
    assert servers["fetch"]["type"] == "local"
    assert servers["fetch"]["command"][0] == "uvx"
    # Context7's key is optional: without it, its header is left out.
    assert servers["context7"]["headers"] == {}


def test_mcp_destinations_are_allowed(env):
    shop = env.project()
    env.append(env.config / "secrets.env", "GITHUB_PAT=ghp_secret\n")
    env.roke("mcp", "add", "github", cwd=shop)
    allowed = env.roke(cwd=shop).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"].split()
    assert "api.githubcopilot.com" in allowed
    out = env.roke("network", cwd=shop).out
    assert "  mcps       catalog/mcps/<name>/mcp.json" in out and "api.githubcopilot.com" in out


def test_own_mcps(env):
    shop = env.project()
    own = env.config / "mcps" / "mine" / "mcp.json"
    own.parent.mkdir(parents=True)
    own.write_text(json.dumps({"description": "Mine", "command": ["mine-mcp", "${MINE_ARG}"]}))
    assert "[yours] Mine" in env.roke("mcp", cwd=shop).out
    env.roke("mcp", "add", "mine", cwd=shop)
    assert mcp_file(env.roke(cwd=shop).last("run")) is None  # MINE_ARG not set
    env.append(env.config / "roke.env", "MINE_ARG=x\n")
    servers = json.loads(mcp_file(env.roke(cwd=shop).last("run")).read_text())["servers"]
    assert servers["mine"]["command"] == ["mine-mcp", "x"]


def test_invalid_definitions(env):
    shop = env.project()
    bad = env.config / "mcps" / "bad" / "mcp.json"
    bad.parent.mkdir(parents=True)
    bad.write_text(json.dumps({"command": ["x"], "url": "https://x"}))
    r = env.roke("mcp", "add", "bad", cwd=shop)
    assert r.code != 0 and "either a command (local) or a url (remote)" in r.err
    assert not env.project_env().exists() or env_value(env.project_env(), "ROKE_MCPS") is None
    env.write_project_env("ROKE_MCPS=bad\n")  # set by hand
    r = env.roke(cwd=shop)
    assert r.code != 0 and "either a command (local) or a url (remote)" in r.err


def test_malformed_mcp_fields_are_reported_before_changing_settings(env):
    shop = env.project()
    bad = env.config / "mcps" / "bad" / "mcp.json"
    bad.parent.mkdir(parents=True)
    cases = [
        ({"command": []}, "command"),
        ({"command": "uvx"}, "command"),
        ({"url": 42}, "url"),
        ({"url": "https://example.com", "headers": ["bad"]}, "headers"),
        ({"command": ["uvx"], "env": {"TOKEN": 1}}, "env"),
        ({"command": ["uvx"], "services": "postgres"}, "services"),
        ({"command": ["uvx"], "requires": [42]}, "requires"),
    ]
    for definition, field in cases:
        bad.write_text(json.dumps(definition))
        r = env.roke("mcp", "add", "bad", cwd=shop)
        assert r.code != 0 and str(bad) in r.err and field in r.err
        assert not env.project_env().exists() or env_value(env.project_env(), "ROKE_MCPS") is None


def test_an_mcp_starts_the_services_it_needs(env):
    shop = env.project()
    env.roke("mcp", "add", "grafana", cwd=shop)
    call = env.roke(cwd=shop).last("run")
    files = [a for i, a in enumerate(call["args"]) if call["args"][i - 1] == "-f"]
    assert any(f.endswith("services/grafana/compose.yaml") for f in files)
    assert call["env"]["ROKE_SERVICES"] == "grafana"
    assert env_value(env.project_env(), "GRAFANA_VERSION")  # pinned like any service
    servers = json.loads(mcp_file(call).read_text())["servers"]
    assert servers["grafana"]["env"] == {"GRAFANA_URL": "http://grafana:3000"}
    services = next(
        line
        for line in env.roke("settings", cwd=shop).out.splitlines()
        if line.startswith("Services")
    )
    assert services.startswith("Services  grafana ") and services.endswith("(for MCP grafana)")


def test_service_mcps_follow_the_project_settings(env):
    shop = env.project()
    env.roke("mcp", "add", "postgres", cwd=shop)
    servers = json.loads(mcp_file(env.roke(cwd=shop).last("run")).read_text())["servers"]
    assert servers["postgres"]["env"]["POSTGRES_DATABASE"] == "app"  # the service's default
    assert servers["postgres"]["env"]["POSTGRES_USER"] == "dev"
    env.append(env.project_env(), "POSTGRES_DB=shop\nPOSTGRES_PASSWORD=s3cret\n")
    servers = json.loads(mcp_file(env.roke(cwd=shop).last("run")).read_text())["servers"]
    assert servers["postgres"]["env"]["POSTGRES_DATABASE"] == "shop"
    assert servers["postgres"]["env"]["POSTGRES_PASSWORD"] == "s3cret"


def test_a_service_already_in_the_project_is_not_marked(env):
    shop = env.project()
    env.roke("service", "add", "postgres", cwd=shop)
    env.roke("mcp", "add", "postgres", cwd=shop)
    out = env.roke("settings", cwd=shop).out
    services = next(line for line in out.splitlines() if line.startswith("Services"))
    assert services.startswith("Services  postgres ") and "(for MCP" not in services


def test_an_mcp_needing_an_unknown_service(env):
    shop = env.project()
    own = env.config / "mcps" / "broken" / "mcp.json"
    own.parent.mkdir(parents=True)
    own.write_text(json.dumps({"url": "http://x:1/mcp", "services": ["nope"]}))
    env.roke("mcp", "add", "broken", cwd=shop)
    r = env.roke(cwd=shop)
    assert r.code != 0 and "needs the service 'nope'" in r.err


def test_penpot_url_with_its_key_and_instance(env):
    shop = env.project()
    env.roke("mcp", "add", "penpot", cwd=shop)
    assert mcp_file(env.roke(cwd=shop).last("run")) is None  # no PENPOT_MCP_KEY yet
    env.append(env.config / "secrets.env", "PENPOT_MCP_KEY=k3y\n")
    servers = json.loads(mcp_file(env.roke(cwd=shop).last("run")).read_text())["servers"]
    assert servers["penpot"]["url"] == "https://design.penpot.app/mcp/stream?userToken=k3y"
    env.append(env.config / "roke.env", "PENPOT_URL=https://penpot.example.com\n")
    servers = json.loads(mcp_file(env.roke(cwd=shop).last("run")).read_text())["servers"]
    assert servers["penpot"]["url"] == "https://penpot.example.com/mcp/stream?userToken=k3y"
