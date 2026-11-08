import pytest
from helpers import allowed_in


def test_add_and_rm_in_the_project(env):
    shop = env.project()
    assert env.roke("network", "add", "db.example.com:5432", cwd=shop).code == 0
    assert env.roke("network", "add", "*.corp.example.com", cwd=shop).code == 0
    assert allowed_in(env.project_env()) == ["db.example.com:5432", "*.corp.example.com"]
    assert "already allowed" in env.roke("network", "add", "db.example.com:5432", cwd=shop).text
    assert env.roke("network", "rm", "db.example.com:5432", cwd=shop).code == 0
    assert allowed_in(env.project_env()) == ["*.corp.example.com"]
    r = env.roke("network", "rm", "nothere.example.com", cwd=shop)
    assert r.code != 0 and "is not allowed" in r.err


def test_add_global(env):
    assert env.roke("network", "add", "api.example.com", "--global", cwd=env.project()).code == 0
    assert allowed_in(env.config / "roke.env") == ["api.example.com"]


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
    assert any(line.startswith("             github.com ") for line in lines)


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


def test_base_allows_what_mise_needs_to_verify_tools(env):
    """mise verifies signatures with Sigstore's trust root, and refuses to
    install a tool it cannot verify."""
    allowed = env.roke(cwd=env.project()).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"].split()
    assert "tuf-repo-cdn.sigstore.dev" in allowed
    assert "github.com" in allowed  # and tuf-repo.github.com, GitHub's root, with it


def test_notes_on_your_destinations(env):
    shop = env.project()
    env.roke("network", "add", "ui.shadcn.com", "--note", "shadcn/ui component registry", cwd=shop)
    env.roke("network", "add", "db.example.com:5432", cwd=shop)
    env.roke("network", "add", "db.example.com:5432", "--note=staging database", cwd=shop)
    text = env.project_env().read_text()
    assert "ui.shadcn.com        # shadcn/ui component registry" in text
    assert "db.example.com:5432  # staging database" in text
    lines = env.roke("network", cwd=shop).out.splitlines()
    shadcn = [line for line in lines if "ui.shadcn.com" in line]
    assert len(shadcn) == 1 and shadcn[0].endswith("shadcn/ui component registry")
    # The gateway gets the destinations only.
    allowed = env.roke(cwd=shop).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"].split()
    assert "ui.shadcn.com" in allowed and "shadcn/ui" not in " ".join(allowed)
    env.roke("network", "rm", "ui.shadcn.com", cwd=shop)
    assert "ui.shadcn.com" not in env.project_env().read_text()
    assert "staging database" in env.project_env().read_text()


def test_old_single_line_lists_still_work(env):
    shop = env.project()
    env.write_project_env('ROKE_NETWORK_ALLOW="a.example.com b.example.com"\nOTHER=1\n')
    env.roke("network", "add", "c.example.com", "--note", "new one", cwd=shop)
    text = env.project_env().read_text()
    assert "a.example.com\nb.example.com\nc.example.com  # new one" in text
    assert "OTHER=1" in text
    allowed = env.roke(cwd=shop).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"].split()
    assert {"a.example.com", "b.example.com", "c.example.com"} <= set(allowed)


def test_notes_never_become_code(env):
    shop = env.project()
    for note in ["x $(touch /tmp/pwned)", "x `id`", 'say "hi"', "back\\slash"]:
        r = env.roke("network", "add", "evil.example.com", "--note", note, cwd=shop)
        assert r.code != 0 and "a note cannot contain" in r.err
    r = env.roke("service", "add", "postgres", "--note", "x", cwd=shop)
    assert r.code != 0 and "--note only applies to roke network add" in r.err


def test_default_destinations_explain_themselves(env):
    out = env.roke("network", cwd=env.project()).out
    crates = next(line for line in out.splitlines() if line.strip().startswith("crates.io"))
    assert crates.endswith("Rust crates")
    anthropic = next(line for line in out.splitlines() if "api.anthropic.com" in line)
    assert anthropic.endswith("Claude API")


def test_group_comments_are_notes_too(env):
    """A list written by hand: a comment line names the entries below it."""
    shop = env.project()
    env.write_project_env(
        'ROKE_NETWORK_ALLOW="\n# Staging\napi.staging.example.com\ncdn.staging.example.com\n"\n'
    )
    lines = env.roke("network", cwd=shop).out.splitlines()
    for host in ("api.staging.example.com", "cdn.staging.example.com"):
        assert next(line for line in lines if host in line).endswith("Staging")
