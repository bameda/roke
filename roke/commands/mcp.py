"""roke mcp: list the MCP servers, give them to the agent or take them away,
in the project or in every project."""

from roke import settings
from roke.commands.common import readme_section
from roke.ui import die, info, page
from roke.workspace import Workspace, split_list


def show(req) -> None:
    ws = Workspace(req).open(guards=False)
    ws.load_settings()
    print(ws.mcps.render(split_list(ws.global_mcps) + split_list(ws.project_mcps)))


def change(req) -> None:
    ws = Workspace(req).open(guards=not req.is_global)
    adding = req.sub == "add"
    if req.is_global:
        path, where = ws.global_env, "every project"
    else:
        path, where = ws.project.env_file, ws.project.name
    current = split_list(settings.value_of(path, "ROKE_MCPS"))
    if adding:
        for name in req.values:
            if not ws.mcps.exists(name):
                die(f"unknown MCP server: '{name}' (see roke mcp); nothing was changed")
    ws.load_settings()
    for name in req.values:
        if adding and name in current:
            info(f"{name} is already in {where}")
        elif adding:
            current.append(name)
            info(f"added to {where}: {name}")
            requires = ws.mcps.definition(name).get("requires", [])
            missing = [v for v in requires if not ws.env.get(v)]
            if missing:
                info(
                    f"note: {name} needs {', '.join(missing)} in secrets.env; "
                    "until then it is left out"
                )
        elif name in current:
            current.remove(name)
            info(f"removed from {where}: {name}")
        elif not req.is_global and name in split_list(ws.global_mcps):
            info(f"{name} is enabled in every project: roke mcp rm {name} --global")
        else:
            info(f"{name} is not in {where}")
    settings.set_or_drop(path, "ROKE_MCPS", ",".join(current))
    info("applies from the next start")


def show_one(req) -> None:
    """An MCP server: its definition and whether its secrets are set, then its
    README. Variables are shown as written, never their values."""
    ws = Workspace(req).open(guards=False)
    ws.load_settings()
    name = req.values[0]
    if not ws.mcps.exists(name):
        die(f"unknown MCP server: '{name}' (see roke mcp)")
    d = ws.mcps.definition(name)
    if name in split_list(ws.project_mcps):
        used = f"used (roke mcp rm {name} to remove it)"
    elif name in split_list(ws.global_mcps):
        used = f"used, in every project (roke mcp rm {name} --global)"
    else:
        used = f"not used (roke mcp add {name})"
    lines = [f"{name}: {d.get('description', '')}", "", f"In this project: {used}"]
    if "command" in d:
        lines.append("  local: " + " ".join(d["command"]))
    else:
        lines.append(f"  remote: {d['url']}")
    for var in d.get("requires", []):
        lines.append(f"  needs {var}: {'set' if ws.env.get(var) else 'NOT SET (in secrets.env)'}")
    if d.get("services"):
        lines.append("  starts: " + ", ".join(d["services"]))
    if d.get("allow"):
        lines.append("  allows: " + ", ".join(d["allow"]))
    page("\n".join(lines + readme_section(ws.mcps.file(name).parent / "README.md", ws)))
