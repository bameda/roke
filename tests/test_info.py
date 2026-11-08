"""roke settings (summary and edit), and the show commands of the catalogs."""

import stat

import pytest

EDITOR = """#!/bin/sh
echo "$1" >> "$EDITOR_LOG"
if [ -n "$EDITOR_APPEND" ]; then printf '%s\\n' "$EDITOR_APPEND" >> "$1"; fi
"""


@pytest.fixture
def editor(env):
    """A fake editor that logs the file it opens and may append to it."""
    script = env.tmp / "editor"
    script.write_text(EDITOR)
    script.chmod(0o755)
    log = env.tmp / "editor.log"
    env.extra_env.update({"EDITOR": str(script), "EDITOR_LOG": str(log)})

    def opened():
        return log.read_text().splitlines()[-1] if log.exists() else None

    return opened


def test_settings_summary(env):
    shop = env.project()
    env.append(env.config / "secrets.env", "GITHUB_PAT=ghp_secret_value\n")
    env.write_project_env("ROKE_SERVICES=postgres\nPOSTGRES_VERSION=17\nROKE_MCPS=github\n")
    (env.config / "projects" / "shop" / "secrets.env").write_text("DB_TOKEN=t0ken\n")
    env.roke("network", "add", "db.example.com", cwd=shop)
    out = env.roke("settings", cwd=shop).out
    assert "Services  postgres 17" in out
    assert "MCPs      github" in out
    assert "Secrets   GITHUB_PAT (global), DB_TOKEN (project)" in out
    assert "ghp_secret_value" not in out and "t0ken" not in out
    assert "1 of them the project's (roke network)" in out
    assert "  base " not in out  # the layers are in roke network


@pytest.mark.parametrize(
    "args,where",
    [
        ([], "projects/shop/project.env"),
        (["--global"], "roke.env"),
        (["secrets"], "projects/shop/secrets.env"),
        (["secrets", "--global"], "secrets.env"),
        (["compose"], "projects/shop/compose.yaml"),
        (["instructions"], "projects/shop/AGENTS.md"),
        (["instructions", "--global"], "AGENTS.md"),
    ],
)
def test_settings_edit_opens_the_right_file(env, editor, args, where):
    r = env.roke("settings", "edit", *args, cwd=env.project())
    assert r.code == 0, r.text
    assert editor() == str(env.config / where)


def test_settings_edit_creates_files_from_templates(env, editor):
    shop = env.project()
    env.roke("settings", "edit", cwd=shop)
    assert "# ROKE_SERVICES=" in env.project_env().read_text()
    env.roke("settings", "edit", "secrets", cwd=shop)
    secrets = env.config / "projects" / "shop" / "secrets.env"
    assert stat.S_IMODE(secrets.stat().st_mode) == 0o600
    env.roke("settings", "edit", "compose", cwd=shop)
    assert "services: {}" in (env.config / "projects" / "shop" / "compose.yaml").read_text()


def test_settings_edit_tools_is_the_project_s_mise_toml(env, editor):
    shop = env.project()
    env.roke("settings", "edit", "tools", cwd=shop)
    assert editor() == str(shop / "mise.toml")
    assert "[tools]" in (shop / "mise.toml").read_text()
    (shop / "mise.toml").unlink()
    (shop / ".mise.toml").write_text("[tools]\n")
    env.roke("settings", "edit", "tools", cwd=shop)
    assert editor() == str(shop / ".mise.toml")


def test_settings_edit_errors(env, editor):
    shop = env.project()
    for args, message in [
        (["tools", "--global"], "tools has no --global"),
        (["compose", "--global"], "compose has no --global"),
        (["nope"], "usage: roke settings edit"),
    ]:
        r = env.roke("settings", "edit", *args, cwd=shop)
        assert r.code != 0 and message in r.err


def test_settings_edit_warns_about_syntax_errors(env, editor):
    r = env.roke("settings", "edit", cwd=env.project(), env={"EDITOR_APPEND": 'X="unclosed'})
    assert r.code != 0
    assert "has a syntax error" in r.err


def test_roke_editor_wins(env, editor):
    other = env.tmp / "other-editor"
    other.write_text('#!/bin/sh\necho "other $1" >> "$EDITOR_LOG"\n')
    other.chmod(0o755)
    env.append(env.config / "roke.env", f"ROKE_EDITOR={other}\n")
    env.roke("settings", "edit", cwd=env.project())
    assert editor().startswith("other ")


def test_mcp_show_never_shows_secret_values(env):
    shop = env.project()
    r = env.roke("mcp", "show", "github", cwd=shop)
    assert "needs GITHUB_PAT: NOT SET" in r.out and "not used (roke mcp add github)" in r.out
    assert "# GitHub (`github`)" in r.out
    env.append(env.config / "secrets.env", "GITHUB_PAT=ghp_secret_value\n")
    env.roke("mcp", "add", "github", "--global", cwd=shop)
    r = env.roke("mcp", "show", "github", cwd=shop)
    assert "needs GITHUB_PAT: set" in r.out and "ghp_secret_value" not in r.out
    assert "in every project (roke mcp rm github --global)" in r.out


def test_agent_show(env):
    r = env.roke("agent", "show", "codex", cwd=env.project())
    assert "not used (roke agent use codex)" in r.out
    assert "allows: api.openai.com" in r.out
    assert "# Codex CLI (`codex`)" in r.out
    assert (
        "used (default agent, roke.env)"
        in env.roke("agent", "show", "claude", cwd=env.project()).out
    )


@pytest.mark.parametrize("group", ["service", "mcp", "agent"])
def test_show_unknown(env, group):
    r = env.roke(group, "show", "nope", cwd=env.project())
    assert r.code != 0 and "unknown" in r.err


@pytest.mark.parametrize("group", ["service", "mcp", "agent"])
def test_lists_point_to_show(env, group):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\n")  # adds the versions table
    out = env.roke(group, cwd=shop).out
    assert out.rstrip().endswith(f"More about each one: roke {group} show NAME")


@pytest.mark.parametrize(
    "env_vars,coloured",
    [
        ({}, False),  # not a terminal
        ({"ROKE_COLOR": "always"}, True),
        ({"ROKE_COLOR": "never"}, False),
        ({"ROKE_COLOR": "always", "NO_COLOR": "1"}, True),  # an explicit setting wins
    ],
)
def test_readmes_in_colour(env, env_vars, coloured):
    r = env.roke("agent", "show", "codex", cwd=env.project(), env=env_vars)
    assert r.code == 0, r.text
    assert ("\033[" in r.out) is coloured
    assert "Codex CLI" in r.out


def test_roke_color_from_settings_and_invalid(env):
    shop = env.project()
    env.append(env.config / "roke.env", "ROKE_COLOR=always\n")
    assert "\033[" in env.roke("agent", "show", "codex", cwd=shop).out
    env.write_project_env("ROKE_COLOR=sometimes\n")
    r = env.roke("agent", "show", "codex", cwd=shop)
    assert r.code != 0 and "ROKE_COLOR must be auto, always or never" in r.err
