"""CI must fail on missing requirements and unexpected skips; local runs may skip."""

import os
import subprocess
import sys

import pytest
from conftest import REPO


def nested_pytest(tmp_path, files, *, strict=False, require_compose=False, compose_override=""):
    # Reuse the actual hooks in an isolated pytest process. Its fake projects
    # and Docker fixtures are not used by these tiny tests.
    source = (REPO / "tests" / "conftest.py").read_text()
    (tmp_path / "conftest.py").write_text(source + compose_override)
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    env = {key: value for key, value in os.environ.items() if not key.startswith("ROKE_")}
    if strict:
        env["ROKE_REQUIRE_NO_SKIPS"] = "1"
    if require_compose:
        env["ROKE_REQUIRE_COMPOSE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize(
    "skip",
    [
        "import pytest\ndef test_optional(): pytest.skip('optional dependency')\n",
        "import pytest\npytest.skip('optional module', allow_module_level=True)\n",
    ],
)
def test_skips_are_allowed_locally_but_fail_strict_ci(tmp_path, skip):
    files = {"test_ok.py": "def test_ok(): pass\n", "test_optional.py": skip}
    local = nested_pytest(tmp_path, files)
    assert local.returncode == 0, local.stdout + local.stderr
    strict = nested_pytest(tmp_path, files, strict=True)
    assert strict.returncode == 1
    assert "CI requires all selected tests to run: 1 skipped" in strict.stderr


def test_ci_fails_before_tests_if_compose_is_missing(tmp_path):
    result = nested_pytest(
        tmp_path,
        {"test_ok.py": "def test_ok(): pass\n"},
        require_compose=True,
        compose_override="\ndef real_compose(): return None\n",
    )
    assert result.returncode == 4
    assert "CI requires a real Docker Compose binary" in result.stderr


def test_strict_ci_passes_without_skips(tmp_path):
    result = nested_pytest(tmp_path, {"test_ok.py": "def test_ok(): pass\n"}, strict=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("status", [0, 1])
def test_ci_checks_that_compose_can_run(tmp_path, status):
    binary = tmp_path / "fake-compose"
    binary.write_text(f"#!/bin/sh\nexit {status}\n")
    binary.chmod(0o755)
    result = nested_pytest(
        tmp_path,
        {"test_ok.py": "def test_ok(): pass\n"},
        require_compose=True,
        compose_override=f"\ndef real_compose(): return {str(binary)!r}\n",
    )
    assert result.returncode == (4 if status else 0)
    if status:
        assert "CI requires a working Docker Compose binary" in result.stderr
