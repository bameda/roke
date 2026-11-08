import pytest
from helpers import env_value


def test_add_and_rm_in_the_project(env):
    shop = env.project()
    assert env.roke("network", "add", "db.example.com:5432", cwd=shop).code == 0
    assert env.roke("network", "add", "*.corp.example.com", cwd=shop).code == 0
    assert (
        env_value(env.project_env(), "ROKE_NETWORK_ALLOW")
        == "db.example.com:5432 *.corp.example.com"
    )
    assert "already allowed" in env.roke("network", "add", "db.example.com:5432", cwd=shop).text
    assert env.roke("network", "rm", "db.example.com:5432", cwd=shop).code == 0
    assert env_value(env.project_env(), "ROKE_NETWORK_ALLOW") == "*.corp.example.com"
    r = env.roke("network", "rm", "nothere.example.com", cwd=shop)
    assert r.code != 0 and "is not allowed" in r.err


def test_add_global(env):
    assert env.roke("network", "add", "api.example.com", "--global", cwd=env.project()).code == 0
    assert env_value(env.config / "roke.env", "ROKE_NETWORK_ALLOW") == "api.example.com"


@pytest.mark.parametrize("dest", ["bad value!", "http://x.com", "a b"])
def test_add_rejects_invalid_destinations(env, dest):
    r = env.roke("network", "add", dest, cwd=env.project())
    assert r.code != 0


def test_allowed_destinations_are_combined_in_layers(env):
    shop = env.project()
    env.roke("network", "add", "global.example.com", "--global", cwd=shop)
    env.roke("network", "add", "project.example.com", cwd=shop)
    allowed = env.roke(cwd=shop).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"].split()
    for dest in ("github.com", "api.anthropic.com", "global.example.com", "project.example.com"):
        assert dest in allowed
    assert "api.openai.com" not in allowed
    allowed = (
        env.roke("--agent", "codex", cwd=shop).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"].split()
    )
    assert "api.openai.com" in allowed


def test_network_mode(env):
    shop = env.project()
    assert env.roke(cwd=shop).last("run")["env"]["ROKE_NETWORK"] == "restricted"
    assert env.roke("--network", "open", cwd=shop).last("run")["env"]["ROKE_NETWORK"] == "open"
    env.write_project_env("ROKE_NETWORK=open\n")
    assert env.roke(cwd=shop).last("run")["env"]["ROKE_NETWORK"] == "open"
    r = env.roke("--network", "closed", cwd=shop)
    assert r.code != 0 and "restricted or open" in r.err


def test_network_lists_the_layers(env):
    shop = env.project()
    env.roke("network", "add", "project.example.com", cwd=shop)
    out = env.roke("network", cwd=shop).out
    assert "Network mode: restricted (built-in default)" in out
    for part in (
        "base",
        "agent",
        "catalog/agents/claude/allow.txt",
        "global",
        "project",
        "project.example.com",
    ):
        assert part in out


def test_blocked(env):
    shop = env.project()
    r = env.roke("network", "blocked", cwd=shop)
    assert r.code != 0 and "not running" in r.err
    r = env.roke("network", "blocked", cwd=shop, env={"FAKE_RUNNING": "1"})
    assert r.code == 0 and "blocked.example.com" in r.out


def test_one_destination_per_line(env):
    shop = env.project()
    env.roke("network", "add", "one.example.com", cwd=shop)
    env.roke("network", "add", "two.example.com", cwd=shop)
    lines = env.roke("network", cwd=shop).out.splitlines()
    assert "             one.example.com" in lines
    assert "             two.example.com" in lines
    assert "             github.com" in lines


def test_destinations_are_sorted(env):
    shop = env.project()
    for dest in ("zeta.example.com", "*.beta.example.com", "alpha.example.com"):
        env.roke("network", "add", dest, cwd=shop)
    out = env.roke("network", cwd=shop).out
    project = out.split("  project")[1].splitlines()[1:]
    assert [line.strip() for line in project] == [
        "alpha.example.com",
        "*.beta.example.com",
        "zeta.example.com",
    ]
    base = out.split("  base")[1].split("  agent")[0].splitlines()[1:]
    entries = [line.strip() for line in base]
    assert entries == sorted(entries, key=lambda e: e.removeprefix("*.").lower())


def test_a_port_of_the_host(env):
    shop = env.project()
    r = env.roke("network", "add", "host", cwd=shop)
    assert r.code != 0 and "never the whole host" in r.err
    assert env.roke("network", "add", "host:4401", cwd=shop).code == 0
    allowed = env.roke(cwd=shop).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"].split()
    assert "host:4401" in allowed


def test_blocked_marks_the_known_ones(env):
    r = env.roke("network", "blocked", cwd=env.project(), env={"FAKE_RUNNING": "1"})
    lines = r.out.splitlines()
    oraios = next(line for line in lines if "oraios-software.de" in line)
    assert "Serena's dashboard news" in oraios and "harmless" in oraios
    unknown = next(line for line in lines if "blocked.example.com" in line)
    assert unknown.rstrip().endswith("1 lookups")  # not annotated


def test_annotate_matches_domains_and_subdomains():
    import sys

    from conftest import REPO

    sys.path.insert(0, str(REPO))
    from roke.commands.network import annotate

    report = "  example.com   1 lookups\n  a.example.com   2 lookups\n  notexample.com   1 lookups"
    out = annotate(report, {"example.com": "why"}).splitlines()
    assert out[0].endswith("(why)") and out[1].endswith("(why)")
    assert out[2].endswith("1 lookups")
