"""Read-only project checks, with an optional report suitable for sharing."""

import io
import json
import platform
import re
import shutil
import subprocess
from contextlib import nullcontext, redirect_stderr

from roke import releases, version
from roke.paths import config_dir
from roke.ports import normalize as normalize_ports
from roke.ui import Fail
from roke.workspace import Workspace


class Report:
    def __init__(self, as_yaml: bool):
        self.as_yaml = as_yaml
        self.checks: list[dict[str, str]] = []
        self.versions = {"roke": version.current(), "python": platform.python_version()}
        self.installation = releases.installation() if as_yaml else {}

    def add(self, name: str, passed: bool, detail: str = "", report_detail: str | None = None):
        status = "OK" if passed else "FAIL"
        check = {"name": name, "status": status}
        safe_detail = report_detail if report_detail is not None else detail
        if safe_detail:
            check["detail"] = safe_detail
        self.checks.append(check)
        if not self.as_yaml:
            print(f"{name}: {status}" + (f" ({detail})" if detail else ""))

    def finish(self) -> int:
        ok = all(check["status"] == "OK" for check in self.checks)
        if self.as_yaml:
            # JSON double-quoted strings are valid YAML scalars. Quote every
            # string so names containing colons or line breaks remain data.
            lines = ["schema_version: 1", f"ok: {str(ok).lower()}", "versions:"]
            lines += [f"  {key}: {json.dumps(value)}" for key, value in self.versions.items()]
            if self.installation:
                lines.append("installation:")
                lines += [
                    f"  {key}: {json.dumps(value)}" for key, value in self.installation.items()
                ]
            lines.append("checks:")
            for check in self.checks:
                lines.append(f"  - name: {json.dumps(check['name'])}")
                lines.append(f"    status: {json.dumps(check['status'])}")
                if "detail" in check:
                    lines.append(f"    detail: {json.dumps(check['detail'])}")
            print("\n".join(lines))
        return 0 if ok else 1


def run(req) -> int:
    report = Report(req.yaml)
    try:
        # Workspace diagnostics may quote user configuration. Keep them local
        # to normal doctor output; reports only contain explicitly chosen data.
        with redirect_stderr(io.StringIO()) if req.yaml else nullcontext():
            diagnose(req, report)
    except Fail:
        if not req.yaml:
            raise
        report.add("Project configuration", False, "Check configuration with roke settings")
    except OSError:
        if not req.yaml:
            raise
        report.add("Local tools", False, "Check local tools and file permissions")
    return report.finish()


def docker_versions(report: Report) -> None:
    result = subprocess.run(
        ["docker", "version", "--format", "{{json .}}"], capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return
    if not isinstance(data, dict):
        return
    # A failed daemon connection may still provide the client's version.
    for component, key in (("Client", "docker_client"), ("Server", "docker_engine")):
        if component == "Server" and result.returncode:
            continue
        details = data.get(component)
        version = details.get("Version") if isinstance(details, dict) else None
        # Only export version tokens, never arbitrary tool output or errors.
        if isinstance(version, str) and re.fullmatch(r"v?\d[\w.+-]*", version):
            report.versions[key] = version


def check_docker(report: Report) -> bool:
    """Docker, its Compose plugin and its daemon: whether all three work."""
    if not shutil.which("docker"):
        report.add("Docker", False, "install Docker with the Compose plugin")
        return False
    if report.as_yaml:
        docker_versions(report)
    version = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    if version.returncode:
        report.add("Docker Compose", False, "install the Compose plugin v2")
        return False
    match = re.fullmatch(r"Docker Compose version (v?\d[\w.+-]*)", version.stdout.strip())
    if match:
        report.versions["docker_compose"] = match[1]
    report.add("Docker Compose", True)
    if subprocess.run(["docker", "info"], capture_output=True).returncode:
        report.add("Docker daemon", False, "start Docker and try again")
        return False
    report.add("Docker daemon", True)
    return True


def step(report: Report, name: str, hint: str, action) -> bool:
    """Run ACTION as the check NAME: it fails with roke's own message, or with
    HINT in a shareable report, which never quotes your configuration."""
    try:
        action()
    except Fail as exc:
        report.add(name, False, str(exc), report_detail=hint)
        return False
    report.add(name, True)
    return True


def agent(req) -> None:
    """Whether an agent is chosen and installed. A workspace of its own: the
    project's one has already settled on "none" when none is chosen."""
    probe = Workspace(req)
    probe.open()
    probe.load_settings()
    probe.choose_agent(required=True)


def check_project(req, report: Report) -> Workspace | None:
    """The configuration, the directory and the project's settings. Each check
    needs the one before it; None when one fails."""
    if not config_dir().is_dir():
        report.add("Configuration directory", False, "create it with roke init")
        return None
    report.add("Configuration directory", True)
    ws = Workspace(req)
    if not step(
        report,
        "Project directory",
        "This directory cannot be used as a project: see roke help",
        ws.open,
    ):
        return None

    def configuration() -> None:
        ws.load_all()
        normalize_ports(ws.ports, "-p or ROKE_PORTS")

    if not step(
        report, "Project configuration", "Check configuration with roke settings", configuration
    ):
        return None
    step(report, "Coding agent", "Choose one with roke agent use NAME", lambda: agent(req))
    for name in ws.selected_mcps:
        if name in ws.resolved_mcps:
            report.add(f"MCP {name}", True)
        else:
            definition = ws.mcps.definition(name)
            missing = [key for key in definition.get("requires", []) if not ws.env.get(key)]
            reason = f"set {', '.join(missing)} in secrets.env" if missing else "set its variables"
            report.add(f"MCP {name}", False, reason)
    return ws


def check_compose(ws: Workspace, report: Report) -> None:
    compose = ws.prepare_compose(create_agent_dir=False)
    result = compose.call("config", "--format", "json", capture=True)
    if result.returncode:
        detail = result.stderr.strip() or "docker compose config failed"
        report.add(
            "Compose configuration",
            False,
            detail,
            report_detail="Check Compose configuration with roke doctor",
        )
        return
    try:
        image = json.loads(result.stdout)["services"]["box"]["image"]
        if not isinstance(image, str) or not image:
            raise ValueError("missing image")
    except (KeyError, TypeError, ValueError):
        report.add("Compose configuration", False, "cannot read the box image")
        return
    report.add("Compose configuration", True)
    missing_image = subprocess.run(
        ["docker", "image", "inspect", image], capture_output=True
    ).returncode
    report.add("Box image", not missing_image, "run roke build" if missing_image else "")


def diagnose(req, report: Report) -> None:
    """Every check that can run, whatever failed before: Docker does not need a
    project, and a project's settings do not need Docker."""
    docker_ready = check_docker(report)
    ws = check_project(req, report)
    if ws and docker_ready:
        check_compose(ws, report)
