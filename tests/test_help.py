import sys

import pytest
from conftest import REPO

sys.path.insert(0, str(REPO))
from roke.commands import HANDLERS  # noqa: E402
from roke.ui.help import COMMANDS, USAGE, help_for  # noqa: E402


@pytest.mark.parametrize("args", [["--help"], ["-h"], ["help"]])
def test_whole_help(env, args):
    r = env.roke(*args)
    assert r.code == 0
    for part in (
        "Usage: roke",
        "Sessions",
        "The project\n",
        "Projects and images, on this machine",
        "Agents",
        "Services",
        "Network",
        "roke itself",
        "roke version",
        "also --version",
        "Options for run",
    ):
        assert part in r.out


@pytest.mark.parametrize(
    "args,expected,absent",
    [
        (["help", "network"], "roke network add", "roke service add"),
        (["network", "--help"], "roke network add", "roke service add"),
        (["agent", "--help"], "roke agent use", "roke network add"),
        (["service", "-h"], "roke service add", "roke agent use"),
        (["shell", "--help"], "roke shell", "roke agent use"),
        (["help", "down"], "roke down", "roke service add"),
        (["help", "doctor"], "roke doctor", "roke settings edit"),
        (["help", "settings"], "roke settings edit", "roke doctor"),
        (["help", "project"], "roke project rename", "roke image"),
        (["image", "--help"], "roke image prune", "roke project"),
        (["mcp", "--help"], "roke mcp reset", "roke network add"),
        (["help", "version"], "roke version", "roke service add"),
        (["update", "--help"], "roke update [--stable|--main]", "roke service add"),
        (["version", "--help"], "roke version", "roke service add"),
    ],
)
def test_help_for_a_command(env, args, expected, absent):
    r = env.roke(*args)
    assert r.code == 0
    assert expected in r.out and absent not in r.out


def test_help_for_run_like_commands_includes_options(env):
    assert "-s, --services" in env.roke("shell", "--help").out


@pytest.mark.parametrize(
    "args,message",
    [
        (["foo"], "unknown command: foo"),
        (["agent", "bar"], "unknown command: roke agent bar"),
        (["--down"], "unknown option"),
        (["down", "--whatever"], "unknown option"),
        (["help", "foo"], "no help for 'foo'"),
        (["exec"], "roke exec needs a command"),
    ],
)
def test_errors(env, args, message):
    r = env.roke(*args)
    assert r.code != 0
    assert message in r.err


def test_a_commands_help_has_only_its_own_options(env):
    assert "--git-rw" in env.roke("help", "exec").out
    assert "--git-rw" not in env.roke("help", "doctor").out
    assert "--id ID" in env.roke("help", "doctor").out  # every project command takes it
    assert "--id ID" not in env.roke("help", "image").out
    assert "--id ID" not in env.roke("help", "update").out
    assert "-p, --port" in env.roke("help", "urls").out  # -s and -p also apply to urls


def test_every_command_has_help():
    for command in COMMANDS:
        assert help_for(command).startswith("  roke")


def test_every_command_is_in_the_help():
    """The table of handlers and the help must not diverge."""
    for command, sub in HANDLERS:
        if command in ("run",) and not sub:
            assert "roke [run]" in USAGE
        elif sub in ("", "list"):
            assert f"  roke {command}" in USAGE, command
        else:
            assert f"  roke {command} {sub}" in USAGE, (command, sub)
    assert set(COMMANDS) >= {command for command, _ in HANDLERS}
