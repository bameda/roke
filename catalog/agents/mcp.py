#!/usr/bin/env python3
"""Translate roke's MCP servers into an agent's format.

    python3 /opt/roke/agents/mcp.py opencode|claude|codex [FILE] [--serena COMMAND...]

FILE (by default /run/roke/mcp.json, written by roke) holds the servers
already resolved: {"servers": {NAME: {"type": "local", "command": [...],
"env": {...}} | {"type": "remote", "url": ..., "headers": {...}}}}.
Optional approvals map server names to allow or ask. Serena is added from
the entrypoint's command, sharing the catalog's permission translation.
OpenCode receives a config fragment, Claude receives its MCP server map
(--permissions emits its settings fragment), and Codex receives TOML.
"""

import argparse
import json
import os
import re
import sys


def load(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def opencode(servers: dict, approvals: dict) -> str:
    out = {}
    for name, s in servers.items():
        if s["type"] == "local":
            out[name] = {"type": "local", "command": s["command"], "environment": s["env"]}
        else:
            out[name] = {"type": "remote", "url": s["url"], "headers": s["headers"]}
        if s.get("serena"):
            out[name]["codemode"] = os.environ.get("ROKE_SERENA_CODEMODE", "0") == "1"
            out[name]["timeout"] = {"startup": 120000}
    config = {"mcp": {"servers": out}}
    rules = []
    for name, mode in approvals.items():
        # OpenCode's normalizedName preserves hyphens.
        normalized = re.sub(r"[^A-Za-z0-9_-]", "_", name)
        builtins = (
            "external_directory",
            "experimental_image_generate",
            "opencode_list_mcp_resources",
            "opencode_read_mcp_resource",
        )
        if any(action.startswith(normalized + "_") for action in builtins):
            raise ValueError(
                f"ambiguous OpenCode MCP approval name {name} (built-in action); rename it"
            )
        for other in servers:
            other_normalized = re.sub(r"[^A-Za-z0-9_-]", "_", other)
            if name != other and (
                normalized == other_normalized
                or normalized.startswith(other_normalized + "_")
                or other_normalized.startswith(normalized + "_")
            ):
                raise ValueError(
                    f"ambiguous OpenCode MCP approval names: {name}, {other}; rename one"
                )
        rules += [
            {"action": normalized + "_*", "resource": "*", "effect": mode},
            {"action": "opencode_list_mcp_resources", "resource": name, "effect": mode},
            {"action": "opencode_read_mcp_resource", "resource": name + ":*", "effect": mode},
        ]
    if rules:
        config["permissions"] = rules
    return json.dumps(config)


def claude(servers: dict) -> str:
    out = {}
    for name, s in servers.items():
        if s["type"] == "local":
            cmd = s["command"]
            out[name] = {"type": "stdio", "command": cmd[0], "args": cmd[1:], "env": s["env"]}
        else:
            out[name] = {"type": "http", "url": s["url"], "headers": s["headers"]}
    return json.dumps(out)


def claude_permissions(servers: dict, approvals: dict) -> str:
    rules: dict[str, list[str]] = {}
    for name, mode in approvals.items():
        for other in servers:
            if name != other and (name.startswith(other + "__") or other.startswith(name + "__")):
                raise ValueError(
                    f"ambiguous Claude MCP approval names: {name}, {other}; rename one"
                )
        rules.setdefault(mode, []).append(f"mcp__{name}__*")
    return json.dumps({"permissions": rules} if rules else {})


def toml(value) -> str:
    """A string or a list of strings as TOML (JSON's escapes are valid TOML)."""
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(v) for v in value) + "]"
    return json.dumps(value)


def toml_table(values: dict) -> str:
    return "{ " + ", ".join(f"{json.dumps(k)} = {toml(v)}" for k, v in values.items()) + " }"


def codex(servers: dict, approvals: dict) -> str:
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
        if name in approvals:
            mode = "approve" if approvals[name] == "allow" else "prompt"
            lines.append(f"default_tools_approval_mode = {toml(mode)}")
        if s.get("serena"):
            lines.append("startup_timeout_sec = 120")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("agent", choices=("opencode", "claude", "codex"))
    parser.add_argument("file", nargs="?", default="/run/roke/mcp.json")
    parser.add_argument(
        "--permissions", action="store_true", help="Claude's tool approval settings"
    )
    parser.add_argument("--serena", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        data = load(args.file)
        servers = data.get("servers", {})
        if args.serena:
            if "serena" in servers and "serena" in data.get("approvals", {}):
                raise ValueError(
                    "a custom MCP named serena conflicts with built-in Serena; rename it"
                )
            servers["serena"] = {"type": "local", "command": args.serena, "env": {}, "serena": True}
        approvals = {
            name: mode for name, mode in data.get("approvals", {}).items() if name in servers
        }
        if any(
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name) or mode not in ("allow", "ask")
            for name, mode in approvals.items()
        ):
            raise ValueError("invalid MCP tool approval preference")
        if args.agent == "claude":
            print(claude_permissions(servers, approvals) if args.permissions else claude(servers))
        elif args.agent == "codex":
            print(codex(servers, approvals))
        else:
            print(opencode(servers, approvals))
    except (OSError, ValueError) as error:
        sys.exit(f"roke MCP configuration: {error}")
