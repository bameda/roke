"""Project diagnostics without starting containers or writing settings."""


def test_healthy_project(env):
    shop = env.project()
    before = sorted(str(path) for path in env.config.rglob("*"))
    r = env.roke("doctor", cwd=shop)
    assert r.code == 0, r.text
    assert "Project configuration: OK" in r.out
    assert "Compose configuration: OK" in r.out
    assert "Agent     claude" not in r.out
    assert "Services  " not in r.out
    assert "Network   " not in r.out
    assert not r.compose_calls("run")
    assert not env.project_env().exists()
    assert sorted(str(path) for path in env.config.rglob("*")) == before


def test_missing_mcp_secret_and_image(env):
    shop = env.project()
    env.write_project_env("ROKE_MCPS=github\n")
    r = env.roke("doctor", cwd=shop, env={"FAKE_NO_IMAGE": "1"})
    assert r.code != 0
    assert "MCP github: FAIL (set GITHUB_PAT in secrets.env)" in r.out
    assert "Box image: FAIL (run roke build)" in r.out
    assert "Compose configuration: OK" in r.out
    assert "ghp_" not in r.text


def test_invalid_project_is_reported(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=unknown\n")
    r = env.roke("doctor", cwd=shop)
    assert r.code != 0 and "unknown service" in r.err
    assert not r.compose_calls("run")


def test_invalid_compose_is_reported_as_a_failed_check(env):
    r = env.roke("doctor", cwd=env.project(), env={"FAKE_COMPOSE_FAIL": "config"})
    assert r.code != 0
    assert "Compose configuration: FAIL (invalid compose file)" in r.out


def test_doctor_rejects_options(env):
    r = env.roke("doctor", "--no-cache", cwd=env.project())
    assert r.code != 0 and "unknown option" in r.err
