"""Project log arguments go to Docker Compose unchanged."""


def test_logs_default_and_selected_service(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres,redis\n")
    r = env.roke("logs", cwd=shop)
    assert r.code == 0, r.text
    assert r.last("logs")["args"][-1:] == ["logs"]
    assert not r.compose_calls("run")
    r = env.roke("logs", "postgres", "-f", cwd=shop)
    assert r.code == 0, r.text
    assert r.last("logs")["args"][-3:] == ["logs", "postgres", "-f"]


def test_logs_forwards_compose_options_and_values(env):
    shop = env.project()
    options = [
        "--tail",
        "25",
        "--since",
        "2h",
        "--until",
        "2026-11-09T12:00:00Z",
        "--timestamps",
        "--no-log-prefix",
        "gateway",
        "postgres",
    ]
    r = env.roke("logs", *options, cwd=shop)
    assert r.code == 0, r.text
    assert r.last("logs")["args"][-len(options) - 1 :] == ["logs", *options]


def test_logs_help(env):
    shop = env.project()
    assert "Compose logs options" in env.roke("help", "logs", cwd=shop).out
    assert "Compose logs options" in env.roke("logs", "--help", cwd=shop).out
    r = env.roke("logs", "--bad", cwd=shop)
    assert r.last("logs")["args"][-2:] == ["logs", "--bad"]


def test_unknown_service_lists_available_logs(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres,redis\n")
    r = env.roke(
        "logs",
        "missing",
        cwd=shop,
        env={
            "FAKE_LOGS_ERROR": "service",
            "FAKE_COMPOSE_SERVICES": "box\ngateway\npostgres\nredis\ncustom",
        },
    )
    assert r.code != 0
    assert "no such service: missing" in r.err
    assert "Available logs: gateway, postgres, redis, custom" in r.err


def test_invalid_option_does_not_list_services(env):
    r = env.roke("logs", "--bad", cwd=env.project(), env={"FAKE_LOGS_ERROR": "flag"})
    assert r.code != 0
    assert "unknown flag: --bad" in r.err
    assert "Available logs:" not in r.err
