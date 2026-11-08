"""The services: in the project's configuration, in yours and in roke's
catalog, looked up in that order."""

import re
from pathlib import Path

from roke.paths import entries, first_line, valid_name

VERSION_DEFAULT = re.compile(r"\$\{([A-Z][A-Z0-9_]*_VERSION):-([^}]+)\}")


class Services:
    def __init__(self, box_dir: Path, user_dir: Path, project_dir: Path | None = None):
        self.catalog_dir = box_dir / "catalog" / "services"
        self.user_dir = user_dir
        self.project_dir = project_dir

    def dirs(self) -> list[Path]:
        return [d for d in (self.project_dir, self.user_dir, self.catalog_dir) if d]

    def names(self) -> list[str]:
        return sorted({n for d in self.dirs() for n in entries(d, "compose.yaml")})

    def file(self, name: str) -> Path:
        """Where the service is defined: the project's first, then yours,
        then the catalog's."""
        for d in self.dirs():
            candidate = d / name / "compose.yaml"
            if candidate.is_file():
                return candidate
        return self.catalog_dir / name / "compose.yaml"

    def exists(self, name: str) -> bool:
        return valid_name(name) and self.file(name).is_file()

    def origin(self, name: str) -> str | None:
        """ "project", "yours" or None (the catalog's)."""
        path = self.file(name)
        if self.project_dir and path.is_relative_to(self.project_dir):
            return "project"
        if path.is_relative_to(self.user_dir):
            return "yours"
        return None

    def render(self, used_text: str) -> str:
        """The services available, marking those in USED_TEXT (comma-separated)."""
        used = {s.strip() for s in used_text.split(",")}
        lines = ["Services (roke service add NAME; * = used by this project):"]
        for name in self.names():
            desc = first_line(self.file(name))
            origin = self.origin(name)
            if origin:
                desc = f"[{origin}] {desc}"
            lines.append(f"{'*' if name in used else ' '} {name:<12} {desc}")
        return "\n".join(lines)

    def versions(self, name: str) -> dict[str, str]:
        """The service's version variables and their defaults, from its
        compose file: ${POSTGRES_VERSION:-18} gives {"POSTGRES_VERSION": "18"}."""
        path = self.file(name)
        text = path.read_text() if path.is_file() else ""
        return dict(VERSION_DEFAULT.findall(text))

    def keeps_data(self, name: str) -> bool:
        """Whether the service keeps data in volumes, whose format a major
        version may change."""
        path = self.file(name)
        return path.is_file() and re.search(r"^volumes:", path.read_text(), re.M) is not None
