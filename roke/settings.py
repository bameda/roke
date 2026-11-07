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


def value_of(path: Path, key: str) -> str:
    """The value of KEY in a settings file, without quotes; empty if unset."""
    if not path.is_file():
        return ""
    found = ""
    for line in path.read_text().splitlines():
        m = re.fullmatch(rf'{re.escape(key)}="?([^"]*)"?', line)
        if m:
            found = m.group(1)
    return found


def set_value(path: Path, key: str, value: str) -> None:
    """Set KEY=VALUE, replacing its line or its first commented-out line, or
    adding it at the end."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text().splitlines() if path.exists() else []
    new = f"{key}={value}"
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = new
            break
    else:
        for i, line in enumerate(lines):
            if re.match(rf"# *{re.escape(key)}=", line):
                lines[i] = new
                break
        else:
            lines.append(new)
    path.write_text("\n".join(lines) + "\n")


def drop(path: Path, key: str) -> None:
    """Remove every KEY= line from the file."""
    if path.is_file():
        lines = [line for line in path.read_text().splitlines() if not line.startswith(f"{key}=")]
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
