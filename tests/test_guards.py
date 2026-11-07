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
        "inside_repo": REPO / "services",
    }[where]
    r = env.roke(cwd=cwd)
    assert r.code != 0
    assert message in r.err


def test_read_only_commands_work_anywhere(env):
    assert env.roke("settings", cwd=env.home).code == 0
    assert env.roke("agent", cwd=env.home).code == 0
    assert env.roke("agent", "use", "codex", "--global", cwd=env.home).code == 0
