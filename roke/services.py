"""The services: in the project's configuration, in yours and in roke's
catalog, looked up in that order."""

from pathlib import Path

from roke.paths import entries, first_line, valid_name


class Services:
    def __init__(self, box_dir: Path, user_dir: Path, project_dir: Path | None = None):
        self.catalog_dir = box_dir / "services"
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
        lines += ["", "How to use each one: services/<name>/README.md (index: services/README.md)"]
        return "\n".join(lines)
