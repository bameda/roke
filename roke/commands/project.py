"""List local project identities, including paths that have disappeared."""

from pathlib import Path

from roke.paths import config_dir
from roke.project import registered
from roke.ui import die


def _projects():
    config = config_dir()
    if not config.is_dir():
        die(f"configuration directory not found: {config} (create it with: roke init)")
    return config.resolve(), registered(config.resolve())


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


def show_one(req) -> None:
    config, projects = _projects()
    name = req.values[0]
    if name not in projects:
        die(f"unknown project ID: '{name}' (see roke project)")
    entry = projects[name]
    state = "found" if Path(entry["path"]).is_dir() else "missing"
    print(
        f"ID        {name}\nPath      {entry['path']} ({state})\n"
        f"Settings  {config / 'projects' / name}\nCompose   {entry['compose_name']}"
    )
