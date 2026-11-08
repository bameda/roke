"""roke network: the mode and the allowed destinations, adding and removing
destinations, and what was blocked."""

import re

from roke import settings
from roke.paths import BOX_DIR
from roke.ui import die, info
from roke.workspace import Workspace

DESTINATION = re.compile(r"(\*\.)?[A-Za-z0-9.-]+(/[0-9]{1,2})?(:[0-9]{1,5})?")


def _sort_key(entry: str) -> str:
    """Alphabetical, with *.example.com next to example.com."""
    return entry.removeprefix("*.").lower()


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
        lines += [f"             {entry}" for entry in sorted(entries, key=_sort_key)] or [
            "             (none)"
        ]
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
    if adding and dest == "host":
        die("allow a port of the host, never the whole host: host:PORT, such as host:4401")
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
    report = compose.call("exec", "-T", "gateway", "roke-gateway", "blocked", capture=True).stdout
    print(annotate(report, expected_blocks(ws)))
    print()
    print(
        "To allow one: roke network add DEST (in this project), or roke network add DEST --global"
    )


def expected_blocks(ws) -> dict[str, str]:
    """Destinations blocked on purpose, and why: those of the tools in the
    image, and those of the project's agent."""
    files = [BOX_DIR / "docker" / "gateway" / "expected.txt"]
    if ws.agent != "none":
        files.append(ws.agents.file(ws.agent, "expected.txt"))
    known = {}
    for path in files:
        if path.is_file():
            for line in path.read_text().splitlines():
                parts = line.split(None, 1)
                if parts and not parts[0].startswith("#"):
                    known[parts[0].lower()] = parts[1].strip() if len(parts) > 1 else ""
    return known


def annotate(report: str, known: dict[str, str]) -> str:
    """The gateway's report, with the reason next to each known domain."""
    lines = []
    for line in report.rstrip("\n").splitlines():
        m = re.match(r"^  (\S+)\s+\d+ lookups?$", line)
        if m:
            domain = m.group(1).lower().rstrip(".")
            reason = next(
                (why for d, why in known.items() if domain == d or domain.endswith("." + d)),
                None,
            )
            if reason is not None:
                line += f"  ({reason})" if reason else "  (blocked on purpose)"
        lines.append(line)
    return "\n".join(lines)
