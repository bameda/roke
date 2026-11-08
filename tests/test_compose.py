"""Tests that need a real Docker Compose binary: the resolved configurations
of the example projects, and roke urls."""

import json
import os
import shutil
import subprocess

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
    assert "mailpit:1025 · mailpit:8025" in r.out
    assert "DATABASE_URL" not in r.out  # variables are in roke service show
    assert "roke service show NAME" in r.out


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


def test_service_show_has_the_variables_one_per_line(env, compose):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\nPOSTGRES_DB=shop\n")
    r = env.roke("service", "show", "postgres", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
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


def test_service_show(env, compose):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=postgres\nPOSTGRES_DB=shop\nPOSTGRES_VERSION=17\n")
    r = env.roke("service", "show", "postgres", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    assert "In this project: used" in r.out
    assert "POSTGRES_VERSION=17 (pinned;" in r.out and "available)" in r.out
    assert "DATABASE_URL=postgres://dev:dev@postgres:5432/shop" in r.out
    assert "# PostgreSQL (`postgres`)" in r.out  # its README
    r = env.roke("service", "show", "mailpit", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert "not used (roke service add mailpit)" in r.out
    assert "from your browser: http://127.0.0.1:8025" in r.out


def test_the_gateway_knows_the_host(env, compose):
    """host:PORT entries rely on host.docker.internal in the gateway."""
    out = subprocess.run(
        [compose, "-f", str(REPO / "compose.yaml"), "config", "--format", "json"],
        env={
            "ROKE_AGENT": "claude",
            "ROKE_CONFIG_DIR": str(env.config),
            "PROJECT_DIR": str(env.project()),
            "ROKE_PROJECT_CONFIG": str(env.config),
            "PATH": os.environ["PATH"],
        },
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    extra_hosts = json.loads(out)["services"]["gateway"]["extra_hosts"]
    assert "host.docker.internal" in str(extra_hosts) and "host-gateway" in str(extra_hosts)


def test_ldap_service(env, compose):
    shop = env.project()
    r = env.roke("service", "show", "ldap", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    assert "LDAP_URL=ldap://ldap:10389" in r.out
    assert "LDAP_BIND_DN=cn=admin,dc=planetexpress,dc=com" in r.out


def test_the_box_knows_its_network_policy(env, compose):
    """The agent's instructions rely on ROKE_NETWORK and the allowed list."""
    shop = env.project()
    env.roke("network", "add", "ui.example.com", cwd=shop)
    r = env.roke("urls", cwd=shop, env={"FAKE_REAL_COMPOSE": compose})
    assert r.code == 0, r.text
    out = subprocess.run(
        [compose, "-f", str(REPO / "compose.yaml"), "config", "--format", "json"],
        env={
            "ROKE_AGENT": "claude",
            "ROKE_CONFIG_DIR": str(env.config),
            "PROJECT_DIR": str(shop),
            "ROKE_PROJECT_CONFIG": str(env.config),
            "ROKE_NETWORK_ALLOW_ALL": "github.com ui.example.com",
            "PATH": os.environ["PATH"],
        },
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    box = json.loads(out)["services"]["box"]["environment"]
    assert box["ROKE_NETWORK"] == "restricted"
    assert box["ROKE_NETWORK_ALLOW_ALL"] == "github.com ui.example.com"
