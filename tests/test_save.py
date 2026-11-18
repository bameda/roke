"""roke --save: the options of a session, kept as the project's settings."""

import pytest
from helpers import env_value


def saved(env, name="shop"):
    return env.project_env(name).read_text() if env.project_env(name).exists() else ""


def test_save_creates_a_project_with_every_option_given(env):
    shop = env.project()
    r = env.roke(
        "-a", "codex", "-s", "postgres,redis", "-p", "3000,5173", "--network", "open",
        "--git-rw", "--serena", "--save", cwd=shop,
    )  # fmt: skip
    assert r.code == 0, r.text
    assert "kept for shop" in r.err
    for line in (
        "ROKE_AGENT=codex",
        "ROKE_SERVICES=postgres,redis",
        "ROKE_PORTS=3000,5173",
        "ROKE_NETWORK=open",
        "ROKE_GIT_RW=1",
        "ROKE_SERENA=1",
    ):
        assert line in saved(env), line
    # The next sessions have it all, with no options.
    out = env.roke("settings", cwd=shop).out
    assert "Agent     codex (this project)" in out
    assert "Services  postgres" in out and "redis" in out
    assert "Box ports 3000 5173" in out
    assert "Network   open" in out and ".git      read-write" in out and "Serena    on" in out
    again = env.roke(cwd=shop).last("run")
    assert again["env"]["ROKE_AGENT"] == "codex"
    assert again["env"]["ROKE_SERVICES"] == "postgres,redis"


def test_save_keeps_only_what_was_given(env):
    shop = env.project()
    env.write_project_env("ROKE_AGENT=codex\nROKE_PORTS=1234\n")
    assert env.roke("-s", "redis", "--save", cwd=shop).code == 0
    text = saved(env)
    assert "ROKE_SERVICES=redis" in text
    assert "ROKE_AGENT=codex" in text and "ROKE_PORTS=1234" in text  # untouched


def test_save_replaces_the_services_like_the_option_does(env):
    shop = env.project()
    env.roke("service", "add", "postgres", "redis", cwd=shop)
    env.roke("-s", "mailpit", "--save", cwd=shop)
    assert env_value(env.project_env(), "ROKE_SERVICES") == "mailpit"
    env.roke("-s", "", "--save", cwd=shop)
    assert env_value(env.project_env(), "ROKE_SERVICES") in ("", None)


def test_save_serena_off_and_a_space_separated_list(env):
    shop = env.project()
    assert env.roke("--no-serena", "-s", "postgres redis", "--save", cwd=shop).code == 0
    assert "ROKE_SERENA=0" in saved(env) and "ROKE_SERVICES=postgres,redis" in saved(env)


def test_save_with_continue(env):
    shop = env.project()
    r = env.roke("continue", "-s", "redis", "--save", cwd=shop)
    assert r.code == 0 and "ROKE_SERVICES=redis" in saved(env)


@pytest.mark.parametrize(
    "args",
    [("-s", "nope"), ("-p", "99999"), ("--network", "sideways"), ("-a", "nope")],
)
def test_nothing_is_kept_when_the_session_cannot_start(env, args):
    shop = env.project()
    r = env.roke(*args, "--save", cwd=shop)
    assert r.code != 0 and not r.compose_calls("run")
    assert "ROKE_" not in saved(env).replace("ROKE_SERVICES=\n", "")


def test_nothing_is_kept_when_another_session_would_be_cut_off(env):
    shop = env.project()
    r = env.roke(
        "-a", "codex", "--save", cwd=shop,
        env={"FAKE_SESSIONS": "claude", "FAKE_RUNNING_HASHES": "gateway=h1",
             "FAKE_CONFIG_HASHES": "gateway=h2"},
    )  # fmt: skip
    assert r.code != 0 and "ROKE_AGENT" not in saved(env)


def test_a_new_project_is_told_how_to_keep_its_options(env):
    shop = env.project()
    r = env.roke("-s", "postgres", "-p", "5173", cwd=shop)
    assert "this project has no settings of its own yet: --save keeps -s, -p for it" in r.err
    # It is said once, when the project is new, and never with --save.
    assert "no settings of its own yet" not in env.roke("-s", "postgres", cwd=shop).err
    other = env.project("other")
    assert "no settings of its own yet" not in env.roke("-s", "redis", "--save", cwd=other).err


def test_no_hint_without_options_or_outside_sessions(env):
    shop = env.project()
    assert "no settings of its own yet" not in env.roke(cwd=shop).err
    fresh = env.project("fresh")
    assert "no settings of its own yet" not in env.roke("shell", "-s", "redis", cwd=fresh).err
