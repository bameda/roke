"""Project diagnostics without starting containers or writing settings."""

import pytest
from conftest import REPO


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


def test_yaml_report_is_read_only_and_contains_no_secrets_or_paths(env):
    shop = env.project()
    env.write_project_env("ROKE_MCPS=github\n")
    env.append(env.config / "secrets.env", "GITHUB_PAT=private-token-value\n")
    before = sorted(str(path) for path in env.config.rglob("*"))
    r = env.roke("doctor", "--yaml", cwd=shop)
    assert r.code == 0, r.text
    assert r.out.startswith("schema_version: 1\nok: true\nversions:\n")
    assert f'  roke: "{(REPO / "VERSION").read_text().strip()}"' in r.out
    assert '  docker_compose: "v5.0.0-fake"' in r.out
    assert '  docker_client: "28.1.0-fake"' in r.out
    assert '  docker_engine: "27.5.0-fake"' in r.out
    assert "  compose:" not in r.out
    assert '  - name: "MCP github"' in r.out
    assert '    status: "FAIL"' not in r.out
    assert "private-token-value" not in r.text
    assert str(env.home) not in r.text
    assert not r.err
    assert sorted(str(path) for path in env.config.rglob("*")) == before


def test_yaml_report_keeps_client_version_when_daemon_is_unavailable(env):
    r = env.roke("doctor", "--yaml", cwd=env.project(), env={"FAKE_DOCKER_FAIL": "info"})
    assert r.code == 1
    assert "ok: false" in r.out
    assert '  docker_client: "28.1.0-fake"' in r.out
    assert "docker_engine:" not in r.out
    assert 'name: "Docker daemon"\n    status: "FAIL"' in r.out
    assert not r.err


@pytest.mark.parametrize(
    "output",
    [
        "invalid secret-value",
        "null",
        "[]",
        '{"Client": null, "Server": []}',
        '{"Client": {"Version": "secret-value"}, "Server": {"Version": 42}}',
    ],
)
def test_yaml_report_ignores_unusable_docker_versions(env, output):
    r = env.roke("doctor", "--yaml", cwd=env.project(), env={"FAKE_DOCKER_VERSION_OUTPUT": output})
    assert r.code == 0, r.text
    assert "ok: true" in r.out
    assert "docker_client:" not in r.out
    assert "docker_engine:" not in r.out
    assert "secret-value" not in r.text
    assert not r.err


def test_yaml_failure_reports_multiple_issues_without_raw_compose_errors(env):
    shop = env.project()
    env.write_project_env("ROKE_MCPS=github\n")
    r = env.roke(
        "doctor",
        "--yaml",
        cwd=shop,
        env={
            "FAKE_COMPOSE_FAIL": "config",
            "FAKE_COMPOSE_ERROR": "error: secret-value: https://private",
        },
    )
    assert r.code == 1
    assert "ok: false" in r.out
    assert 'name: "MCP github"' in r.out
    assert 'name: "Compose configuration"' in r.out
    assert 'status: "FAIL"' in r.out
    assert "secret-value" not in r.text and "https://private" not in r.text
    assert not r.err


def test_yaml_configuration_error_does_not_echo_invalid_values(env):
    shop = env.project()
    env.write_project_env("ROKE_SERVICES=secret-value\n")
    r = env.roke("doctor", "--yaml", cwd=shop)
    assert r.code == 1
    assert "ok: false" in r.out
    assert 'name: "Project configuration"' in r.out
    assert "secret-value" not in r.text
    assert not r.err


def test_yaml_report_when_configuration_is_missing(bare_env):
    r = bare_env.roke("doctor", "--yaml")
    assert r.code == 1
    assert r.out.startswith("schema_version: 1\nok: false\n")
    assert f'  roke: "{(REPO / "VERSION").read_text().strip()}"' in r.out
    assert not r.err
