"""The application version, kept separately from agent and service versions."""

from roke.paths import BOX_DIR
from roke.ui import die


def current() -> str:
    """Read the installation's single version source, regardless of the project."""
    try:
        return (BOX_DIR / "VERSION").read_text().strip()
    except OSError:
        die("could not read roke's VERSION file; reinstall roke")
