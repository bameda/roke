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


def test_down_all_does_not_treat_query_failure_as_no_projects(env):
    r = env.roke("down", "--all", cwd=env.home, env={"FAKE_DOCKER_FAIL": "ls"})
    assert r.code != 0
    assert "could not list running roke projects" in r.err
    assert "daemon unavailable" in r.err
    assert "no roke project is running" not in r.text
    assert not r.compose_calls("down")


def test_start_is_refused_when_running_containers_cannot_be_checked(env):
    r = env.roke(cwd=env.project(), env={"FAKE_DOCKER_FAIL": "ps"})
    assert r.code != 0
    assert "could not list project containers" in r.err
    assert not r.compose_calls("run")


def test_malformed_container_list_cannot_bypass_session_protection(env):
    r = env.roke(cwd=env.project(), env={"FAKE_BAD_PS": "1"})
    assert r.code != 0
    assert "could not read Docker's container list" in r.err
    assert not r.compose_calls("run")


def test_inspection_failure_does_not_bypass_running_session_protection(env):
    for failure in ({"FAKE_DOCKER_FAIL": "inspect"}, {"FAKE_BAD_INSPECT": "1"}):
        r = env.roke(
            cwd=env.project(),
            env={
                "FAKE_SESSIONS": "claude",
                "FAKE_RUNNING_HASHES": "gateway=h1",
                "FAKE_CONFIG_HASHES": "gateway=h2",
                **failure,
            },
        )
        assert r.code != 0
        assert "container" in r.err
        assert "Traceback" not in r.err
        assert not r.compose_calls("run")


def test_settings_marks_unknown_docker_state_without_losing_settings(env):
    r = env.roke("settings", cwd=env.project(), env={"FAKE_DOCKER_FAIL": "ps"})
    assert r.code == 0, r.text
    assert "Docker state unavailable" in r.out
    assert "Agent     claude" in r.out
    assert "not running" not in r.out
