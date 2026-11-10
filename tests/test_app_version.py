"""The application version works without a configured project or Docker."""

import pytest
from conftest import REPO
from helpers import after


@pytest.mark.parametrize("command", ["version", "--version"])
def test_version_needs_no_configuration_or_docker(bare_env, command):
    result = bare_env.roke(command, env={"FAKE_DOCKER_FAIL": "info"})
    assert result.code == 0, result.text
    assert result.out == f"roke {(REPO / 'VERSION').read_text().strip()}\n"
    assert not result.err
    assert not result.calls
    assert not bare_env.config.exists()


@pytest.mark.parametrize("command", ["version", "--version"])
def test_version_uses_the_installation_not_the_current_project(bare_env, command):
    project = bare_env.project()
    (project / "VERSION").write_text("a-different-project-version\n")
    result = bare_env.roke(command, cwd=project)
    assert result.code == 0, result.text
    assert result.out == f"roke {(REPO / 'VERSION').read_text().strip()}\n"
    assert not result.calls


@pytest.mark.parametrize("extra", ["run", "--yaml"])
@pytest.mark.parametrize("command", ["version", "--version"])
def test_version_rejects_extra_arguments_without_starting_a_session(bare_env, command, extra):
    result = bare_env.roke(command, extra)
    assert result.code != 0
    assert "roke version" in result.err or "usage: roke --version" in result.err
    assert not result.calls


def test_exec_passes_version_option_to_the_command(env):
    result = env.roke("exec", "python3", "--version", cwd=env.project())
    assert result.code == 0, result.text
    assert after(result.last("run"), "box") == ["python3", "--version"]
