"""Pieces shared by the commands."""

from pathlib import Path

from roke import markdown
from roke.paths import BOX_DIR, repo_web_url
from roke.ui import use_color


def link_resolver(source: Path):
    """For a README in roke's repository: its relative links as URLs on
    GitHub. Links that leave the repository, or a README elsewhere (your own
    services), keep only their text."""
    base = repo_web_url()
    if not base or not source.resolve().is_relative_to(BOX_DIR):

        def nothing(target: str) -> None:
            return None

        return nothing

    def resolve(target: str) -> str | None:
        path, _, anchor = target.partition("#")
        full = (source.parent / path).resolve() if path else source.resolve()
        if not full.is_relative_to(BOX_DIR):
            return None
        kind = "tree" if full.is_dir() else "blob"
        url = f"{base}/{kind}/main/{full.relative_to(BOX_DIR)}"
        return f"{url}#{anchor}" if anchor else url

    return resolve


def readme_section(path: Path, ws) -> list[str]:
    """A catalog entry's README, to print after its details: rendered with
    colours when the output allows it (ROKE_COLOR), as plain Markdown
    otherwise."""
    if not path.is_file():
        return []
    text = path.read_text().rstrip()
    if use_color(ws.env.get("ROKE_COLOR")):
        text = markdown.render(text, resolve=link_resolver(path))
    return ["", "─" * 78, "", text]
