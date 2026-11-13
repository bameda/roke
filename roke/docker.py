"""Everything that talks to Docker: checking it is there, listing the
running roke projects, and docker compose for a project."""

import json
import re
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


def available() -> bool:
    """Whether Docker and its compose plugin are there, without failing."""
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "compose", "version"], capture_output=True).returncode == 0


def _output(args: list[str], operation: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        die(f"could not {operation}: {result.stderr.strip() or 'Docker command failed'}")
    return result.stdout


BOX_IMAGE = re.compile(r"roke:(build-[0-9a-f]+|latest)")


def box_images() -> list[dict[str, str]]:
    """The box images on this machine: roke:build-<hash>, and the roke:latest
    of the versions that built a single image."""
    fmt = "{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}"
    out = _output(["docker", "images", "roke", "--format", fmt], "list images")
    rows = [line.split("\t") for line in out.splitlines()]
    return [
        dict(zip(("tag", "id", "size", "created"), row, strict=True))
        for row in rows
        if len(row) == 4 and BOX_IMAGE.fullmatch(row[0])
    ]


def remove_image(tag: str) -> str | None:
    """Remove an image tag. None when it is gone, or why it is not: Docker
    refuses an image that a container, even a stopped one, still uses."""
    result = subprocess.run(["docker", "rmi", tag], capture_output=True, text=True)
    if result.returncode == 0:
        return None
    reason = (result.stderr.strip().splitlines() or ["Docker could not remove it"])[-1]
    return reason.removeprefix("Error response from daemon: ")


def running_projects() -> list[str]:
    """The compose projects of roke that are running."""
    out = _output(
        ["docker", "compose", "ls", "-q", "--filter", "name=roke-"], "list running roke projects"
    )
    return out.split()


def running_containers(project: str) -> list[dict[str, str]]:
    """The project's running containers: service, whether it is a session
    (a one-off run of the box), the hash of its configuration, and its id."""
    fmt = (
        '{{.Label "com.docker.compose.service"}}\t{{.Label "com.docker.compose.oneoff"}}\t'
        '{{.Label "com.docker.compose.config-hash"}}\t{{.ID}}'
    )
    out = _output(
        [
            "docker",
            "ps",
            "--filter",
            f"label=com.docker.compose.project={project}",
            "--format",
            fmt,
        ],
        "list project containers",
    )
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 4:
            die("could not read Docker's container list")
        rows.append(dict(zip(("service", "oneoff", "hash", "id"), parts, strict=True)))
    return rows


def container_env(container: str) -> dict[str, str]:
    out = _output(
        ["docker", "inspect", "--format", "{{json .Config.Env}}", container],
        f"inspect container {container}",
    )
    try:
        values = json.loads(out)
    except ValueError:
        die(f"could not read Docker's environment for container {container}")
    if values is None:
        return {}
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        die(f"could not read Docker's environment for container {container}")
    return dict(item.split("=", 1) for item in values if "=" in item)


def published_configuration(containers: list[dict[str, str]]) -> dict:
    """Published bindings and gateway forwards of the running containers,
    in the same shape as resolved Compose configuration."""
    services: dict = {}
    for container in containers:
        name, ident = container["service"], container["id"]
        out = _output(
            ["docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", ident],
            f"read published ports of container {ident}",
        )
        try:
            bindings = json.loads(out)
            if bindings is None:
                bindings = {}
            if not isinstance(bindings, dict):
                raise ValueError
            service = services.setdefault(name, {"ports": []})
            for target, addresses in bindings.items():
                port, protocol = target.split("/")
                for address in addresses or []:
                    if not all(isinstance(address[key], str) for key in ("HostIp", "HostPort")):
                        raise ValueError
                    service["ports"].append(
                        {
                            "target": port,
                            "protocol": protocol,
                            "host_ip": address["HostIp"],
                            "published": address["HostPort"],
                        }
                    )
        except (ValueError, TypeError, KeyError, AttributeError):
            die(f"could not read published ports of container {ident}")
        if name == "gateway":
            service["environment"] = {
                key: value
                for key, value in container_env(ident).items()
                if key.startswith("ROKE_FORWARD_")
            }
    return {"services": services}


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

    def call(
        self, *args: str, files=None, capture=False, capture_stderr=False
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            self.command(*args, files=files),
            env=self.env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture or capture_stderr else None,
            text=True,
        )

    def running(self, service: str) -> bool:
        out = self.call("ps", "--status", "running", "--quiet", service, capture=True)
        if out.returncode:
            detail = out.stderr.strip() or "docker compose ps failed"
            die(f"could not check whether {service} is running: {detail}")
        return bool(out.stdout.strip())

    def config_hashes(self) -> dict[str, str]:
        """The hash of each service's configuration, as compose computes it to
        decide whether a running container must be recreated."""
        result = self.call("config", "--hash", "*", capture=True)
        if result.returncode:
            detail = result.stderr.strip() or "docker compose config failed"
            die(f"could not check Compose configuration: {detail}")
        return dict(
            line.split(None, 1) for line in result.stdout.splitlines() if " " in line.strip()
        )

    def config(self, files=None) -> dict:
        """The resolved configuration, as docker compose reports it."""
        out = self.call("config", "--format", "json", files=files, capture=True)
        if out.returncode:
            die(
                "could not read the project's compose configuration: "
                + (out.stderr.strip() or "docker compose config failed")
            )
        try:
            return json.loads(out.stdout)
        except ValueError:
            die(
                "could not read the project's compose configuration: "
                + (out.stderr.strip() or "docker compose config failed")
            )
