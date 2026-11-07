from helpers import compose_files, env_value


def test_add_and_rm(env):
    shop = env.project()
    assert env.roke("service", "add", "postgres", "mailpit", cwd=shop).code == 0
    assert env_value(env.project_env(), "ROKE_SERVICES") == "postgres,mailpit"
    assert "already in" in env.roke("service", "add", "postgres", cwd=shop).text
    assert env.roke("service", "rm", "mailpit", cwd=shop).code == 0
    assert env_value(env.project_env(), "ROKE_SERVICES") == "postgres"
    env.roke("service", "rm", "postgres", cwd=shop)
    assert env_value(env.project_env(), "ROKE_SERVICES") is None


def test_add_validates_every_name_before_changing_anything(env):
    shop = env.project()
    env.roke("service", "add", "postgres", cwd=shop)
    r = env.roke("service", "add", "redis", "nonexistent", cwd=shop)
    assert r.code != 0 and "unknown service" in r.err
    assert env_value(env.project_env(), "ROKE_SERVICES") == "postgres"


def test_add_starts_from_the_global_list(env):
    shop = env.project()
    env.append(env.config / "roke.env", "ROKE_SERVICES=redis\n")
    env.roke("service", "add", "postgres", cwd=shop)
    assert env_value(env.project_env(), "ROKE_SERVICES") == "redis,postgres"


def test_list_marks_the_project_services(env):
    shop = env.project()
    env.roke("service", "add", "postgres", cwd=shop)
    lines = env.roke("service", cwd=shop).out.splitlines()
    assert any(line.startswith("* postgres") for line in lines)
    assert any(line.startswith("  redis") for line in lines)


def test_run_loads_the_services(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres,mailpit\n")
    files = compose_files(env.roke(cwd=shop).last("run"))
    assert files[0].endswith("/compose.yaml")
    assert any(f.endswith("services/postgres/compose.yaml") for f in files)
    assert any(f.endswith("services/mailpit/compose.yaml") for f in files)
    assert not any("services/redis/" in f for f in files)


def test_services_option_overrides_the_project(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\n")
    r = env.roke("-s", "redis", cwd=shop)
    files = compose_files(r.last("run"))
    assert any("services/redis/" in f for f in files)
    assert not any("services/postgres/" in f for f in files)
    assert r.last("run")["env"]["ROKE_SERVICES"] == "redis"


def test_unknown_service_at_run(env):
    r = env.roke("-s", "nope", cwd=env.project())
    assert r.code != 0 and "unknown service" in r.err


def test_own_services_precedence(env):
    shop = env.project()
    for base in (env.config / "services", env.config / "projects" / "shop" / "services"):
        (base / "mailpit").mkdir(parents=True)
        (base / "mailpit" / "compose.yaml").write_text("# Mine\nservices: {}\n")
    (env.config / "services" / "keycloak").mkdir()
    (env.config / "services" / "keycloak" / "compose.yaml").write_text("# Keycloak\nservices: {}\n")
    out = env.roke("service", cwd=shop).out
    assert "[project]" in [line for line in out.splitlines() if " mailpit " in line][0]
    assert "[yours]" in [line for line in out.splitlines() if " keycloak " in line][0]
    files = compose_files(env.roke("-s", "mailpit", cwd=shop).last("run"))
    assert any("projects/shop/services/mailpit/" in f for f in files)
