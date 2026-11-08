"""Several agents in the same project at once: ROKE_PARALLEL_AGENTS, and the
protection of the sessions already running."""

import pytest
from helpers import env_value


def allowed(env, cwd, *args):
    return env.roke(*args, cwd=cwd).last("run")["env"]["ROKE_NETWORK_ALLOW_ALL"]


def test_by_default_only_the_agent_s_destinations(env):
    shop = env.project()
    claude = allowed(env, shop).split()
    assert "api.anthropic.com" in claude and "api.openai.com" not in claude
    assert allowed(env, shop) != allowed(env, shop, "--agent", "codex")


def test_parallel_agents_share_the_same_network(env):
    shop = env.project()
    env.write_project_env("ROKE_PARALLEL_AGENTS=claude,codex\n")
    claude = allowed(env, shop)
    assert claude == allowed(env, shop, "--agent", "codex")
    assert "api.anthropic.com" in claude.split() and "api.openai.com" in claude.split()
    # An agent outside the list keeps only its own destinations.
    assert "platform.claude.com" not in allowed(env, shop, "--agent", "opencode").split()
    assert (
        "agents     catalog/agents/claude/allow.txt catalog/agents/codex/allow.txt"
        in env.roke("network", cwd=shop).out
    )


def test_unknown_parallel_agent(env):
    env.write_project_env("ROKE_PARALLEL_AGENTS=claude,nope\n")
    r = env.roke(cwd=env.project())
    assert r.code != 0 and "unknown agent in ROKE_PARALLEL_AGENTS" in r.err


def test_a_session_that_changes_nothing_starts(env):
    r = env.roke(
        cwd=env.project(),
        env={
            "FAKE_SESSIONS": "claude",
            "FAKE_RUNNING_HASHES": "gateway=h1",
            "FAKE_CONFIG_HASHES": "gateway=h1,box=x",
        },
    )
    assert r.code == 0, r.text
    assert r.compose_calls("run")


def test_another_agent_would_cut_off_the_running_session(env):
    r = env.roke(
        "--agent",
        "codex",
        cwd=env.project(),
        env={
            "FAKE_SESSIONS": "claude",
            "FAKE_RUNNING_HASHES": "gateway=h1",
            "FAKE_CONFIG_HASHES": "gateway=h2",
        },
    )
    assert r.code != 0
    assert "already running claude" in r.err
    assert "ROKE_PARALLEL_AGENTS=claude,codex" in r.err
    assert not r.compose_calls("run")


def test_other_changes_would_cut_off_the_running_session(env):
    r = env.roke(
        "-p",
        "3000",
        cwd=env.project(),
        env={
            "FAKE_SESSIONS": "claude",
            "FAKE_RUNNING_HASHES": "gateway=h1,postgres=p1",
            "FAKE_CONFIG_HASHES": "gateway=h2,postgres=p1",
        },
    )
    assert r.code != 0 and "would recreate gateway" in r.err
    assert not r.compose_calls("run")


@pytest.mark.parametrize("parallel,starts", [(True, True), (False, False)])
def test_second_agent_with_real_compose(env, compose, parallel, starts):
    """With real compose hashes: Codex joins a running Claude Code session
    only when both are in ROKE_PARALLEL_AGENTS."""
    shop = env.project()
    if parallel:
        env.write_project_env("ROKE_PARALLEL_AGENTS=claude,codex\n")
    real = {"FAKE_REAL_COMPOSE": compose}
    # The hashes Claude Code's session would leave running.
    r = env.roke(cwd=shop, env={**real, "FAKE_SESSIONS": "x", "FAKE_RUNNING_HASHES": "nothing=0"})
    hashes = dict(
        line.split(None, 1)
        for call in r.calls
        if call["args"] == ["hashes"]
        for line in call["stdout"].splitlines()
    )
    running = f"gateway={hashes['gateway']}"
    r = env.roke(
        "--agent",
        "codex",
        cwd=shop,
        env={**real, "FAKE_SESSIONS": "claude", "FAKE_RUNNING_HASHES": running},
    )
    assert (r.code == 0) is starts, r.text
    if not starts:
        assert "ROKE_PARALLEL_AGENTS=claude,codex" in r.err
    if env.project_env().exists():  # nothing was changed
        assert env_value(env.project_env(), "ROKE_AGENT") is None
