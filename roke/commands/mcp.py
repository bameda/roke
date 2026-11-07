"""roke mcp: list the MCP servers, give them to the agent or take them away,
in the project or in every project."""

from roke import settings
from roke.ui import die, info
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
