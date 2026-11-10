"""roke settings: what applies to the project and where it comes from, and
editing the settings files in your editor."""

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from roke import docker, settings
from roke.ui import Fail, die, info
from roke.workspace import Workspace

SECRET_NAME = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=", re.M)


# --- roke settings ------------------------------------------------------------------
def show(req) -> None:
    ws = Workspace(req).open(guards=False, registered_id=req.values[0] if req.sub == "show" else "")
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
    agent = (
        "none chosen (roke agent use NAME --global)"
        if ws.agent == "none"
        else f"{ws.agent} ({ws.agent_source})"
    )
    print(
        "\n".join(
            [
                f"Project   {p.dir}{state(p.compose_name)}",
                f"ID        {p.name}",
                f"Settings  {ws.config}: {found or '(no files)'}",
                f"Agent     {agent}",
                *([f"Parallel  {', '.join(ws.parallel_agents)}"] if ws.parallel_agents else []),
                f"Network   {network_summary(ws)}",
                f"Services  {service_labels(ws) or 'none'}",
                f"MCPs      {mcp_labels(ws) or 'none'}",
                f"Secrets   {secret_names(ws) or 'none'}",
                f"Ports     {' '.join(ws.ports) or 'none'}",
                f"Serena    {'on' if ws.serena else 'off'}",
                f".git      {'read-write' if ws.git_rw else 'read-only'}",
            ]
        )
    )


def state(compose_name: str) -> str:
    """ " (running)" or " (not running)", or nothing without Docker."""
    if not docker.available():
        return ""
    try:
        running = docker.running_containers(compose_name)
    except Fail as exc:
        info(str(exc))
        return " (Docker state unavailable)"
    return " (running)" if running else " (not running)"


def network_summary(ws) -> str:
    mode = f"{ws.network} ({ws.network_source})"
    if ws.network == "open":
        return f"{mode}: no limits (roke network)"
    layers = {label: entries for label, _, entries in ws.allow_layers()}
    total = len({d for entries in layers.values() for d in entries})
    own = len(layers.get("project", []))
    mine = f", {own} of them the project's" if own else ""
    return f"{mode}: {total} destinations allowed{mine} (roke network)"


def service_labels(ws) -> str:
    labels = []
    for name in ws.selected:
        versions = []
        for var, default in ws.services.versions(name).items():
            pinned = settings.value_of(ws.project.env_file, var)
            versions.append(
                pinned or f"{ws.current_version(var, default, ws.env)} (not pinned yet)"
            )
        label = " ".join([name, *versions])
        origin = ws.services.origin(name)
        if origin:
            label += f" [{origin}]"
        if name in ws.mcp_services:
            label += f" (for MCP {ws.mcp_services[name]})"
        labels.append(label)
    return ", ".join(labels)


def mcp_labels(ws) -> str:
    """The project's MCP servers, marking those left out for missing secrets."""
    return ", ".join(
        name if name in ws.resolved_mcps else f"{name} (left out: needs secrets)"
        for name in ws.selected_mcps
    )


def secret_names(ws) -> str:
    """The names of the secrets set, never their values."""
    names = []
    for path, where in (
        (ws.config / "secrets.env", "global"),
        (ws.project.config / "secrets.env", "project"),
    ):
        if path.is_file():
            names += [f"{n} ({where})" for n in SECRET_NAME.findall(path.read_text())]
    return ", ".join(names)


# --- roke settings edit -------------------------------------------------------------
TEMPLATES = {
    "env": """\
# Settings for {name}: they add to ~/.config/roke/roke.env and win over it.
# See docs/configuration.md for every setting.
# ROKE_SERVICES=postgres,mailpit     (or roke service add NAME)
# ROKE_PORTS="5173"                  ports of the box to publish on 127.0.0.1
# ROKE_SERENA=1                      semantic code navigation
# ROKE_AGENT=claude                  (or roke agent use NAME)
""",
    "env-global": """\
# Settings for every project. See docs/configuration.md.
""",
    "secrets": """\
# Secrets: API keys and tokens, passed to the box as environment variables.
# Never committed. Only their names are shown by roke settings.
""",
    "compose": """\
# Compose overrides for {name}: extra services, environment, volumes...
# See docs/configuration.md.
services: {{}}
""",
    "instructions": """\
# Instructions for the agent in {name}

Private: not in the project's repository. The agent gets them after the
box's instructions and yours.
""",
    "instructions-global": """\
# Your instructions for the agent, in every project
""",
    "tools": """\
# Tools for this project, installed by mise when the box starts.
# See https://mise.jdx.dev/configuration.html
[tools]
# node = "22"
# python = "3.13"
""",
}
EDITABLE = ("env", "secrets", "compose", "instructions", "tools")


def target(ws, what: str, is_global: bool) -> tuple[Path, str]:
    """The file to edit and its template's key."""
    p = ws.project
    if what == "tools":
        if is_global:
            die("tools has no --global: the box does not read your own mise configuration")
        for name in ("mise.toml", ".mise.toml", ".mise/config.toml"):
            if (p.dir / name).is_file():
                return p.dir / name, "tools"
        return p.dir / "mise.toml", "tools"
    if what == "compose":
        if is_global:
            die("compose has no --global: put services of your own in ~/.config/roke/services")
        return p.config / "compose.yaml", "compose"
    base = ws.config if is_global else p.config
    path = {
        "env": ws.global_env if is_global else p.env_file,
        "secrets": base / "secrets.env",
        "instructions": base / "AGENTS.md",
    }[what]
    key = f"{what}-global" if is_global and f"{what}-global" in TEMPLATES else what
    return path, key


def editor(ws) -> list[str]:
    """ROKE_EDITOR, $VISUAL, $EDITOR, then nano or vi."""
    for value in (ws.env.get("ROKE_EDITOR"), os.environ.get("VISUAL"), os.environ.get("EDITOR")):
        if value:
            return shlex.split(value)
    for fallback in ("nano", "vi"):
        if shutil.which(fallback):
            return [fallback]
    die("no editor found: set ROKE_EDITOR in roke.env, or $EDITOR")


def edit(req) -> int:
    what = req.values[0] if req.values else "env"
    ws = Workspace(req).open(guards=not req.is_global, register_project=not req.is_global)
    ws.load_settings()
    path, key = target(ws, what, req.is_global)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(TEMPLATES[key].format(name=ws.project.name))
        info(f"created {path}")
    if what == "secrets":
        path.chmod(0o600)
    code = subprocess.run([*editor(ws), str(path)]).returncode
    if path.suffix == ".env":
        check = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        if check.returncode != 0:
            info(f"WARNING: {path} has a syntax error, and roke will fail until it is fixed:")
            info(check.stderr.strip())
            return 1
    return code
