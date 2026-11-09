"""Read-only checks for a project's configuration and local prerequisites."""

import shutil
import subprocess

from roke.ui import die
from roke.workspace import Workspace


def run(req) -> int:
    ws = Workspace(req).open()
    ws.load_all(required_agent=True)
    print(f"Project   {ws.project.dir}")
    print(f"Agent     {ws.agent} (configured in ROKE_AGENTS)")
    print(f"Services  {', '.join(ws.selected) or 'none'}")
    print(f"Network   {ws.network}")
    issues = False
    for name in ws.selected_mcps:
        if name in ws.resolved_mcps:
            print(f"MCP       {name}: ready")
        else:
            definition = ws.mcps.definition(name)
            missing = [key for key in definition.get("requires", []) if not ws.env.get(key)]
            reason = f"set {', '.join(missing)} in secrets.env" if missing else "set its variables"
            print(f"MCP       {name}: left out ({reason})")
            issues = True
    if not shutil.which("docker"):
        die("Docker is not installed; install Docker with the Compose plugin")
    version = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    if version.returncode:
        die("the Docker Compose plugin (v2) is missing")
    print("Docker    Compose available")
    if subprocess.run(["docker", "info"], capture_output=True).returncode:
        die("cannot connect to the Docker daemon; start Docker and try again")
    print("Docker    daemon available")
    if subprocess.run(
        ["docker", "image", "inspect", "roke:latest"], capture_output=True
    ).returncode:
        print("Image     roke:latest missing (run roke build)")
        issues = True
    else:
        print("Image     roke:latest available")
    compose = ws.prepare_compose(create_agent_dir=False)
    result = compose.call("config", "--quiet", capture=True)
    if result.returncode:
        detail = result.stderr.strip() or "docker compose config failed"
        die(f"invalid Compose configuration: {detail}")
    print("Compose   valid")
    return 1 if issues else 0
