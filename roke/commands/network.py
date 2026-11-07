"""roke network: the mode and the allowed destinations, adding and removing
destinations, and what was blocked."""

import re

from roke import settings
from roke.ui import die, info
from roke.workspace import Workspace

DESTINATION = re.compile(r"(\*\.)?[A-Za-z0-9.-]+(/[0-9]{1,2})?(:[0-9]{1,5})?")


def render_network(ws) -> str:
    """The allowed destinations by layer, as roke settings and roke network show them."""
    if ws.network == "open":
        lines = [
            "Allowed destinations: everything (open mode). "
            "The lists below apply in restricted mode."
        ]
    else:
        lines = ["Allowed destinations (restricted mode), by layer:"]
    for label, source, entries in ws.allow_layers():
        lines.append(f"  {label:<10} {source}")
        lines += [f"             {entry}" for entry in entries] or ["             (none)"]
    return "\n".join(lines)


def show(req) -> None:
    ws = Workspace(req).open(guards=False)
    ws.load_all()
    print(f"Network mode: {ws.network} ({ws.network_source})\n")
    print(render_network(ws))


def change(req) -> None:
    ws = Workspace(req).open(guards=not req.is_global)
    dest, adding = req.values[0], req.sub == "add"
    if req.is_global:
        path, where = ws.global_env, "every project"
    else:
        path, where = ws.project.env_file, ws.project.name
    if adding and not DESTINATION.fullmatch(dest):
        die(f"not a destination: '{dest}' (use a domain, IP or CIDR, with an optional :port)")
    current = settings.value_of(path, "ROKE_NETWORK_ALLOW").split()
    if adding:
        if dest in current:
            info(f"{dest} is already allowed in {where}")
            return
        current.append(dest)
        verb = "allowed"
    else:
        if dest not in current:
            die(f"{dest} is not allowed in {where} (see roke network)")
        current.remove(dest)
        verb = "no longer allowed"
    settings.set_or_drop(path, "ROKE_NETWORK_ALLOW", f'"{" ".join(current)}"' if current else "")
    info(f"{verb} in {where}: {dest} (from the next start; in {path})")


def blocked(req) -> None:
    ws = Workspace(req).open(docker=True)
    ws.load_all()
    compose = ws.prepare_compose(all_services=True)
    if not compose.running("gateway"):
        die(
            "the project is not running; start it with roke, reproduce the problem, "
            "then run roke network blocked"
        )
    compose.call("exec", "-T", "gateway", "roke-gateway", "blocked")
    print()
    print(
        "To allow one: roke network add DEST (in this project), or roke network add DEST --global"
    )
