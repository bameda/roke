"""When Docker has no subnet left for a project's networks, roke says what to do."""

import subprocess

import pytest
from conftest import ROKE

EXHAUSTED = {"FAKE_RUN_EXIT": "1", "FAKE_POOLS_EXHAUSTED": "1"}


def network_calls(result):
    return [c["args"] for c in result.calls if c["args"][:1] == ["network"]]


def test_a_session_that_cannot_start_for_lack_of_subnets_says_why(env):
    r = env.roke(cwd=env.project(), env=EXHAUSTED)
    assert r.code == 1
    assert "Docker has no subnet left for this project's networks" in r.err
    for fix in ("roke down --all", "docker network prune", "docs/troubleshooting.md"):
        assert fix in r.err
    create = network_calls(r)
    assert len(create) == 1 and create[0][:2] == ["network", "create"]


def test_a_failure_for_another_reason_says_nothing_about_subnets(env):
    r = env.roke(cwd=env.project(), env={"FAKE_RUN_EXIT": "1"})
    assert r.code == 1 and "no subnet left" not in r.err
    # The probe network was removed at once.
    create, remove = network_calls(r)
    assert create[2].startswith("roke-probe-") and remove == ["network", "rm", create[2]]


def test_nothing_is_probed_when_the_session_ends_normally_or_by_the_agent(env):
    shop = env.project()
    assert not network_calls(env.roke(cwd=shop))
    for code in ("2", "130"):  # the agent's own exit codes
        r = env.roke(cwd=shop, env={"FAKE_RUN_EXIT": code})
        assert r.code == int(code) and not network_calls(r)


@pytest.mark.parametrize("command", [("shell",), ("exec", "true"), ("continue",)])
def test_every_session_command_explains_it(env, command):
    r = env.roke(*command, cwd=env.project(), env=EXHAUSTED)
    assert r.code == 1 and "no subnet left" in r.err


def test_the_editor_session_explains_it_too(env):
    shop = env.project()
    environ = env.environment(EXHAUSTED)
    proc = subprocess.run(
        [str(ROKE), "acp"],
        cwd=shop,
        env=environ,
        input="",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 1 and "no subnet left" in proc.stderr
    assert proc.stdout == ""  # standard output stays the protocol's


@pytest.mark.parametrize(
    "error",
    [
        "permission denied while trying to connect to the Docker daemon",
        "network name already in use",
    ],
)
def test_another_reason_for_not_creating_a_network_is_not_blamed_on_subnets(env, error):
    r = env.roke(cwd=env.project(), env={"FAKE_RUN_EXIT": "1", "FAKE_NETWORK_ERROR": error})
    assert r.code == 1 and "no subnet left" not in r.err
