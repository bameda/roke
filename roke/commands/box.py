"""The project's box: run (also continue, shell and exec), urls, settings,
build, down and purge."""

import re
import sys

from roke import urls as urls_output
from roke.docker import (
    container_env,
    require_docker,
    running_containers,
    running_projects,
    stop_project,
)
from roke.ui import die, info
from roke.workspace import Workspace


def run(req) -> int:
    ws = Workspace(req).open(docker=True, register_project=True)
    ws.load_all(required_agent=True)
    ws.pin_versions(ws.selected)
    compose = ws.prepare_compose(publish=True)
    p = ws.project
    args = ["--rm"]
    if req.command == "continue":
        args += ["-e", "ROKE_CONTINUE=1"]
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        args.append("-T")
    if (ws.config / "AGENTS.md").is_file():
        args += ["-v", f"{ws.config / 'AGENTS.md'}:/run/roke/user-AGENTS.md:ro"]
    if (p.config / "AGENTS.md").is_file():
        args += ["-v", f"{p.config / 'AGENTS.md'}:/run/roke/project-AGENTS.md:ro"]
    mcp_config = ws.write_mcp_config()
    if mcp_config:
        args += ["-v", f"{mcp_config}:/run/roke/mcp.json:ro"]
    # Read-only .git: prevents the agent from planting hooks or settings
    # (core.fsmonitor, core.hooksPath...) that would run on your host.
    if not ws.git_rw and (p.dir / ".git").is_dir():
        args += ["-v", f"{p.dir}/.git:{p.dir}/.git:ro", "-e", "ROKE_GIT_READONLY=1"]
    info(
        f"project: {p.dir}  ·  id: {p.name}  ·  agent: {ws.agent}  ·  network: {ws.network}  ·  "
        f"services: {ws.env['ROKE_SERVICES'] or 'none'}  ·  "
        f".git: {'rw' if ws.git_rw else 'ro'}  ·  serena: {'yes' if ws.serena else 'no'}"
    )
    protect_running_sessions(ws, compose)
    return compose.call("run", *args, "box", *req.cmd).returncode


def urls(req) -> int:
    ws = Workspace(req).open(docker=True)
    ws.load_all()
    compose = ws.prepare_compose(publish=True)
    services = {s: compose.config(ws.base_files + [ws.services.file(s)]) for s in ws.selected}
    print(
        urls_output.render(
            ws.project.name,
            compose.running("gateway"),
            compose.config(),
            compose.config(ws.base_files),
            services,
        )
    )
    return 0


def logs(req) -> int:
    ws = Workspace(req).open(docker=True)
    ws.load_all()
    compose = ws.prepare_compose(create_agent_dir=False)
    result = compose.call("logs", *req.cmd, capture_stderr=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
        if result.returncode and re.search(
            r"no such service|service .+ not found", result.stderr, re.I
        ):
            available = compose.call("config", "--services", capture=True)
            names = [name for name in available.stdout.splitlines() if name != "box"]
            if not available.returncode and names:
                print(f"Available logs: {', '.join(names)}", file=sys.stderr)
    return result.returncode


def build(req) -> int:
    ws = Workspace(req).open(docker=True, register_project=True)
    ws.load_all()
    args = ["build", "--pull"] + (["--no-cache"] if req.no_cache else [])
    return ws.prepare_compose().call(*args).returncode


def down(req) -> int:
    if req.all:
        require_docker(compose=False)
        projects = running_projects()
        for name in projects:
            info(f"stopping {name}")
            stop_project(name)
        if not projects:
            info("no roke project is running")
        return 0
    return _down(req, "--remove-orphans")


def purge(req) -> int:
    return _down(req, "--remove-orphans", "--volumes")


def _down(req, *args) -> int:
    ws = Workspace(req).open(docker=True)
    ws.load_all()
    return ws.prepare_compose(all_services=True).call("down", *args).returncode


def protect_running_sessions(ws, compose) -> None:
    """Refuse to start a session that would recreate a container another
    session is using: docker compose run recreates the running dependencies
    whose configuration changed, and recreating the gateway would leave the
    other session without network."""
    running = running_containers(compose.name)
    sessions = [c for c in running if c["service"] == "box" and c["oneoff"] == "True"]
    if not sessions:
        return
    wanted = compose.config_hashes()
    changed = sorted(
        c["service"]
        for c in running
        if c["oneoff"] != "True" and c["service"] in wanted and wanted[c["service"]] != c["hash"]
    )
    if not changed:
        return
    agents = sorted({container_env(c["id"]).get("ROKE_AGENT", "?") for c in sessions})
    if "gateway" in changed and any(agent != ws.agent for agent in agents):
        together = ",".join(sorted({*agents, ws.agent}))
        die(
            f"the project is already running {', '.join(agents)}, and its network does not "
            f"allow {ws.agent} too: set ROKE_PARALLEL_AGENTS={together} in the project's "
            "project.env, then finish that session (or run roke down) and start again"
        )
    die(
        "the project is already running a session, and starting this one would recreate "
        f"{', '.join(changed)}, cutting that session off (different ports, services or "
        "network): finish it first, or run roke down"
    )
