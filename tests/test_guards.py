import pytest
from conftest import REPO


@pytest.mark.parametrize(
    "where,message",
    [
        ("home", "your whole $HOME"),
        ("root", "the whole /"),
        ("config_parent", "contains your roke configuration"),
        ("inside_config", "inside your roke configuration"),
        ("inside_repo", "inside the roke repo"),
    ],
)
def test_refuses_dangerous_project_directories(env, where, message):
    cwd = {
        "home": env.home,
        "root": "/",
        "config_parent": env.home / ".config",
        "inside_config": env.config / "projects",
        "inside_repo": REPO / "catalog",
    }[where]
    r = env.roke(cwd=cwd)
    assert r.code != 0
    assert message in r.err


def test_read_only_commands_work_anywhere(env):
    assert env.roke("settings", cwd=env.home).code == 0
    assert env.roke("agent", cwd=env.home).code == 0
    assert env.roke("agent", "use", "codex", "--global", cwd=env.home).code == 0


def test_a_roke_package_in_the_project_is_never_imported(env):
    """The agent can write to the project, and roke usually runs there: a
    roke/ directory in it must not replace roke's own code on the host."""
    shop = env.project()
    marker = env.tmp / "hijacked"
    (shop / "roke").mkdir()
    (shop / "roke" / "__init__.py").write_text(
        f"open({str(marker)!r}, 'w').write('x')\nraise SystemExit('hijacked')\n"
    )
    r = env.roke("settings", cwd=shop, env={"PYTHONPATH": str(shop)})
    assert r.code == 0, r.text
    assert "Project" in r.out
    assert not marker.exists()
