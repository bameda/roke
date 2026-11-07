"""Everything that talks to Docker: checking it is there, listing the
running roke projects, and docker compose for a project."""

import json
import shutil
import subprocess
from pathlib import Path

from roke.ui import die


def require_docker(compose: bool = True) -> None:
    if not shutil.which("docker"):
        die("docker is not installed")
    if (
        compose
        and subprocess.run(["docker", "compose", "version"], capture_output=True).returncode != 0
    ):
        die("the 'docker compose' plugin (v2) is missing")


def running_projects() -> list[str]:
    """The compose projects of roke that are running."""
    out = subprocess.run(
        ["docker", "compose", "ls", "-q", "--filter", "name=roke-"], capture_output=True, text=True
    )
    return out.stdout.split()


def stop_project(name: str) -> int:
    return subprocess.run(["docker", "compose", "-p", name, "down", "--remove-orphans"]).returncode


class Compose:
    """docker compose for one project: its name, files and environment."""

    def __init__(self, box_dir: Path, name: str, files: list[Path], env: dict[str, str]):
        self.box_dir = box_dir
        self.name = name
        self.files = list(files)
        self.env = env

    def command(self, *args: str, files=None) -> list[str]:
        cmd = ["docker", "compose", "--project-directory", str(self.box_dir), "-p", self.name]
        for f in self.files if files is None else files:
            cmd += ["-f", str(f)]
        return cmd + list(args)

    def call(self, *args: str, files=None, capture=False) -> subprocess.CompletedProcess:
        return subprocess.run(
            self.command(*args, files=files), env=self.env, capture_output=capture, text=True
        )

    def running(self, service: str) -> bool:
        out = self.call("ps", "--status", "running", "--quiet", service, capture=True)
        return bool(out.stdout.strip())

    def config(self, files=None) -> dict:
        """The resolved configuration, as docker compose reports it."""
        out = self.call("config", "--format", "json", files=files, capture=True)
        try:
            return json.loads(out.stdout)
        except ValueError:
            die(
                "could not read the project's compose configuration: "
                + (out.stderr.strip() or "docker compose config failed")
            )
