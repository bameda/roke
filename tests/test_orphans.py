"""Containers of services that are no longer the project's: removed when no session is open."""

import pytest

OPEN_SESSION = {
    "FAKE_SESSIONS": "claude",
    "FAKE_RUNNING_HASHES": "gateway=h1",
    "FAKE_CONFIG_HASHES": "gateway=h1",
}


def run_args(result):
    return result.last("run")["args"]


@pytest.mark.parametrize("command", [(), ("continue",), ("shell",), ("exec", "true")])
def test_leftover_containers_are_removed_when_no_session_is_open(env, command):
    args = run_args(env.roke(*command, cwd=env.project()))
    assert "--remove-orphans" in args and args.index("--remove-orphans") < args.index("box")


def test_nothing_is_removed_while_another_session_is_open(env):
    """The containers may be that session's: -s can differ from one to the other."""
    r = env.roke(cwd=env.project(), env=OPEN_SESSION)
    assert r.code == 0, r.text
    assert "--remove-orphans" not in run_args(r)


def test_a_session_that_cannot_start_removes_nothing(env):
    r = env.roke(
        "-a",
        "codex",
        cwd=env.project(),
        env={**OPEN_SESSION, "FAKE_CONFIG_HASHES": "gateway=h2"},
    )
    assert r.code != 0 and not r.compose_calls("run")


def test_down_still_removes_them(env):
    r = env.roke("down", cwd=env.project())
    assert "--remove-orphans" in next(c["args"] for c in r.compose_calls("down"))
