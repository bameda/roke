"""Failures in settings and Compose should be actionable CLI errors."""


def test_bad_settings_file_has_a_path_without_a_traceback(env):
    shop = env.project()
    env.write_project_env('ROKE_AGENT="unclosed\n')
    r = env.roke("settings", cwd=shop)
    assert r.code != 0
    assert str(env.project_env()) in r.err
    assert "could not load settings" in r.err
    assert "Traceback" not in r.err


def test_bad_compose_configuration_is_reported(env):
    r = env.roke("urls", cwd=env.project(), env={"FAKE_COMPOSE_FAIL": "config"})
    assert r.code != 0
    assert "invalid compose file" in r.err
    assert "Traceback" not in r.err


def test_failed_compose_ps_is_not_reported_as_stopped(env):
    r = env.roke("network", "blocked", cwd=env.project(), env={"FAKE_COMPOSE_FAIL": "ps"})
    assert r.code != 0
    assert "could not check whether gateway is running" in r.err
    assert "daemon unavailable" in r.err
    assert "not running" not in r.err
