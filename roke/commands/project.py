"""The projects registered on this machine: list them, inspect one, give one
another ID, or forget one."""

from pathlib import Path

from roke import docker
from roke import project as registry
from roke.commands.settings import summary
from roke.paths import config_dir
from roke.ui import Fail, die, info
from roke.workspace import Workspace


def _projects():
    config = config_dir()
    if not config.is_dir():
        die(f"configuration directory not found: {config} (create it with: roke init)")
    return config.resolve(), registry.registered(config.resolve())


def _known(projects: dict, name: str) -> dict:
    if name not in projects:
        die(f"unknown project ID: '{name}' (see roke project)")
    return projects[name]


def _stopped(entry: dict, name: str) -> None:
    """Refuse while the project's containers run: they mount its settings."""
    if not docker.available():
        return
    try:
        running = docker.running_containers(entry["compose_name"])
    except Fail:
        return  # Docker cannot be asked, so nothing can be running
    if running:
        die(f"{name} is running: stop it first, with roke down in {entry['path']}")


def show(req) -> None:
    _, projects = _projects()
    if not projects:
        print("No projects registered on this machine. Start a session to register one.")
        return
    width = max(len(name) for name in projects)
    print("Projects registered on this machine:")
    for name, entry in sorted(projects.items()):
        state = "found" if Path(entry["path"]).is_dir() else "missing"
        print(f"  {name:<{width}}  {state:<7}  {entry['path']}")
    print("\nFor a moved project: start it from the new directory with roke --id ID.")
    print("More about one: roke project show ID")


def show_one(req) -> None:
    """A registered project, from any directory: what roke settings shows for
    the current one."""
    ws = Workspace(req).open(guards=False, registered_id=req.values[0])
    ws.load_all()
    print(summary(ws))


def rename(req) -> None:
    config, projects = _projects()
    old, new = req.values
    _stopped(_known(projects, old), old)
    entry = registry.rename(config, old, new)
    info(f"renamed {old} to {new}; its settings moved to {config / 'projects' / new}")
    info(f"its containers and data are kept ({entry['compose_name']})")


def rm(req) -> None:
    config, projects = _projects()
    name = req.values[0]
    _stopped(_known(projects, name), name)
    entry = registry.unregister(config, name)
    info(f"forgot {name} ({entry['path']})")
    info(
        f"kept: its settings in {config / 'projects' / name}, and in Docker its "
        f"containers and data ({entry['compose_name']})"
    )
    info(
        f"to delete them, remove that directory and run: "
        f"docker compose -p {entry['compose_name']} down --volumes"
    )
