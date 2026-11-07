"""Tests that need a real Docker Compose binary: the resolved configurations
of the example projects, and roke urls."""

import shutil

import pytest
from conftest import REPO

EXAMPLES = sorted(p.name for p in (REPO / "examples" / "projects").iterdir() if p.is_dir())


@pytest.mark.parametrize("example", EXAMPLES)
@pytest.mark.parametrize("agent", ["claude", "codex", "opencode"])
def test_example_projects_resolve(env, compose, example, agent):
    shutil.copytree(REPO / "examples" / "projects" / example, env.config / "projects" / example)
    project = env.project(example)
    r = env.roke("urls", "--agent", agent, cwd=project, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    assert "Reach from inside the box" in r.out


def test_urls(env, compose):
    shop = env.project()
    env.write_project_env(
        "ROKE_SERVICES=postgres,mailpit\nPOSTGRES_DB=shop\nMAILPIT_UI_PORT=18025\n"
    )
    r = env.roke("urls", "-p", "5173", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    assert "http://127.0.0.1:5173 (box port 5173)" in r.out
    assert "mailpit      http://127.0.0.1:18025" in r.out
    assert "DATABASE_URL=postgres://dev:dev@postgres:5432/shop" in r.out
    assert "mailpit:1025 · mailpit:8025" in r.out


def test_urls_does_not_need_the_image(env, compose):
    r = env.roke(
        "urls", cwd=env.project(), env={"FAKE_NO_IMAGE": "1", "FAKE_REAL_COMPOSE": compose}
    )
    assert r.code == 0, r.text


def test_urls_reports_an_unreadable_configuration(env):
    r = env.roke("urls", cwd=env.project())  # the fake docker answers with YAML
    assert r.code != 0
    assert "could not read the project's compose configuration" in r.err
    assert "Traceback" not in r.err


def test_urls_shows_one_variable_per_line(env, compose):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\nPOSTGRES_DB=shop\n")
    r = env.roke("urls", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    lines = [line.strip() for line in r.out.splitlines()]
    for var in ("PGHOST=postgres", "PGPORT=5432", "PGUSER=dev", "PGDATABASE=shop"):
        assert var in lines


def test_urls_with_service_mcps(env, compose):
    shop = env.project()
    env.roke("mcp", "add", "grafana", "postgres", cwd=shop)
    r = env.roke("urls", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    assert "grafana      http://127.0.0.1:3001" in r.out
    assert "postgres     postgres:5432" in r.out
