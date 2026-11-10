"""Persistent MCP approval preferences, separate from enabling a server."""

import re

from roke.ui import die

SETTING = "ROKE_MCP_APPROVALS"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def valid_name(name: str) -> bool:
    return NAME.fullmatch(name) is not None


def parse(text: str) -> dict[str, str]:
    policies = {}
    for entry in text.replace(",", " ").split():
        name, separator, mode = entry.partition("=")
        if not separator or not valid_name(name) or mode not in ("allow", "ask"):
            die(f"{SETTING} entries must be NAME=allow or NAME=ask")
        policies[name] = mode
    return policies


def serialize(policies: dict[str, str]) -> str:
    return '"' + ",".join(f"{name}={mode}" for name, mode in sorted(policies.items())) + '"'


def describe(ws, name: str) -> str:
    if name in ws.project_mcp_approvals:
        return f"{ws.project_mcp_approvals[name]} (this project)"
    if name in ws.global_mcp_approvals:
        return f"{ws.global_mcp_approvals[name]} (global)"
    return "agent default"
