"""The project's box: run (also continue, shell and exec), urls, logs, build,
down and purge."""

import ipaddress
import re
import sys

from roke import acp, settings
from roke import urls as urls_output
from roke.docker import (
    address_pools_exhausted,
    container_env,
    published_configuration,
    require_docker,
    running_containers,
    running_projects,
    stop_project,
)
from roke.ui import die, info
from roke.workspace import Workspace

OPENCODE_UI_PORT = "4096"
# Claude Code settings that also turn off the feature flags Remote Control needs.
FLAGS_OFF_BY = ("DISABLE_TELEMETRY", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC")


def run(req) -> int:
    ws = Workspace(req).open(docker=True, register_project=True)
    ws.load_all(required_agent=True)
    new_project = not ws.project.env_file.exists()
    command = ui_command(ws, req) if req.ui else req.cmd
    ws.pin_versions(ws.selected)
    compose = ws.prepare_compose(publish=True)
    if req.ui and ws.agent == "opencode":
        check_ui_binding(compose.config())
    p = ws.project
    args = ["--rm"]
    if req.command == "continue":
        args += ["-e", "ROKE_CONTINUE=1"]
    if req.command == "acp":
        # The editor speaks to the adapter on standard input and output.
        args += ["-e", "ROKE_ACP=1", "-T"]
    elif not (sys.stdin.isatty() and sys.stdout.isatty()):
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
    if not protect_running_sessions(ws, compose):
        # No session is open, so a container of a service that is no longer
        # the project's serves nobody: compose would only warn about it, and
        # advise an option roke does not offer. Its data stays in its volumes.
        args.append("--remove-orphans")
    if req.save:
        save_options(ws, req)
    elif req.command in ("run", "continue"):
        session_notice(ws, req, new_project)
    if req.command == "acp":
        # Quiet progress: nothing from Compose may reach the editor's stream.
        session = compose.command("--progress", "quiet", "run", *args, "box")
        return explain_failure(acp.serve(session, compose.env, p.dir))
    if req.ui and ws.agent == "opencode":
        info(f"OpenCode UI: http://127.0.0.1:{OPENCODE_UI_PORT} (use the server password)")
    elif req.ui:
        info(
            "Remote Control: open the session URL Claude Code prints, or find the session "
            "at claude.ai/code or in the Claude app"
        )
    return explain_failure(compose.call("run", *args, "box", *command).returncode)


def explain_failure(code: int) -> int:
    """compose exits with 1 when it cannot start the session: when that is
    because Docker has run out of subnets, say what to do, since compose only
    says that the address pools are fully subnetted."""
    if code == 1 and address_pools_exhausted():
        info(
            "Docker has no subnet left for this project's networks: its address pools are "
            "used up (each roke project uses two, and Docker's defaults allow about 30). "
            "roke down --all stops every project and frees them, docker network prune "
            "removes unused ones, and docs/troubleshooting.md says how to give Docker more"
        )
    return code


def ui_command(ws, req) -> list[str]:
    """What --ui runs: OpenCode's web interface, or Claude Code with Remote
    Control, which also keeps the session in the terminal."""
    if ws.agent == "opencode":
        if req.command == "continue":
            die("use roke --ui and select the conversation in the OpenCode interface")
        if OPENCODE_UI_PORT not in ws.ports:
            ws.ports.append(OPENCODE_UI_PORT)
        return ["opencode", "serve", "--hostname", "0.0.0.0", "--port", OPENCODE_UI_PORT]
    if ws.agent == "claude":
        if ws.env.get("ANTHROPIC_API_KEY"):
            info(
                "Remote Control needs a claude.ai login: with ANTHROPIC_API_KEY set, Claude "
                "Code uses the API key and refuses it; remove the key from secrets.env"
            )
        flags = [v for v in FLAGS_OFF_BY if ws.env.get(v)]
        if flags:
            info(
                f"{' and '.join(flags)} turn off the feature flags Remote Control needs: "
                f"remove {'it' if len(flags) == 1 else 'them'} from your settings"
            )
        resume = ["--continue"] if req.command == "continue" else []
        return ["claude", *resume, "--remote-control", ws.project.name]
    die(
        f"--ui is available for OpenCode (its web interface) and Claude Code (Remote "
        f"Control), not for {ws.agent}: to use it from an editor, see roke acp"
    )


def check_ui_binding(config: dict) -> None:
    """Reject mappings that would publish the UI beyond the host loopback."""
    if OPENCODE_UI_PORT in urls_output.forwards(config):
        die(f"OpenCode UI port {OPENCODE_UI_PORT} is already forwarded to a service")
    gateway = config.get("services", {}).get("gateway", {})
    for binding in gateway.get("ports") or []:
        if (
            str(binding.get("target")) != OPENCODE_UI_PORT
            or binding.get("protocol", "tcp") != "tcp"
        ):
            continue
        address = ipaddress.ip_address(binding.get("host_ip") or "0.0.0.0")
        if not address.is_loopback:
            die(f"OpenCode UI port {OPENCODE_UI_PORT} must be published on loopback only")


def urls(req) -> int:
    ws = Workspace(req).open(docker=True)
    ws.load_all()
    compose = ws.prepare_compose(publish=True)
    services = {s: compose.config(ws.base_files + [ws.services.file(s)]) for s in ws.selected}
    containers = running_containers(compose.name)
    print(
        urls_output.render(
            ws.project.name,
            bool(containers),
            compose.config(),
            compose.config(ws.base_files),
            services,
            published_configuration(containers),
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
        failed = []
        for name in projects:
            info(f"stopping {name}")
            if stop_project(name):
                failed.append(name)
        if failed:
            die(f"could not stop projects: {', '.join(failed)}")
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


def protect_running_sessions(ws, compose) -> bool:
    """Refuse to start a session that would recreate a container another
    session is using: docker compose run recreates the running dependencies
    whose configuration changed, and recreating the gateway would leave the
    other session without network. Returns whether another session is open."""
    running = running_containers(compose.name)
    sessions = [c for c in running if c["service"] == "box" and c["oneoff"] == "True"]
    if not sessions:
        return False
    wanted = compose.config_hashes()
    changed = sorted(
        c["service"]
        for c in running
        if c["oneoff"] != "True" and c["service"] in wanted and wanted[c["service"]] != c["hash"]
    )
    if not changed:
        return True
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


def save_options(ws, req) -> None:
    """--save: keep the options of this session as the project's settings,
    once the session is sure to start."""
    path, kept = ws.project.env_file, []
    if req.agent:
        settings.set_value(path, "ROKE_AGENT", ws.agent)
        kept.append(f"agent {ws.agent}")
    if req.services is not None:
        names = ",".join(settings.split_list(req.services))
        settings.set_value(path, "ROKE_SERVICES", names)
        kept.append(f"services {names or 'none'}")
    if req.ports:
        settings.set_value(path, "ROKE_PORTS", ",".join(req.ports))
        kept.append(f"ports {' '.join(req.ports)}")
    if req.network:
        settings.set_value(path, "ROKE_NETWORK", req.network)
        kept.append(f"network {req.network}")
    if req.git_rw:
        settings.set_value(path, "ROKE_GIT_RW", "1")
        kept.append(".git read-write")
    if req.serena is not None:
        settings.set_value(path, "ROKE_SERENA", "1" if req.serena else "0")
        kept.append(f"Serena {'on' if req.serena else 'off'}")
    info(f"kept for {ws.project.name}, in {path}: {', '.join(kept)}")


def session_notice(ws, req, new_project: bool) -> None:
    """Say that the options of this session are not kept: --agent when it
    differs from the project's, and every option when the project is new,
    which is when it is worth knowing how to keep them."""
    if req.agent and ws.agent != ws.configured_agent:
        used = (
            f"the project uses {ws.configured_agent}"
            if ws.configured_agent
            else "no agent is set for the project"
        )
        info(
            f"{ws.agent} for this session only; {used}: "
            f"roke agent use {ws.agent}, or --save, keeps it"
        )
    elif new_project and req.given_options():
        info(
            f"this project has no settings of its own yet: --save keeps "
            f"{', '.join(req.given_options())} for it, and for the next sessions"
        )
