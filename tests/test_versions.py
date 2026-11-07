"""Service versions are pinned in each project, so updating roke never
changes them; roke service upgrade moves them on explicitly."""

from helpers import catalog_default, env_value

OWN_SERVICE = """# Thing
services:
  thing:
    image: example/thing:${THING_VERSION:-%s}
%s"""


def own_service(env, default, keeps_data=False):
    """A service of yours whose default version can be changed, as an
    update of roke would."""
    path = env.config / "services" / "thing" / "compose.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(OWN_SERVICE % (default, "volumes:\n  thing-data:\n" if keeps_data else ""))


def test_add_pins_the_version(env):
    shop = env.project()
    r = env.roke("service", "add", "postgres", cwd=shop)
    default = catalog_default("postgres", "POSTGRES_VERSION")
    assert f"pinned for shop: POSTGRES_VERSION={default}" in r.err
    assert env_value(env.project_env(), "POSTGRES_VERSION") == default


def test_existing_versions_are_respected(env):
    shop = env.project()
    env.write_project_env("POSTGRES_VERSION=17\n")
    env.roke("service", "add", "postgres", cwd=shop)
    assert env_value(env.project_env(), "POSTGRES_VERSION") == "17"


def test_global_version_is_the_one_pinned(env):
    shop = env.project()
    env.append(env.config / "roke.env", "POSTGRES_VERSION=16\n")
    env.roke("service", "add", "postgres", cwd=shop)
    assert env_value(env.project_env(), "POSTGRES_VERSION") == "16"


def test_run_pins_the_services_it_starts(env):
    shop = env.project()
    r = env.roke("-s", "redis,mailpit", cwd=shop)
    assert r.code == 0, r.text
    assert env_value(env.project_env(), "REDIS_VERSION") == catalog_default(
        "redis", "REDIS_VERSION"
    )
    assert env_value(env.project_env(), "MAILPIT_VERSION") == catalog_default(
        "mailpit", "MAILPIT_VERSION"
    )
    assert "pinned" not in env.roke("-s", "redis", cwd=shop).err  # already pinned


def test_pinned_version_survives_an_update_of_the_default(env):
    shop = env.project()
    own_service(env, "1.0")
    env.roke("service", "add", "thing", cwd=shop)
    own_service(env, "2.0")  # roke is updated
    r = env.roke(cwd=shop)
    assert r.last("run")["env"]["THING_VERSION"] == "1.0"
    other = env.project("other")
    env.roke("service", "add", "thing", cwd=other)
    assert env_value(env.project_env("other"), "THING_VERSION") == "2.0"


def test_list_shows_available_versions(env):
    shop = env.project()
    own_service(env, "1.0")
    env.roke("service", "add", "thing", "postgres", cwd=shop)
    own_service(env, "1.1")
    out = env.roke("service", cwd=shop).out
    assert "Versions pinned in this project" in out
    assert "THING_VERSION=1.0" in out and "1.1 available" in out
    postgres = catalog_default("postgres", "POSTGRES_VERSION")
    assert f"POSTGRES_VERSION={postgres}" in out and "up to date" in out


def test_upgrade_one_or_all(env):
    shop = env.project()
    own_service(env, "1.0")
    env.roke("service", "add", "thing", "postgres", cwd=shop)
    own_service(env, "1.1")
    r = env.roke("service", "upgrade", "thing", cwd=shop)
    assert r.code == 0 and "THING_VERSION 1.0 → 1.1" in r.err
    assert env_value(env.project_env(), "THING_VERSION") == "1.1"
    own_service(env, "1.2")
    r = env.roke("service", "upgrade", cwd=shop)
    assert env_value(env.project_env(), "THING_VERSION") == "1.2"
    assert "applies from the next start" in r.err
    assert "is up to date" in env.roke("service", "upgrade", cwd=shop).err


def test_major_versions_of_services_with_data_need_major(env):
    shop = env.project()
    own_service(env, "1.0", keeps_data=True)
    env.roke("service", "add", "thing", cwd=shop)
    own_service(env, "2.0", keeps_data=True)
    r = env.roke("service", "upgrade", cwd=shop)
    assert "is a major version and thing keeps data" in r.err
    assert env_value(env.project_env(), "THING_VERSION") == "1.0"
    r = env.roke("service", "upgrade", "thing", "--major", cwd=shop)
    assert env_value(env.project_env(), "THING_VERSION") == "2.0"


def test_major_versions_without_data_are_upgraded(env):
    shop = env.project()
    own_service(env, "1.0")
    env.roke("service", "add", "thing", cwd=shop)
    own_service(env, "2.0")
    env.roke("service", "upgrade", cwd=shop)
    assert env_value(env.project_env(), "THING_VERSION") == "2.0"


def test_upgrade_errors(env):
    shop = env.project()
    env.roke("service", "add", "postgres", cwd=shop)
    r = env.roke("service", "upgrade", "redis", cwd=shop)
    assert r.code != 0 and "redis is not in shop" in r.err
    r = env.roke("service", "upgrade", "nope", cwd=shop)
    assert r.code != 0 and "unknown service" in r.err
    r = env.roke("service", "add", "redis", "--major", cwd=shop)
    assert r.code != 0 and "--major only applies" in r.err


def test_read_only_commands_do_not_pin(env):
    shop = env.project()
    env.roke("settings", "-s", "postgres", cwd=shop)
    env.roke("service", cwd=shop)
    assert not env.project_env().exists()
