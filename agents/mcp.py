#!/usr/bin/env python3
"""Translate roke's MCP servers into an agent's format.

    python3 /opt/roke/agents/mcp.py opencode|claude|codex [FILE]

FILE (by default /run/roke/mcp.json, written by roke) holds the servers
already resolved: {"servers": {NAME: {"type": "local", "command": [...],
"env": {...}} | {"type": "remote", "url": ..., "headers": {...}}}}.
The output is the agent's own format: JSON for OpenCode and Claude Code,
TOML for Codex. With no file, the output is empty ({} or nothing).
"""

import json
import sys


def load(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f).get("servers", {})
    except FileNotFoundError:
        return {}


def opencode(servers: dict) -> str:
    out = {}
    for name, s in servers.items():
        if s["type"] == "local":
            out[name] = {"type": "local", "command": s["command"], "environment": s["env"]}
        else:
            out[name] = {"type": "remote", "url": s["url"], "headers": s["headers"]}
    return json.dumps(out)


def claude(servers: dict) -> str:
    out = {}
    for name, s in servers.items():
        if s["type"] == "local":
            cmd = s["command"]
            out[name] = {"type": "stdio", "command": cmd[0], "args": cmd[1:], "env": s["env"]}
        else:
            out[name] = {"type": "http", "url": s["url"], "headers": s["headers"]}
    return json.dumps(out)


def toml(value) -> str:
    """A string or a list of strings as TOML (JSON's escapes are valid TOML)."""
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(v) for v in value) + "]"
    return json.dumps(value)


def toml_table(values: dict) -> str:
    return "{ " + ", ".join(f"{json.dumps(k)} = {toml(v)}" for k, v in values.items()) + " }"


def codex(servers: dict) -> str:
    lines = []
    for name, s in servers.items():
        lines += ["", f"[mcp_servers.{json.dumps(name)}]"]
        if s["type"] == "local":
            lines += [f"command = {toml(s['command'][0])}", f"args = {toml(s['command'][1:])}"]
            if s["env"]:
                lines.append(f"env = {toml_table(s['env'])}")
        else:
            lines.append(f"url = {toml(s['url'])}")
            if s["headers"]:
                lines.append(f"http_headers = {toml_table(s['headers'])}")
    return "\n".join(lines)


if __name__ == "__main__":
    agent = sys.argv[1]
    servers = load(sys.argv[2] if len(sys.argv) > 2 else "/run/roke/mcp.json")
    print({"opencode": opencode, "claude": claude, "codex": codex}[agent](servers))
