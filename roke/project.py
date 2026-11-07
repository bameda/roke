"""The project roke works on, and the guards against mounting too much."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from roke.ui import die


@dataclass
class Project:
    dir: Path  # the project's directory, resolved
    name: str  # its directory's name
    config: Path  # ~/.config/roke/projects/<name>/
    compose_name: str

    @property
    def env_file(self) -> Path:
        return self.config / "project.env"

    @property
    def services_dir(self) -> Path:
        return self.config / "services"


def resolve(directory: str, config_dir: Path) -> Project:
    path = Path(directory)
    if not path.is_dir():
        die(f"directory does not exist: {directory}")
    path = path.resolve()
    name = path.name
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", name.lower())).strip("-")
    digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    return Project(
        dir=path,
        name=name,
        config=config_dir / "projects" / name,
        compose_name=f"roke-{slug or 'project'}-{digest}",
    )


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
