"""The MCP servers: in the project's configuration, in yours and in roke's
catalog, looked up in that order. Each one is a directory with an mcp.json
that does not depend on the agent:

  description  one line, shown by roke mcp
  command      a local server: the command that starts it, run in the box
  url          a remote server: its URL
  env          variables for a local server
  headers      HTTP headers for a remote server
  requires     variables that must be set (in secrets.env) for it to start
  allow        network destinations it needs
  services     services it needs, started with it (such as its own server)

${VAR} in command, env, url and headers is replaced with the variable's
value from your settings, and ${VAR:-default} with its default when it is
not set, as in compose files; an env entry or header with a ${VAR} that is
not set is left out.
"""

import json
import re
from pathlib import Path
from typing import Any

from roke.paths import entries, valid_name
from roke.ui import die

VARIABLE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


class Mcps:
    def __init__(self, box_dir: Path, user_dir: Path, project_dir: Path | None = None):
        self.catalog_dir = box_dir / "catalog" / "mcps"
        self.user_dir = user_dir
        self.project_dir = project_dir

    def dirs(self) -> list[Path]:
        return [d for d in (self.project_dir, self.user_dir, self.catalog_dir) if d]

    def names(self) -> list[str]:
        return sorted({n for d in self.dirs() for n in entries(d, "mcp.json")})

    def file(self, name: str) -> Path:
        for d in self.dirs():
            candidate = d / name / "mcp.json"
            if candidate.is_file():
                return candidate
        return self.catalog_dir / name / "mcp.json"

    def exists(self, name: str) -> bool:
        return valid_name(name) and self.file(name).is_file()

    def origin(self, name: str) -> str | None:
        path = self.file(name)
        if self.project_dir and path.is_relative_to(self.project_dir):
            return "project"
        if path.is_relative_to(self.user_dir):
            return "yours"
        return None

    def definition(self, name: str) -> dict[str, Any]:
        path = self.file(name)
        try:
            data = json.loads(path.read_text())
        except ValueError as e:
            die(f"{path} is not valid JSON: {e}")
        if not isinstance(data, dict) or ("command" in data) == ("url" in data):
            die(f"{path} must have either a command (local) or a url (remote)")
        return data

    def render(self, used: list[str]) -> str:
        lines = ["MCP servers (roke mcp add NAME; --global for every project; * = used here):"]
        for name in self.names():
            desc = str(self.definition(name).get("description", ""))
            origin = self.origin(name)
            if origin:
                desc = f"[{origin}] {desc}"
            lines.append(f"{'*' if name in used else ' '} {name:<12} {desc}")
        lines += ["", "More about each one: roke mcp show NAME"]
        return "\n".join(lines)


def _substitute(value: str, env: dict[str, str]) -> str | None:
    """VALUE with its ${VAR}s and ${VAR:-default}s replaced, or None if a
    ${VAR} without a default is not set."""
    for match in VARIABLE.finditer(value):
        if not env.get(match.group(1)) and match.group(2) is None:
            return None
    return VARIABLE.sub(lambda m: env.get(m.group(1)) or m.group(2) or "", value)


def resolve(definition: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    """The definition ready for the box: local or remote, with the variables
    replaced and the entries whose variables are not set left out."""
    if "command" in definition:
        command = [_substitute(str(part), env) for part in definition["command"]]
        if any(part is None for part in command):
            return {}
        values = {k: _substitute(str(v), env) for k, v in definition.get("env", {}).items()}
        return {
            "type": "local",
            "command": command,
            "env": {k: v for k, v in values.items() if v is not None},
        }
    url = _substitute(str(definition["url"]), env)
    if url is None:
        return {}
    headers = {k: _substitute(str(v), env) for k, v in definition.get("headers", {}).items()}
    return {
        "type": "remote",
        "url": url,
        "headers": {k: v for k, v in headers.items() if v is not None},
    }
