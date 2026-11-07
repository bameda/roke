"""The project's box: run (also continue, shell and exec), urls, settings,
build, down and purge."""

import sys

from roke import urls as urls_output
from roke.commands.network import render_network
from roke.docker import require_docker, running_projects, stop_project
from roke.ui import info
from roke.workspace import Workspace


def run(req) -> int:
    ws = Workspace(req).open(docker=True)
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
        f"project: {p.dir}  ·  agent: {ws.agent}  ·  network: {ws.network}  ·  "
        f"services: {ws.env['ROKE_SERVICES'] or 'none'}  ·  "
        f".git: {'rw' if ws.git_rw else 'ro'}  ·  serena: {'yes' if ws.serena else 'no'}"
    )
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


def settings(req) -> None:
    ws = Workspace(req).open(guards=False)
    ws.load_all()
    p = ws.project
    files = [
        ws.global_env,
        ws.config / "secrets.env",
        p.env_file,
        p.config / "secrets.env",
        p.config / "compose.yaml",
        p.config / "AGENTS.md",
    ]
    found = " ".join(str(f.relative_to(ws.config)) for f in files if f.is_file())
    labels = []
    for name in ws.selected:
        origin = ws.services.origin(name)
        label = f"{name} [{origin}]" if origin else name
        if name in ws.mcp_services:
            label += f" (for MCP {ws.mcp_services[name]})"
        labels.append(label)
    agent = (
        "none chosen (roke agent use NAME --global)"
        if ws.agent == "none"
        else f"{ws.agent} ({ws.agent_source})"
    )
    print(
        "\n".join(
            [
                f"Project   {p.dir}",
                f"Settings  {ws.config}: {found or '(no files)'}",
                f"Agent     {agent}",
                f"Network   {ws.network} ({ws.network_source})",
                f"Services  {', '.join(labels) or 'none'}",
                f"Ports     {' '.join(ws.ports) or 'none'}",
                f"MCPs      {mcp_labels(ws) or 'none'}",
                f"Serena    {'on' if ws.serena else 'off'}",
                f".git      {'read-write' if ws.git_rw else 'read-only'}",
                "",
                render_network(ws),
            ]
        )
    )


def build(req) -> int:
    ws = Workspace(req).open(docker=True)
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


def mcp_labels(ws) -> str:
    """The project's MCP servers, marking those left out for missing secrets."""
    return ", ".join(
        name if name in ws.resolved_mcps else f"{name} (left out: needs secrets)"
        for name in ws.selected_mcps
    )
