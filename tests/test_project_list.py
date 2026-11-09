"""Project inventory works independently of the current directory and Docker."""


def test_empty_inventory_is_read_only(env):
    r = env.roke("project", cwd=env.home)
    assert r.code == 0, r.text
    assert "No projects registered" in r.out
    assert not (env.config / ".local").exists()
    assert not r.calls


def test_lists_current_and_missing_paths_without_modifying_registry(env):
    first, second = env.project("first"), env.project("second")
    assert env.roke(cwd=first).code == 0
    assert env.roke(cwd=second).code == 0
    first.rename(first.with_name("moved"))
    registry = env.config / ".local" / "projects.json"
    before = registry.read_text()
    r = env.roke("project", cwd=env.home)
    assert r.code == 0, r.text
    assert f"first   missing  {first}" in r.out
    assert f"second  found    {second}" in r.out
    assert "roke --id ID" in r.out
    assert registry.read_text() == before
    assert not r.calls
    r = env.roke("project", "show", "first", cwd=env.home)
    assert r.code == 0 and f"Path      {first} (missing)" in r.out
    assert registry.read_text() == before
    assert not r.calls


def test_show_details_and_rejects_unknown_ids(env):
    first, second = env.project("first"), env.project("second")
    env.roke(cwd=first)
    env.roke(cwd=second)
    r = env.roke("project", "show", "first", cwd=env.home)
    assert r.code == 0 and str(first) in r.out and str(second) not in r.out
    assert "Compose   roke-first-" in r.out
    assert "ID        first" in r.out
    assert not r.calls
    r = env.roke("project", "show", "missing", cwd=env.home)
    assert r.code != 0 and "unknown project ID: 'missing'" in r.err


def test_inventory_help_and_invalid_arguments(env):
    for args in (("project", "--help"), ("help", "project")):
        assert "Projects" in env.roke(*args).out
    for args in (("project", "--global"), ("project", "extra"), ("project", "list", "extra")):
        assert env.roke(*args).code != 0
    for args in (("project", "--id", "first"), ("--id", "first", "project")):
        assert "roke project show ID" in env.roke(*args).err


def test_inventory_needs_configuration(bare_env):
    r = bare_env.roke("project")
    assert r.code != 0 and "roke init" in r.err
