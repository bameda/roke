import pytest
from helpers import env_value


def test_lists_agents_and_the_one_in_use(env):
    shop = env.project()
    r = env.roke("agent", cwd=shop)
    assert r.code == 0
    for agent in ("claude", "codex", "opencode"):
        assert agent in r.out
    assert "claude" in r.out.split("<- used here")[0].splitlines()[-1]
    assert "(default agent, roke.env)" in r.out


def test_use_in_the_project(env):
    shop = env.project()
    r = env.roke("agent", "use", "opencode", cwd=shop)
    assert r.code == 0, r.text
    assert env_value(env.project_env(), "ROKE_AGENT") == "opencode"
    assert "(this project)" in env.roke("agent", cwd=shop).out


def test_use_global_replaces_the_default(env):
    shop = env.project()
    assert env.roke("agent", "use", "codex", "--global", cwd=shop).code == 0
    roke_env = (env.config / "roke.env").read_text()
    assert roke_env.count("\nROKE_AGENT=") + roke_env.startswith("ROKE_AGENT=") == 1
    assert env_value(env.config / "roke.env", "ROKE_AGENT") == "codex"


def test_use_global_warns_when_the_project_has_its_own(env):
    shop = env.project()
    env.roke("agent", "use", "opencode", cwd=shop)
    r = env.roke("agent", "use", "codex", "--global", cwd=shop)
    assert "this project has its own agent" in r.text


def test_reset(env):
    shop = env.project()
    env.roke("agent", "use", "opencode", cwd=shop)
    assert env.roke("agent", "reset", cwd=shop).code == 0
    assert env_value(env.project_env(), "ROKE_AGENT") is None


def test_unknown_agent(env):
    r = env.roke("agent", "use", "nope", cwd=env.project())
    assert r.code != 0 and "unknown agent" in r.err


def test_run_needs_an_agent_when_several_are_installed(bare_env):
    bare_env.roke("init")
    r = bare_env.roke(cwd=bare_env.project())
    assert r.code != 0 and "choose a coding agent" in r.err


def test_run_uses_the_only_installed_agent(bare_env):
    bare_env.roke("init")
    bare_env.append(bare_env.config / "roke.env", 'ROKE_AGENTS="codex"\n')
    r = bare_env.roke(cwd=bare_env.project())
    assert r.code == 0, r.text
    assert r.last("run")["env"]["ROKE_AGENT"] == "codex"


def test_agent_option_overrides_everything(env):
    shop = env.project()
    env.roke("agent", "use", "opencode", cwd=shop)
    r = env.roke("--agent", "codex", cwd=shop)
    assert r.last("run")["env"]["ROKE_AGENT"] == "codex"


def test_project_agent_overrides_the_default(env):
    shop = env.project()
    env.roke("agent", "use", "opencode", cwd=shop)
    assert env.roke(cwd=shop).last("run")["env"]["ROKE_AGENT"] == "opencode"


def test_agent_not_in_the_image(env):
    shop = env.project()
    env.append(env.config / "roke.env", 'ROKE_AGENTS="claude"\n')
    assert "not in ROKE_AGENTS" in env.roke("agent", "use", "codex", cwd=shop).text
    r = env.roke("--agent", "codex", cwd=shop)
    assert r.code != 0 and "not in ROKE_AGENTS" in r.err


def agent_of(result):
    return result.last("run")["env"]["ROKE_AGENT"]


def test_agent_option_says_it_is_for_this_session_only(env):
    shop = env.project()  # the default agent is claude
    for args in (("-a", "codex"), ("continue", "-a", "codex")):
        r = env.roke(*args, cwd=shop)
        assert agent_of(r) == "codex"
        assert "codex for this session only; the project uses claude" in r.err
        assert "roke agent use codex, or --save, keeps it" in r.err
    assert not env.project_env().exists()  # nothing was kept
    assert agent_of(env.roke(cwd=shop)) == "claude"


def test_no_notice_when_the_option_is_the_projects_agent(env):
    r = env.roke("-a", "claude", cwd=env.project())
    assert "this session only" not in r.err


def test_the_notice_says_when_no_agent_is_set(env):
    shop = env.project()
    (env.config / "roke.env").write_text("")
    r = env.roke("-a", "codex", cwd=shop)
    assert r.code == 0
    assert "codex for this session only; no agent is set for the project" in r.err


@pytest.mark.parametrize("command", ["shell", "exec"])
def test_no_notice_for_a_login_or_a_command(env, command):
    """roke exec -a codex codex login is not a session to keep."""
    extra = ["codex", "login"] if command == "exec" else []
    r = env.roke(command, "-a", "codex", *extra, cwd=env.project())
    assert r.code == 0 and "this session only" not in r.err


@pytest.mark.parametrize("command", [(), ("continue",)])
def test_save_keeps_the_agent_for_the_project(env, command):
    shop, other = env.project(), env.project("other")
    r = env.roke(*command, "-a", "codex", "--save", cwd=shop)
    assert r.code == 0, r.text
    assert agent_of(r) == "codex"
    assert "agent for shop: codex" in r.err and "this session only" not in r.err
    assert env_value(env.project_env(), "ROKE_AGENT") == "codex"
    # The project keeps it; others and the default do not change.
    assert agent_of(env.roke(cwd=shop)) == "codex"
    assert agent_of(env.roke("continue", cwd=shop)) == "codex"
    assert agent_of(env.roke(cwd=other)) == "claude"
    assert "ROKE_AGENT=claude" in (env.config / "roke.env").read_text()


def test_save_needs_an_agent(env):
    r = env.roke("--save", cwd=env.project())
    assert r.code != 0 and "--save keeps the agent chosen with -a" in r.err
    assert not r.compose_calls("run")


# (roke exec takes what follows its options as the command to run, so it is not here.)
@pytest.mark.parametrize("command", ["shell", "acp", "urls"])
def test_save_is_for_sessions_only(env, command):
    r = env.roke(command, "-a", "codex", "--save", cwd=env.project())
    assert r.code != 0 and "unknown option" in r.err and "--save" in r.err


def test_save_keeps_nothing_when_the_agent_cannot_run(env):
    shop = env.project()
    r = env.roke("-a", "nope", "--save", cwd=shop)
    assert r.code != 0 and "unknown agent: 'nope'" in r.err
    env.append(env.config / "roke.env", 'ROKE_AGENTS="claude"\n')
    r = env.roke("-a", "codex", "--save", cwd=shop)
    assert r.code != 0 and "not in ROKE_AGENTS" in r.err
    assert not env.project_env().exists() or env_value(env.project_env(), "ROKE_AGENT") is None
