"""roke service: list the services, add them to the project or remove them."""

import re

from roke import docker, settings, urls
from roke.paths import first_line
from roke.ui import die, info, page
from roke.workspace import Workspace


def project_services(ws) -> list[str]:
    """The project's services: its own list, or the global one."""
    p = ws.project
    source = p.env_file if settings.defines(p.env_file, "ROKE_SERVICES") else ws.global_env
    return [s for s in settings.value_of(source, "ROKE_SERVICES").replace(" ", "").split(",") if s]


def show(req) -> None:
    ws = Workspace(req).open(guards=False)
    ws.load_settings()
    print(ws.services.render(ws.services_text))
    rows = []
    for name in project_services(ws):
        if not ws.services.exists(name):
            continue
        for var, default in ws.services.versions(name).items():
            current = ws.current_version(var, default)
            pinned = settings.value_of(ws.project.env_file, var)
            if not pinned:
                state = f"not pinned yet: gets {current}"
            elif pinned == current:
                state = "up to date"
            else:
                state = f"{current} available"
            rows.append(f"  {name:<12} {var}={pinned or '-':<12} {state}")
    if rows:
        print("\nVersions pinned in this project (roke service upgrade [NAME...]):")
        print("\n".join(rows))
    print("\nMore about each one: roke service show NAME")


def _major(version: str) -> str:
    """The first number of a version: "v3.16.0" and "3" give "3"."""
    digits = re.match(r"v?(\d+)", version)
    return digits.group(1) if digits else version


def upgrade(req) -> None:
    ws = Workspace(req).open()
    p, used = ws.project, project_services(ws)
    names = req.values or used
    for name in names:
        if not ws.services.exists(name):
            die(f"unknown service: '{name}' (see roke service)")
        if name not in used:
            die(f"{name} is not in {p.name}; add it with roke service add {name}")
    if not names:
        info(f"{p.name} has no services")
        return
    changed = False
    for name in names:
        for var, default in ws.services.versions(name).items():
            target = ws.current_version(var, default)
            pinned = settings.value_of(p.env_file, var)
            if pinned == target:
                continue
            if (
                pinned
                and _major(pinned) != _major(target)
                and ws.services.keeps_data(name)
                and not req.major
            ):
                info(
                    f"{name}: {pinned} → {target} is a major version and {name} keeps data, "
                    "whose format may change. Back up, see "
                    f"services/{name}/README.md, then: roke service upgrade {name} --major"
                )
                continue
            settings.set_value(p.env_file, var, target)
            info(f"{name}: {var} {pinned or '(not pinned)'} → {target}")
            changed = True
    info("applies from the next start of the project" if changed else f"{p.name} is up to date")


def change(req) -> None:
    ws = Workspace(req).open()
    p, names, adding = ws.project, req.values, req.sub == "add"
    current = project_services(ws)
    if adding:
        for name in names:
            if not ws.services.exists(name):
                die(f"unknown service: '{name}' (see roke service); nothing was changed")
    for name in names:
        if adding and name in current:
            info(f"{name} is already in {p.name}")
        elif adding:
            current.append(name)
            info(f"added to {p.name}: {name}")
        elif name not in current:
            info(f"{name} is not in {p.name}")
        else:
            current.remove(name)
            info(f"removed from {p.name}: {name} (its data is kept until roke purge)")
    settings.set_or_drop(p.env_file, "ROKE_SERVICES", ",".join(current))
    if adding:
        ws.pin_versions(names)
    info(f"applies from the next start; services: {', '.join(current) or 'none'}")


def show_one(req) -> None:
    """A service: what applies to it in this project, then its README."""
    ws = Workspace(req).open(guards=False)
    ws.load_all()
    name = req.values[0]
    if not ws.services.exists(name):
        die(f"unknown service: '{name}' (see roke service)")
    path = ws.services.file(name)
    used = name in ws.selected
    lines = [
        f"{name}: {first_line(path)}",
        "",
        "In this project: " + ("used" if used else f"not used (roke service add {name})"),
    ]
    for var, default in ws.services.versions(name).items():
        pinned = settings.value_of(ws.project.env_file, var)
        current = ws.current_version(var, default)  # what a new project would get
        if not pinned:
            lines.append(f"  {var}={current} (not pinned yet)")
        elif pinned == current:
            lines.append(f"  {var}={pinned} (pinned)")
        else:
            lines.append(f"  {var}={pinned} (pinned; {current} available)")
    if docker.available():
        compose = ws.prepare_compose()
        own = compose.config([ws.base_files[0], path])
        base = compose.config([ws.base_files[0]])
        addresses, variables = urls.service_info(name, own, base, own)
        lines.append("  inside the box: " + " · ".join(addresses))
        lines += [
            f"  from your browser: {url}" for label, url, _ in urls.host_urls(own) if label == name
        ]
        if variables:
            lines.append("  variables in the box:")
            lines += [f"    {k}={v}" for k, v in variables.items()]
    else:
        lines.append("  (without Docker, its addresses and variables cannot be shown)")
    page("\n".join(lines + readme_section(path.parent / "README.md")))


def readme_section(path) -> list[str]:
    """A catalog entry's README, to print after its details."""
    if not path.is_file():
        return []
    return ["", "─" * 78, "", path.read_text().rstrip()]
