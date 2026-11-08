"""Settings files (roke.env, project.env, secrets.env): reading and editing.

The files are read by bash, as if sourced with `set -a`, so they behave
exactly like shell files: quotes, comments and variable references work.
"""

import re
import subprocess
from pathlib import Path

_DUMP = 'set -a; for f in "$@"; do [ -f "$f" ] && . "$f"; done; env -0'


def load(files: list[Path], base: dict[str, str]) -> dict[str, str]:
    """The environment BASE after sourcing FILES in order."""
    out = subprocess.run(
        ["bash", "-c", _DUMP, "roke", *map(str, files)], env=base, capture_output=True, check=True
    ).stdout
    env = {}
    for item in out.decode(errors="replace").split("\0"):
        if "=" in item:
            key, value = item.split("=", 1)
            env[key] = value
    for key in ("_", "SHLVL", "PWD", "OLDPWD"):
        if key in base:
            env[key] = base[key]
        else:
            env.pop(key, None)
    return env


def defines(path: Path, key: str) -> bool:
    """Whether the file sets KEY (on a line of its own)."""
    return path.is_file() and any(
        line.startswith(f"{key}=") for line in path.read_text().splitlines()
    )


def _spans(lines: list[str], key: str) -> list[tuple[int, int]]:
    """The (first, last) line of each KEY= assignment: a value in double
    quotes may go on over several lines."""
    spans, i = [], 0
    while i < len(lines):
        if lines[i].startswith(f"{key}="):
            rest = lines[i][len(key) + 1 :]
            end = i
            if rest.startswith('"') and rest.count('"') == 1:
                while end + 1 < len(lines) and '"' not in lines[end + 1]:
                    end += 1
                end = min(end + 1, len(lines) - 1)
            spans.append((i, end))
            i = end
        i += 1
    return spans


def value_of(path: Path, key: str) -> str:
    """The value of KEY in a settings file, without quotes, over several
    lines if it has them; empty if unset. The last assignment wins."""
    if not path.is_file():
        return ""
    lines = path.read_text().splitlines()
    spans = _spans(lines, key)
    if not spans:
        return ""
    first, last = spans[-1]
    text = "\n".join(lines[first : last + 1])[len(key) + 1 :]
    if text.startswith('"') and text.endswith('"') and len(text) > 1:
        text = text[1:-1]
    return text.strip("\n") if "\n" in text else text


def set_value(path: Path, key: str, value: str) -> None:
    """Set KEY=VALUE, replacing its assignment or its first commented-out
    line, or adding it at the end. VALUE may hold several lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text().splitlines() if path.exists() else []
    new = f"{key}={value}".split("\n")
    spans = _spans(lines, key)
    if spans:
        first, last = spans[0]
        lines[first : last + 1] = new
    else:
        for i, line in enumerate(lines):
            if re.match(rf"# *{re.escape(key)}=", line):
                lines[i : i + 1] = new
                break
        else:
            lines += new
    path.write_text("\n".join(lines) + "\n")


def drop(path: Path, key: str) -> None:
    """Remove every KEY= assignment from the file."""
    if path.is_file():
        lines = path.read_text().splitlines()
        for first, last in reversed(_spans(lines, key)):
            del lines[first : last + 1]
        path.write_text("\n".join(lines) + ("\n" if lines else ""))


def set_or_drop(path: Path, key: str, value: str) -> None:
    if value:
        set_value(path, key, value)
    else:
        drop(path, key)


def entries(text: str) -> list[str]:
    """The whitespace-separated entries of TEXT, ignoring # comments."""
    return [w for line in text.splitlines() for w in line.split("#", 1)[0].split()]


def file_entries(path: Path) -> list[str]:
    return entries(path.read_text()) if path.is_file() else []


def noted_entries(text: str) -> list[tuple[str, str]]:
    """The entries of TEXT, each with its note: the # comment on its line,
    or else the comment lines just above its group (a blank line ends a
    group)."""
    out: list[tuple[str, str]] = []
    block: list[str] = []
    group = ""
    for line in text.splitlines():
        body, hash_, comment = line.partition("#")
        words, comment = body.split(), comment.strip()
        if not words:
            if hash_:
                block.append(comment)
                group = " ".join(block)
            else:
                block, group = [], ""
            continue
        block = []
        note = comment if hash_ and comment else group
        out += [(word, note) for word in words]
    return out


def file_noted_entries(path: Path) -> list[tuple[str, str]]:
    return noted_entries(path.read_text()) if path.is_file() else []
