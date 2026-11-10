import pytest


@pytest.mark.parametrize("args", [["--help"], ["-h"], ["help"]])
def test_whole_help(env, args):
    r = env.roke(*args)
    assert r.code == 0
    for part in (
        "Usage: roke",
        "The project's box",
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
