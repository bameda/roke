"""The coding agents: one directory per agent in agents/, with an
install.sh and a setup.sh."""

from pathlib import Path

from roke.paths import entries, first_line, valid_name

DEFAULT_INSTALLED = "claude codex opencode"


class Agents:
    def __init__(self, box_dir: Path):
        self.dir = box_dir / "agents"

    def names(self) -> list[str]:
        return entries(self.dir, "setup.sh")

    def exists(self, name: str) -> bool:
        return valid_name(name) and (self.dir / name / "setup.sh").is_file()

    def file(self, name: str, filename: str) -> Path:
        return self.dir / name / filename

    def description(self, name: str) -> str:
        return first_line(self.file(name, "README.md"))
