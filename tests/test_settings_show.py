"""Inspect effective project settings by ID, independently of the current directory."""


def test_named_settings_match_current_project_without_writes(env):
    shop = env.project()
    env.write_project_env('ROKE_AGENT=codex\nROKE_SERVICES=redis\nROKE_PORTS="5173"\n')
    assert env.roke(cwd=shop).code == 0
    env.append(env.config / "projects" / "shop" / "secrets.env", "TOKEN=private_value\n")
    registry = env.config / ".local" / "projects.json"
    before = registry.read_text()
    current = env.roke("settings", cwd=shop)
    named = env.roke("settings", "show", "shop", cwd=env.home)
    assert named.code == 0, named.text
    assert named.out == current.out
    assert "private_value" not in named.text
    assert "TOKEN (project)" in named.out
    assert registry.read_text() == before
    assert not named.compose_calls("run")


def test_named_settings_work_when_project_path_is_missing(env):
    shop = env.project()
    env.write_project_env('ROKE_PORTS="5173"\n')
    assert env.roke("--id", "alias", cwd=shop).code == 0
    shop.rename(shop.with_name("moved"))
    registry = env.config / ".local" / "projects.json"
    before = registry.read_text()
    r = env.roke("settings", "show", "alias", cwd=env.home)
    assert r.code == 0, r.text
    assert f"Project   {shop}" in r.out
    assert "ID        alias" in r.out
    assert "Ports     5173" in r.out
    assert registry.read_text() == before


def test_named_settings_reject_unknown_ids_and_missing_operand(env):
    r = env.roke("settings", "show", "missing", cwd=env.home)
    assert r.code != 0 and "unknown project ID: 'missing'" in r.err
    assert not (env.config / ".local").exists()
    r = env.roke("settings", "show", cwd=env.home)
    assert r.code != 0 and "usage: roke settings show ID" in r.err
