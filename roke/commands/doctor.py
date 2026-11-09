"""Read-only checks for a project's configuration and local prerequisites."""

import shutil
import subprocess

from roke.workspace import Workspace


def run(req) -> int:
    ws = Workspace(req).open()
    ws.load_all(required_agent=True)
    print("Project configuration: OK")
    issues = False
    for name in ws.selected_mcps:
        if name in ws.resolved_mcps:
            print(f"MCP {name}: OK")
        else:
            definition = ws.mcps.definition(name)
            missing = [key for key in definition.get("requires", []) if not ws.env.get(key)]
            reason = f"set {', '.join(missing)} in secrets.env" if missing else "set its variables"
            print(f"MCP {name}: FAIL ({reason})")
            issues = True
    if not shutil.which("docker"):
        print("Docker: FAIL (install Docker with the Compose plugin)")
        return 1
    version = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    if version.returncode:
        print("Docker Compose: FAIL (install the Compose plugin v2)")
        return 1
    print("Docker Compose: OK")
    if subprocess.run(["docker", "info"], capture_output=True).returncode:
        print("Docker daemon: FAIL (start Docker and try again)")
        return 1
    print("Docker daemon: OK")
    if subprocess.run(
        ["docker", "image", "inspect", "roke:latest"], capture_output=True
    ).returncode:
        print("Box image: FAIL (run roke build)")
        issues = True
    else:
        print("Box image: OK")
    compose = ws.prepare_compose(create_agent_dir=False)
    result = compose.call("config", "--quiet", capture=True)
    if result.returncode:
        detail = result.stderr.strip() or "docker compose config failed"
        print(f"Compose configuration: FAIL ({detail})")
        issues = True
    else:
        print("Compose configuration: OK")
    return 1 if issues else 0
