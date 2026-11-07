"""Where things are: roke's repository, your configuration directory, and
small helpers to read the catalog directories."""

import os
from pathlib import Path

BOX_DIR = Path(__file__).resolve().parent.parent


def config_dir() -> Path:
    """Your configuration directory: $ROKE_CONFIG_DIR, or ~/.config/roke."""
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(os.environ.get("ROKE_CONFIG_DIR") or Path(xdg) / "roke")


def first_line(path: Path) -> str:
    """A file's first line without its leading "# ": its description."""
    try:
        line = path.read_text().splitlines()[0]
    except (OSError, IndexError):
        return ""
    return line[1:].lstrip() if line.startswith("#") else ""


def entries(directory: Path, marker: str) -> list[str]:
    """The subdirectories of DIRECTORY holding MARKER, except those starting
    with "_" (templates)."""
    if not directory.is_dir():
        return []
    return sorted(
        d.name for d in directory.iterdir() if (d / marker).is_file() and not d.name.startswith("_")
    )


def valid_name(name: str) -> bool:
    return bool(name) and not name.startswith("_") and "/" not in name
