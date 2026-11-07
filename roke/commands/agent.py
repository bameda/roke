"""roke agent: list the agents, use one in the project or by default, reset."""

from roke import settings
from roke.ui import die, info
from roke.workspace import Workspace


def show(req) -> None:
    ws = Workspace(req).open(guards=False)
    ws.load_settings()
    ws.choose_agent()
    lines = ["Agents (roke agent use NAME; --global for the default):"]
    for name in ws.agents.names():
        desc = ws.agents.description(name)
        if name not in ws.installed:
            desc += " (not installed)"
        if name == ws.agent:
            desc += f"  <- used here ({ws.agent_source})"
        lines.append(f"  {name:<12} {desc}")
    print("\n".join(lines))


def use(req) -> None:
    ws = Workspace(req).open(guards=not req.is_global)
    name, p = req.values[0], ws.project
    if not ws.agents.exists(name):
        die(f"unknown agent: '{name}' (available: {' '.join(ws.agents.names())})")
    installed = ws.installed_agents()
    if name not in installed:
        info(
            f"note: '{name}' is not in ROKE_AGENTS ({' '.join(installed)}); "
            "add it there and run roke build"
        )
    if req.is_global:
        settings.set_value(ws.global_env, "ROKE_AGENT", name)
        info(f"default agent: {name} (in {ws.global_env})")
        if settings.defines(p.env_file, "ROKE_AGENT"):
            info("note: this project has its own agent; roke agent reset to use the default")
    else:
        settings.set_value(p.env_file, "ROKE_AGENT", name)
        info(f"agent for {p.name}: {name} (in {p.env_file})")


def reset(req) -> None:
    p = Workspace(req).open().project
    settings.drop(p.env_file, "ROKE_AGENT")
    info(f"{p.name} uses the default agent")
