"""MCP approval preferences persist per project and reach each agent's adapter."""

import json
import os
import subprocess
import sys

import pytest
import tomllib
from conftest import REPO
from helpers import env_value
from test_mcp import mcp_file

ADAPTER = REPO / "catalog" / "agents" / "mcp.py"


def payload(env, shop, *args):
    result = env.roke(*args, cwd=shop)
    assert result.code == 0, result.text
    path = mcp_file(result.last("run"))
    return json.loads(path.read_text()) if path else {}


@pytest.mark.parametrize("mode", ["allow", "ask"])
def test_add_sets_policy_for_all_names_and_later_add_preserves_it(env, mode):
    shop = env.project()
    result = env.roke("mcp", "add", "fetch", "context7", f"--{mode}", cwd=shop)
    assert result.code == 0, result.text
    assert env_value(env.project_env(), "ROKE_MCP_APPROVALS") == f"context7={mode},fetch={mode}"
    assert payload(env, shop)["approvals"] == {"fetch": mode, "context7": mode}
    assert env.roke("mcp", "add", "fetch", cwd=shop).code == 0
    assert payload(env, shop)["approvals"]["fetch"] == mode
    assert (
        f"tool approvals: {mode} (this project)" in env.roke("mcp", "show", "fetch", cwd=shop).out
    )


def test_project_policy_overrides_global_for_one_mcp_only(env):
    shop = env.project()
    assert (
        env.roke("mcp", "add", "fetch", "context7", "--allow", "--global", cwd=env.home).code == 0
    )
    assert env.roke("mcp", "ask", "fetch", cwd=shop).code == 0
    assert payload(env, shop)["approvals"] == {"fetch": "ask", "context7": "allow"}
    assert "tool approvals: ask (this project)" in env.roke("mcp", "show", "fetch", cwd=shop).out
    assert "tool approvals: allow (global)" in env.roke("mcp", "show", "context7", cwd=shop).out
    other = env.project("other")
    assert payload(env, other)["approvals"] == {"fetch": "allow", "context7": "allow"}
    assert env.roke("mcp", "allow", "fetch", cwd=shop).code == 0
    assert payload(env, shop)["approvals"]["fetch"] == "allow"


def test_setting_an_approval_does_not_enable_the_server(env):
    shop = env.project()
    assert env.roke("mcp", "allow", "fetch", "serena", cwd=shop).code == 0
    assert payload(env, shop) == {}
    assert "not used" in env.roke("mcp", "show", "fetch", cwd=shop).out
    shown = env.roke("mcp", "show", "serena", cwd=shop)
    assert "disabled" in shown.out
    assert "tool approvals: allow (this project)" in shown.out
    assert payload(env, shop, "--serena")["approvals"] == {"serena": "allow"}


def test_serena_add_remove_and_approval_keep_builtin_settings_compatible(env):
    shop = env.project()
    result = env.roke("mcp", "add", "serena", "--allow", cwd=shop)
    assert result.code == 0, result.text
    assert env_value(env.project_env(), "ROKE_SERENA") == "1"
    assert env_value(env.project_env(), "ROKE_MCPS") is None
    assert payload(env, shop)["approvals"] == {"serena": "allow"}
    assert "* serena" in env.roke("mcp", cwd=shop).out
    assert env.roke("mcp", "ask", "serena", cwd=shop).code == 0
    assert payload(env, shop)["approvals"] == {"serena": "ask"}
    assert env.roke("mcp", "rm", "serena", cwd=shop).code == 0
    assert env_value(env.project_env(), "ROKE_SERENA") == "0"
    assert env_value(env.project_env(), "ROKE_MCP_APPROVALS") is None


def test_remove_clears_only_the_policy_at_that_scope(env):
    shop = env.project()
    assert env.roke("mcp", "allow", "fetch", "--global", cwd=shop).code == 0
    assert env.roke("mcp", "add", "fetch", "context7", "--ask", cwd=shop).code == 0
    assert env.roke("mcp", "rm", "fetch", cwd=shop).code == 0
    assert env_value(env.project_env(), "ROKE_MCP_APPROVALS") == "context7=ask"
    assert env_value(env.config / "roke.env", "ROKE_MCP_APPROVALS") == "fetch=allow"
    assert env.roke("mcp", "add", "fetch", cwd=shop).code == 0
    assert payload(env, shop)["approvals"] == {"fetch": "allow", "context7": "ask"}


@pytest.mark.parametrize(
    "args",
    [
        ("mcp", "add", "fetch", "--allow", "--ask"),
        ("mcp", "rm", "fetch", "--allow"),
        ("service", "add", "postgres", "--ask"),
        ("mcp", "add", "fetch", "no-such-mcp", "--allow"),
        ("mcp", "allow", "fetch", "no-such-mcp"),
    ],
)
def test_invalid_requests_do_not_change_project_settings(env, args):
    shop = env.project()
    env.write_project_env("ROKE_MCPS=context7\n")
    before = env.project_env().read_text()
    result = env.roke(*args, cwd=shop)
    assert result.code != 0
    assert env.project_env().read_text() == before
    assert not result.compose_calls("run")


def test_invalid_policy_and_wildcard_names_are_rejected(env):
    shop = env.project()
    own = env.config / "mcps" / "wild*" / "mcp.json"
    own.parent.mkdir(parents=True)
    own.write_text('{"command": ["example"]}')
    result = env.roke("mcp", "add", "wild*", "--allow", cwd=shop)
    assert result.code != 0
    assert "letters, digits" in result.err
    assert not env.project_env().exists()
    env.write_project_env('ROKE_MCP_APPROVALS="fetch=never"\n')
    result = env.roke(cwd=shop)
    assert result.code != 0
    assert "NAME=allow or NAME=ask" in result.err
    assert not result.compose_calls("run")


def test_revoking_replaces_duplicate_allow_assignments(env):
    shop = env.project()
    env.write_project_env(
        'ROKE_MCPS=fetch\nROKE_MCP_APPROVALS="fetch=allow"\nROKE_MCP_APPROVALS="fetch=allow"\n'
    )
    result = env.roke("mcp", "ask", "fetch", cwd=shop)
    assert result.code == 0, result.text
    assert env.project_env().read_text().count("ROKE_MCP_APPROVALS=") == 1
    assert payload(env, shop)["approvals"] == {"fetch": "ask"}


def test_removing_an_inherited_server_does_not_drop_its_project_restriction(env):
    shop = env.project()
    assert env.roke("mcp", "add", "fetch", "--allow", "--global", cwd=shop).code == 0
    assert env.roke("mcp", "ask", "fetch", cwd=shop).code == 0
    result = env.roke("mcp", "rm", "fetch", cwd=shop)
    assert "enabled in every project" in result.err
    assert payload(env, shop)["approvals"] == {"fetch": "ask"}


def adapter(agent, file, *args, **extra):
    return subprocess.run(
        [sys.executable, str(ADAPTER), agent, str(file), *args],
        env={**os.environ, **extra},
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.mark.parametrize("agent", ["codex", "claude", "opencode"])
@pytest.mark.parametrize("mode", ["allow", "ask"])
def test_cli_preferences_translate_to_each_agent_with_builtin_serena(env, agent, mode):
    shop = env.project()
    assert env.roke("mcp", "add", "context7", "serena", f"--{mode}", cwd=shop).code == 0
    call = env.roke(cwd=shop).last("run")
    path = mcp_file(call)
    result = adapter(
        agent, path, "--serena", "env", "SERENA_USAGE_REPORTING=false", "serena", "--context", agent
    )
    assert result.returncode == 0, result.stderr
    if agent == "codex":
        servers = tomllib.loads(result.stdout)["mcp_servers"]
        for name in ("context7", "serena"):
            assert servers[name]["default_tools_approval_mode"] == (
                "approve" if mode == "allow" else "prompt"
            )
        assert servers["serena"]["startup_timeout_sec"] == 120
        assert servers["serena"]["args"][-1] == agent
    elif agent == "claude":
        assert json.loads(result.stdout)["serena"]["type"] == "stdio"
        policy = adapter(agent, path, "--permissions", "--serena", "serena")
        assert json.loads(policy.stdout)["permissions"] == {
            mode: ["mcp__context7__*", "mcp__serena__*"]
        }
    else:
        config = json.loads(result.stdout)
        for name in ("context7", "serena"):
            assert {"action": name + "_*", "resource": "*", "effect": mode} in config["permissions"]
            assert {
                "action": "opencode_read_mcp_resource",
                "resource": name + ":*",
                "effect": mode,
            } in config["permissions"]
        assert config["mcp"]["servers"]["serena"]["timeout"] == {"startup": 120000}


@pytest.mark.parametrize("agent", ["codex", "claude", "opencode"])
def test_absent_policy_keeps_native_defaults_and_only_active_servers_get_rules(tmp_path, agent):
    path = tmp_path / "mcps.json"
    path.write_text(
        json.dumps(
            {
                "servers": {"fetch": {"type": "local", "command": ["uvx", "fetch"], "env": {}}},
                "approvals": {"github": "allow"},
            }
        )
    )
    result = adapter(agent, path)
    assert result.returncode == 0, result.stderr
    assert "approve" not in result.stdout and "prompt" not in result.stdout
    if agent == "claude":
        assert json.loads(adapter(agent, path, "--permissions").stdout) == {}
    elif agent == "opencode":
        assert "permissions" not in json.loads(result.stdout)


@pytest.mark.parametrize(
    "agent,names",
    [
        ("opencode", ["docs", "docs_extra"]),
        ("opencode", ["my_docs", "my.docs"]),
        ("opencode", ["opencode"]),
        ("opencode", ["external"]),
        ("claude", ["docs", "docs__extra"]),
    ],
)
def test_ambiguous_server_patterns_cannot_authorize_other_servers(tmp_path, agent, names):
    path = tmp_path / "mcps.json"
    path.write_text(
        json.dumps(
            {
                "servers": {
                    name: {"type": "local", "command": ["example"], "env": {}} for name in names
                },
                "approvals": {names[0]: "allow"},
            }
        )
    )
    args = ["--permissions"] if agent == "claude" else []
    result = adapter(agent, path, *args)
    assert result.returncode != 0
    assert "ambiguous" in result.stderr


def test_opencode_preserves_hyphens_in_server_names(tmp_path):
    path = tmp_path / "mcps.json"
    path.write_text(
        json.dumps(
            {
                "servers": {
                    name: {"type": "local", "command": ["example"], "env": {}}
                    for name in ("my-docs", "my_docs")
                },
                "approvals": {"my-docs": "allow"},
            }
        )
    )
    result = adapter("opencode", path)
    assert result.returncode == 0, result.stderr
    actions = [rule["action"] for rule in json.loads(result.stdout)["permissions"]]
    assert "my-docs_*" in actions
    assert "my_docs_*" not in actions


def test_builtin_serena_cannot_silently_replace_an_authorized_custom_server(tmp_path):
    path = tmp_path / "mcps.json"
    path.write_text(
        json.dumps(
            {
                "servers": {"serena": {"type": "local", "command": ["custom"], "env": {}}},
                "approvals": {"serena": "allow"},
            }
        )
    )
    result = adapter("codex", path, "--serena", "serena")
    assert result.returncode != 0
    assert "conflicts with built-in Serena" in result.stderr


def test_reset_goes_back_to_the_agent_default_in_the_project_only(env):
    shop = env.project()
    env.roke("mcp", "add", "fetch", "context7", "--global", cwd=shop)
    env.roke("mcp", "allow", "fetch", "context7", "--global", cwd=shop)
    env.roke("mcp", "ask", "fetch", cwd=shop)
    r = env.roke("mcp", "reset", "fetch", cwd=shop)
    assert r.code == 0 and "back to the agent's default: fetch" in r.err
    assert env_value(env.project_env(), "ROKE_MCP_APPROVALS") is None
    assert "tool approvals: allow (global)" in env.roke("mcp", "show", "fetch", cwd=shop).out
    r = env.roke("mcp", "reset", "fetch", "--global", cwd=shop)
    assert r.code == 0
    assert env_value(env.config / "roke.env", "ROKE_MCP_APPROVALS") == "context7=allow"
    assert "tool approvals: agent default" in env.roke("mcp", "show", "fetch", cwd=shop).out


def test_reset_says_when_there_was_nothing_to_reset(env):
    shop = env.project()
    r = env.roke("mcp", "reset", "fetch", cwd=shop)
    assert r.code == 0 and "fetch has no tool approval set in shop" in r.err
    r = env.roke("mcp", "reset", "nope", cwd=shop)
    assert r.code != 0 and "unknown MCP server: 'nope'" in r.err


def test_an_approval_for_a_server_that_is_not_enabled_says_so(env):
    shop = env.project()
    r = env.roke("mcp", "allow", "context7", cwd=shop)
    assert r.code == 0
    assert "note: context7 is not enabled here (roke mcp add context7)" in r.err
    env.roke("mcp", "add", "context7", cwd=shop)
    assert "not enabled here" not in env.roke("mcp", "ask", "context7", cwd=shop).err
    assert "not enabled here" not in env.roke("mcp", "allow", "fetch", "--global", cwd=shop).err
