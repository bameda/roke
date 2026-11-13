"""The project roke works on, and the guards against mounting too much."""

import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from roke.ui import die

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
INVALID_ID = (
    "invalid project ID: use letters, digits, dots, underscores or hyphens; "
    "start with a letter or digit"
)


@dataclass
class Project:
    dir: Path  # the project's directory, resolved
    name: str  # stable project ID
    config: Path  # ~/.config/roke/projects/<id>/
    compose_name: str

    @property
    def env_file(self) -> Path:
        return self.config / "project.env"

    @property
    def services_dir(self) -> Path:
        return self.config / "services"


def registered(config: Path) -> dict[str, dict[str, str]]:
    """Read the machine-local identities, without registering a working directory."""
    registry = config / ".local" / "projects.json"
    if not registry.exists():
        return {}
    try:
        records = json.loads(registry.read_text())
        if not isinstance(records, dict):
            raise ValueError("expected an object")
        for name, entry in records.items():
            if not ID.fullmatch(name):
                raise ValueError("invalid project ID")
            if not isinstance(entry, dict) or set(entry) != {"path", "compose_name"}:
                raise ValueError("expected path and compose_name")
            if not isinstance(entry["path"], str) or not Path(entry["path"]).is_absolute():
                raise ValueError("expected an absolute path")
            if not isinstance(entry["compose_name"], str) or not re.fullmatch(
                r"roke-[a-z0-9][a-z0-9_-]*", entry["compose_name"]
            ):
                raise ValueError("invalid Compose name")
        for field in ("path", "compose_name"):
            if len({entry[field] for entry in records.values()}) != len(records):
                raise ValueError(f"duplicate {field}")
        return records
    except (OSError, ValueError) as exc:
        die(f"cannot read project registry {registry}: {exc}")


def by_id(config: Path, project_id: str) -> Project:
    """Look up an identity for inspection, even when its directory is missing."""
    projects = registered(config)
    if project_id not in projects:
        die(f"unknown project ID: '{project_id}' (see roke project)")
    entry = projects[project_id]
    return Project(
        Path(entry["path"]), project_id, config / "projects" / project_id, entry["compose_name"]
    )


def resolve(directory: str, config_dir: Path, project_id: str = "", lookup: bool = True) -> Project:
    path = Path(directory)
    if not path.is_dir():
        die(f"directory does not exist: {directory}")
    path = path.resolve()
    records = registered(config_dir) if lookup else {}
    if project_id and not ID.fullmatch(project_id):
        die(INVALID_ID)
    bound = next((name for name, entry in records.items() if entry["path"] == str(path)), "")
    if bound and project_id and bound != project_id:
        die(
            f"{path} is already registered as {bound}; omit --id or use --id {bound}, "
            f"or rename it: roke project rename {bound} {project_id}"
        )
    name = project_id or bound or path.name
    if name in records:
        entry = records[name]
        if entry["path"] != str(path) and (not project_id or Path(entry["path"]).exists()):
            die(
                f"project ID '{name}' is registered at {entry['path']}; "
                "choose another ID with: roke --id ID. "
                "After moving a directory, use --id with its existing ID "
                "once the old path is gone"
            )
        return Project(path, name, config_dir / "projects" / name, entry["compose_name"])
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", path.name.lower())).strip("-")
    digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    config = config_dir / "projects" / name
    legacy = config_dir / "projects" / path.name
    # An explicit ID can adopt existing settings, but never copy another
    # registered project's settings or secrets merely because names match.
    if name != path.name and not config.exists() and path.name not in records and legacy.is_dir():
        config = legacy
    return Project(
        dir=path,
        name=name,
        config=config,
        compose_name=f"roke-{slug or 'project'}-{digest}",
    )


def register(project: Project, config: Path, project_id: str = "") -> Project:
    """Adopt legacy names and serialize registrations without exposing state to the box."""
    try:
        return _register(project, config, project_id)
    except OSError as exc:
        die(f"cannot register project {project.name}: {exc}")


def _register(project: Project, config: Path, project_id: str) -> Project:
    state = config / ".local"
    state.mkdir(mode=0o700, exist_ok=True)
    if not state.resolve().is_relative_to(config):
        die("the local project registry must live inside the roke configuration")
    ignore = state / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n")
    with (state / "projects.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        project = resolve(str(project.dir), config, project_id)
        if not ID.fullmatch(project.name):
            die(
                "choose a project ID with roke --id ID "
                "(letters, digits, dots, underscores or hyphens)"
            )
        records = registered(config)
        target = config / "projects" / project.name
        if project.config != target:
            shutil.copytree(project.config, target)
            project.config = target
        entry = {"path": str(project.dir), "compose_name": project.compose_name}
        if records.get(project.name) == entry:
            return project
        records[project.name] = entry
        _save(state, records)
    return project


def _save(state: Path, records: dict[str, dict[str, str]]) -> None:
    """Replace the registry atomically; only you can read it."""
    with tempfile.NamedTemporaryFile(mode="w", dir=state, delete=False) as tmp:
        try:
            json.dump(records, tmp, indent=2)
            tmp.write("\n")
            tmp.close()
            os.replace(tmp.name, state / "projects.json")
        finally:
            Path(tmp.name).unlink(missing_ok=True)


@contextmanager
def _locked(config: Path) -> Iterator[Path]:
    """Hold the registry's lock, yielding its directory."""
    state = config / ".local"
    state.mkdir(mode=0o700, exist_ok=True)
    with (state / "projects.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield state


def rename(config: Path, old: str, new: str) -> dict[str, str]:
    """Give the registered project OLD the ID NEW. Its settings move to the new
    ID's directory; its Compose name, so its containers and data, stay."""
    if not ID.fullmatch(new):
        die(INVALID_ID)
    if old == new:
        die(f"the project is already named {old}")
    with _locked(config) as state:
        records = registered(config)
        if old not in records:
            die(f"unknown project ID: '{old}' (see roke project)")
        if new in records:
            die(f"project ID '{new}' is already registered at {records[new]['path']}")
        source, target = config / "projects" / old, config / "projects" / new
        if target.exists():
            die(f"{target} already exists: choose another ID, or move that directory away")
        try:
            if source.exists():
                source.rename(target)
            records[new] = records.pop(old)
            _save(state, records)
        except OSError as exc:
            if target.exists() and not source.exists():
                target.rename(source)
            die(f"cannot rename project {old}: {exc}")
        return records[new]


def unregister(config: Path, project_id: str) -> dict[str, str]:
    """Forget the registration of PROJECT_ID, and nothing else."""
    with _locked(config) as state:
        records = registered(config)
        if project_id not in records:
            die(f"unknown project ID: '{project_id}' (see roke project)")
        entry = records.pop(project_id)
        try:
            _save(state, records)
        except OSError as exc:
            die(f"cannot forget project {project_id}: {exc}")
        return entry


def _inside(path: Path, parent: Path) -> bool:
    return path == parent or path.is_relative_to(parent)


def check_guards(project: Path, home: Path, box_dir: Path, config_dir: Path) -> None:
    """Refuse project directories that would expose more than a project."""
    if project == Path("/"):
        die("refusing to mount the whole /")
    if project == home:
        die("refusing to mount your whole $HOME")
    if _inside(home, project):
        die(f"{project} contains your $HOME; pick a specific project directory")
    if _inside(box_dir, project):
        die("the project contains the roke repo; the agent could modify its own sandbox")
    if _inside(project, box_dir):
        die("the project is inside the roke repo")
    if _inside(config_dir, project):
        die("the project contains your roke configuration; the agent could change its own settings")
    if _inside(project, config_dir):
        die("the project is inside your roke configuration directory")
