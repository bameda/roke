"""roke service: list the services, add them to the project or remove them."""

from roke import settings
from roke.ui import die, info
from roke.workspace import Workspace


def show(req) -> None:
    ws = Workspace(req).open(guards=False)
    ws.load_settings()
    print(ws.services.render(ws.services_text))


def change(req) -> None:
    ws = Workspace(req).open()
    p, names, adding = ws.project, req.values, req.sub == "add"
    # Start from the project's list, or from the global one if it has none.
    source = p.env_file if settings.defines(p.env_file, "ROKE_SERVICES") else ws.global_env
    current = [
        s for s in settings.value_of(source, "ROKE_SERVICES").replace(" ", "").split(",") if s
    ]
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
    info(f"applies from the next start; services: {', '.join(current) or 'none'}")
