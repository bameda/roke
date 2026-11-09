"""Stable project identities, first-use adoption, collisions and moves."""

import hashlib
import json
import stat
from concurrent.futures import ThreadPoolExecutor

import pytest
from helpers import project_name


def registry(env):
    return env.config / ".local" / "projects.json"


def test_first_run_preserves_legacy_compose_and_settings(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\nPOSTGRES_DB=existing\n")
    before = f"roke-shop-{hashlib.sha1(str(shop).encode()).hexdigest()[:8]}"
    r = env.roke(cwd=shop)
    assert r.code == 0, r.text
    assert project_name(r.last("run")) == before
    entry = json.loads(registry(env).read_text())["shop"]
    assert entry == {"path": str(shop), "compose_name": before}
    assert "POSTGRES_DB=existing" in env.project_env().read_text()
    assert stat.S_IMODE(registry(env).stat().st_mode) == 0o600
    assert (registry(env).parent / ".gitignore").read_text() == "*\n"


def test_same_basename_requires_another_id(env):
    shop = env.project()
    assert env.roke(cwd=shop).code == 0
    other = env.tmp / "elsewhere" / "shop"
    other.mkdir(parents=True)
    r = env.roke(cwd=other)
    assert r.code != 0 and "choose another ID" in r.err
    assert not r.compose_calls("run")
    r = env.roke("--id", "other-shop", cwd=other)
    assert r.code == 0, r.text
    assert r.last("run")["env"]["ROKE_PROJECT_CONFIG"].endswith("/projects/other-shop")
    assert "ID        other-shop" in env.roke("settings", cwd=other).out


def test_explicit_id_adopts_unclaimed_legacy_settings(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\nPOSTGRES_DB=existing\n")
    r = env.roke("--id", "my-shop", cwd=shop)
    assert r.code == 0, r.text
    assert "POSTGRES_DB=existing" in env.project_env("my-shop").read_text()
    assert r.last("run")["env"]["ROKE_SERVICES"] == "postgres"
    assert "ID        my-shop" in env.roke("settings", cwd=shop).out


def test_colliding_project_never_copies_another_projects_secrets(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\n")
    env.append(env.config / "projects" / "shop" / "secrets.env", "TOKEN=private\n")
    assert env.roke(cwd=shop).code == 0
    other = env.tmp / "elsewhere" / "shop"
    other.mkdir(parents=True)
    r = env.roke("--id", "other-shop", cwd=other)
    assert r.code == 0, r.text
    assert not (env.config / "projects" / "other-shop" / "secrets.env").exists()
    assert r.last("run")["env"]["ROKE_SERVICES"] == ""


def test_move_preserves_id_compose_and_configuration(env):
    shop = env.project()
    before = env.roke(cwd=shop).last("run")
    moved = shop.with_name("renamed")
    shop.rename(moved)
    r = env.roke("--id", "shop", "-C", str(moved))
    assert r.code == 0, r.text
    assert project_name(r.last("run")) == project_name(before)
    assert r.last("run")["env"]["PROJECT_DIR"] == str(moved)
    assert r.last("run")["env"]["ROKE_PROJECT_CONFIG"] == before["env"]["ROKE_PROJECT_CONFIG"]
    assert "ID        shop" in env.roke("settings", cwd=moved).out


def test_existing_location_cannot_be_taken_over(env):
    shop = env.project()
    env.roke(cwd=shop)
    r = env.roke("--id", "shop", cwd=env.project("copy"))
    assert r.code != 0 and "registered at" in r.err
    assert json.loads(registry(env).read_text())["shop"]["path"] == str(shop)


@pytest.mark.parametrize("project_id", ["../outside", ".", "..", "_bad", "bad/name"])
def test_invalid_ids(env, project_id):
    r = env.roke("--id", project_id, cwd=env.project())
    assert r.code != 0 and "invalid project ID" in r.err
    assert not registry(env).exists()


def test_read_only_commands_do_not_register(env):
    shop = env.project()
    for command in ("settings", "doctor", "logs"):
        assert env.roke(command, cwd=shop).code == 0
    assert not registry(env).exists()


def test_corrupt_registry_is_not_replaced(env):
    shop = env.project()
    path = registry(env)
    path.parent.mkdir()
    path.write_text("broken")
    r = env.roke(cwd=shop)
    assert r.code != 0 and "cannot read project registry" in r.err
    assert path.read_text() == "broken"


def test_global_commands_do_not_claim_or_depend_on_project_ids(env):
    shop = env.project()
    assert env.roke(cwd=shop).code == 0
    other = env.tmp / "elsewhere" / "shop"
    other.mkdir(parents=True)
    before = registry(env).read_text()
    r = env.roke("agent", "use", "codex", "--global", cwd=other)
    assert r.code == 0, r.text
    assert registry(env).read_text() == before
    assert env.roke("--id", "shop", "agent", "use", "codex", "--global", cwd=other).code != 0


def test_same_registered_path_cannot_be_given_another_id(env):
    shop = env.project()
    assert env.roke(cwd=shop).code == 0
    before = registry(env).read_text()
    r = env.roke("--id", "different", cwd=shop)
    assert r.code != 0 and "already registered as shop" in r.err
    assert registry(env).read_text() == before


def test_guards_run_before_registration(env):
    r = env.roke("--id", "unsafe", cwd=env.home)
    assert r.code != 0 and "refusing to mount your whole" in r.err
    assert not registry(env).exists()


def test_concurrent_registration_cannot_claim_the_same_id(env):
    first, second = env.project("first"), env.project("second")

    def start(path):
        return env.roke(
            "--id", "shared", cwd=path, env={"FAKE_DOCKER_LOG": str(path / "docker.log")}
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(start, [first, second]))
    assert sorted(r.code for r in results) == [0, 1]
    entries = json.loads(registry(env).read_text())
    assert list(entries) == ["shared"]


def test_id_after_commands_and_group_arguments(env):
    shop = env.project()
    r = env.roke("run", "--id", "alias", cwd=shop)
    assert r.code == 0, r.text
    assert env.roke("service", "add", "redis", cwd=shop).code == 0
    assert env.project_env("alias").exists()
    assert "ID        alias" in env.roke("settings", cwd=shop).out
    assert "redis" in env.roke("service", cwd=shop).out


def test_project_options_before_passthrough_arguments(env):
    shop = env.project()
    r = env.roke("exec", "--id", "alias", "echo", "--id", "child", cwd=shop)
    assert r.code == 0, r.text
    assert r.last("run")["args"][-3:] == ["echo", "--id", "child"]
    r = env.roke("logs", "-C", str(shop), "--tail", "10", "gateway", cwd=env.home)
    assert r.last("logs")["args"][-4:] == ["logs", "--tail", "10", "gateway"]


def test_directory_after_settings_command(env):
    shop = env.project()
    r = env.roke("settings", "-C", str(shop), cwd=env.home)
    assert r.code == 0, r.text
    assert str(shop) in r.out and "ID        shop" in r.out
    assert not registry(env).exists()


@pytest.mark.parametrize("args", [("run",), ("doctor",), ("logs",), ("service", "list")])
def test_missing_trailing_id_is_reported(env, args):
    r = env.roke(*args, "--id", cwd=env.project())
    assert r.code != 0 and "needs a project ID" in r.err


@pytest.mark.parametrize(
    "args",
    [
        ("settings",),
        ("doctor",),
        ("logs",),
        ("service", "add", "redis"),
        ("settings", "edit"),
        ("down",),
    ],
)
def test_id_is_reserved_for_preparing_or_starting_projects(env, args):
    r = env.roke(*args, "--id", "alias", cwd=env.project())
    assert r.code != 0 and "--id is for preparing or starting a project" in r.err
    assert not registry(env).exists()


def test_build_registers_custom_id_for_subsequent_commands(env):
    shop = env.project()
    r = env.roke("build", "--id", "alias", cwd=shop)
    assert r.code == 0, r.text
    assert r.last("build")["env"]["ROKE_PROJECT_CONFIG"].endswith("/projects/alias")
    assert not r.compose_calls("run")
    assert "ID        alias" in env.roke("settings", cwd=shop).out
    assert env.roke(cwd=shop).last("run")["env"]["ROKE_PROJECT_CONFIG"].endswith("/projects/alias")
