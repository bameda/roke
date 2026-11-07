"""Shared fixtures: every test gets an isolated home, roke configuration and
projects, and runs the real `roke` command against a fake `docker`."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ROKE = REPO / "bin" / "roke"
FAKES = Path(__file__).resolve().parent / "fakes"


def real_compose():
    """The path of a real Docker Compose binary, if there is one."""
    found = shutil.which("docker-compose")
    if found:
        return found
    for candidate in (
        "/usr/libexec/docker/cli-plugins/docker-compose",
        "/usr/lib/docker/cli-plugins/docker-compose",
        os.path.expanduser("~/.docker/cli-plugins/docker-compose"),
    ):
        if os.access(candidate, os.X_OK):
            return candidate
    return None


class Result:
    def __init__(self, proc, calls):
        self.code = proc.returncode
        self.out = proc.stdout
        self.err = proc.stderr
        self.calls = calls

    @property
    def text(self):
        return self.out + self.err

    def compose_calls(self, verb=None):
        """The `docker compose` calls, optionally only those with VERB."""
        calls = [c for c in self.calls if c["args"][:1] == ["compose"]]
        if verb:
            calls = [c for c in calls if verb in c["args"]]
        return calls

    def last(self, verb):
        calls = self.compose_calls(verb)
        assert calls, f"no `docker compose ... {verb}` call; calls: {self.calls}"
        return calls[-1]


class Env:
    """An isolated environment: a home, a roke configuration and projects."""

    def __init__(self, tmp_path):
        self.tmp = tmp_path
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.config = self.home / ".config" / "roke"
        self.src = self.home / "src"
        self.src.mkdir()
        self.log = tmp_path / "docker.log"
        self.extra_env = {}

    def project(self, name="shop", git=True):
        path = self.src / name
        path.mkdir(exist_ok=True)
        if git:
            (path / ".git").mkdir(exist_ok=True)
        return path

    def project_env(self, name="shop"):
        return self.config / "projects" / name / "project.env"

    def write_project_env(self, text, name="shop"):
        p = self.project_env(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def append(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(text)

    def roke(self, *args, cwd=None, env=None):
        if self.log.exists():
            self.log.unlink()
        environ = {
            "PATH": f"{FAKES}:{os.environ['PATH']}",
            "HOME": str(self.home),
            "FAKE_DOCKER_LOG": str(self.log),
            "XDG_RUNTIME_DIR": str(self.tmp / "run"),
            "LANG": "C.UTF-8",
        }
        environ.update(self.extra_env)
        environ.update(env or {})
        proc = subprocess.run(
            [str(ROKE), *args],
            cwd=cwd or self.src,
            env=environ,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
        )
        calls = []
        if self.log.exists():
            calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return Result(proc, calls)


@pytest.fixture
def env(tmp_path):
    """An environment with an initialised configuration and a default agent."""
    e = Env(tmp_path)
    r = e.roke("init")
    assert r.code == 0, r.text
    e.append(e.config / "roke.env", "\nROKE_AGENT=claude\n")
    return e


@pytest.fixture
def bare_env(tmp_path):
    """An environment without any roke configuration yet."""
    return Env(tmp_path)


@pytest.fixture
def compose():
    path = real_compose()
    if not path:
        pytest.skip("needs a real Docker Compose binary")
    return path
