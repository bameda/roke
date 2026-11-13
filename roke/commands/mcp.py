"""roke mcp: list the MCP servers, give them to the agent or take them away,
in the project or in every project."""

from roke import mcp_permissions, settings
from roke.commands.common import readme_section
from roke.ui import die, info, page
from roke.workspace import Workspace, split_list


def show(req) -> None:
    ws = Workspace(req).open(guards=False)
    ws.load_settings()
    print(
        ws.mcps.render(split_list(ws.global_mcps) + split_list(ws.project_mcps), serena=ws.serena)
    )


def validate(ws, names: list[str], policy: bool = False) -> None:
    for name in names:
        if name != "serena" and not ws.mcps.exists(name):
            die(f"unknown MCP server: '{name}' (see roke mcp); nothing was changed")
        if policy and not mcp_permissions.valid_name(name):
            die("MCP approval names must contain only letters, digits, hyphens and underscores")
        if ws.mcps.exists(name):
            ws.mcps.definition(name)


def save_approvals(path, policies: dict[str, str]) -> None:
    # Remove duplicate assignments too: a later old allow must never shadow ask.
    settings.drop(path, mcp_permissions.SETTING)
    settings.set_or_drop(
        path, mcp_permissions.SETTING, mcp_permissions.serialize(policies) if policies else ""
    )


def approval(req) -> None:
    ws = Workspace(req).open(guards=not req.is_global, register_project=not req.is_global)
    ws.load_settings()
    validate(ws, req.values, policy=True)
    path = ws.global_env if req.is_global else ws.project.env_file
    where = "every project" if req.is_global else ws.project.name
    policies = mcp_permissions.parse(settings.value_of(path, mcp_permissions.SETTING))
    if req.sub == "reset":
        for name in req.values:
            if policies.pop(name, None) is None:
                info(f"{name} has no tool approval set in {where}")
        save_approvals(path, policies)
        info(f"MCP tool approvals back to the agent's default: {', '.join(req.values)}")
        return
    enabled = split_list(ws.global_mcps) + split_list(ws.project_mcps) + ["serena"] * ws.serena
    for name in req.values:
        policies[name] = req.sub
        if not req.is_global and name not in enabled:
            info(
                f"note: {name} is not enabled here (roke mcp add {name}); "
                "the approval applies once it is"
            )
    save_approvals(path, policies)
    info(f"MCP tool approvals: {', '.join(req.values)} = {req.sub}; applies from the next start")


def change(req) -> None:
    ws = Workspace(req).open(guards=not req.is_global, register_project=not req.is_global)
    adding = req.sub == "add"
    if req.is_global:
        path, where = ws.global_env, "every project"
    else:
        path, where = ws.project.env_file, ws.project.name
    current = split_list(settings.value_of(path, "ROKE_MCPS"))
    if adding:
        validate(ws, req.values, policy=bool(req.mcp_approval))
    ws.load_settings()
    policies = mcp_permissions.parse(settings.value_of(path, mcp_permissions.SETTING))
    for name in req.values:
        if req.mcp_approval:
            policies[name] = req.mcp_approval
        elif not adding and (req.is_global or name not in split_list(ws.global_mcps)):
            policies.pop(name, None)
        if name == "serena" and not ws.mcps.exists(name):
            settings.set_value(path, "ROKE_SERENA", "1" if adding else "0")
            info(f"{'enabled' if adding else 'disabled'} in {where}: serena")
            continue
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
    save_approvals(path, policies)
    info("applies from the next start")


def show_one(req) -> None:
    """An MCP server: its definition and whether its secrets are set, then its
    README. Variables are shown as written, never their values."""
    ws = Workspace(req).open(guards=False)
    ws.load_settings()
    name = req.values[0]
    if name == "serena" and not ws.mcps.exists(name):
        used = "enabled" if ws.serena else "disabled (roke mcp add serena)"
        page(
            "\n".join(
                [
                    "serena: Built-in semantic tools",
                    "",
                    f"In this project: {used}",
                    f"  tool approvals: {mcp_permissions.describe(ws, name)}",
                    *readme_section(ws.mcps.catalog_dir.parent.parent / "docs" / "serena.md", ws),
                ]
            )
        )
        return
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
    lines.append(f"  tool approvals: {mcp_permissions.describe(ws, name)}")
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
