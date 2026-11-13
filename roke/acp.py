"""roke acp: the Agent Client Protocol between an editor and the agent in the box.

An editor starts `roke acp` as the agent and speaks ACP with it on standard
input and output: JSON-RPC messages, one per line. roke runs the agent's
adapter in the box and passes the messages along, with two exceptions that
keep the box the boundary:

- ACP lets the editor offer the agent its own file and terminal methods
  (fs/* and terminal/*), which would run on the host, outside the box. roke
  tells the agent the editor offers none, and refuses any such request, so the
  agent works in the box with its own tools.
- The agent only sees the project, so a session for a folder outside it is
  refused, with a message that says what to open instead.
"""

import contextlib
import json
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

# Methods the agent may call on the editor that would run outside the box.
HOST_METHODS = ("fs/", "terminal/")
# Parameters of a session that name folders.
FOLDERS = ("cwd", "additionalDirectories")


def _error(message: dict, code: int, text: str) -> bytes:
    reply = {"jsonrpc": "2.0", "id": message["id"], "error": {"code": code, "message": text}}
    return json.dumps(reply, ensure_ascii=False).encode()


def _outside(params: dict, project: Path) -> list[str]:
    """The folders in a session's parameters that are not in the project."""
    paths: list[Any] = []  # whatever the editor sent: checked below
    for key in FOLDERS:
        value = params.get(key)
        paths += [value] if isinstance(value, str) else value if isinstance(value, list) else []
    outside = []
    for path in paths:
        try:
            resolved = Path(path).resolve()
            inside = Path(path).is_absolute() and (project in (resolved, *resolved.parents))
        except (OSError, ValueError, TypeError):
            inside = False
        if not inside:
            outside.append(str(path))
    return outside


def from_editor(line: bytes, project: Path) -> tuple[bytes | None, bytes | None]:
    """A message from the editor: what to pass to the agent, and what to answer
    the editor instead; None for nothing."""
    try:
        message = json.loads(line)
    except ValueError:
        return line, None
    if not isinstance(message, dict) or not isinstance(message.get("method"), str):
        return line, None
    method, params = message["method"], message.get("params")
    if not isinstance(params, dict):
        return line, None
    if method == "initialize":
        capabilities = params.get("clientCapabilities")
        if isinstance(capabilities, dict):
            for key in ("fs", "terminal"):
                capabilities.pop(key, None)
            return json.dumps(message, ensure_ascii=False).encode(), None
    elif method.startswith("session/"):
        outside = _outside(params, project)
        if outside:
            text = (
                f"roke: {', '.join(outside)} is outside the project {project}, the only "
                "folder the agent can see: open the project's folder in the editor, or "
                "start roke acp with -C DIR"
            )
            return None, _error(message, -32602, text) if "id" in message else None
    return line, None


def from_agent(line: bytes) -> tuple[bytes | None, bytes | None]:
    """A message from the agent: what to pass to the editor, and what to answer
    the agent instead."""
    try:
        message = json.loads(line)
    except ValueError:
        return line, None
    method = message.get("method") if isinstance(message, dict) else None
    if isinstance(method, str) and method.startswith(HOST_METHODS):
        if "id" in message:
            text = (
                "roke does not let the agent use the editor's files or terminal: "
                "it works in the box"
            )
            return None, _error(message, -32601, text)
        return None, None
    return line, None


def serve(command: list[str], env: dict[str, str], project: Path) -> int:
    """Run COMMAND, the box's session, and pass the messages between it and the
    editor until either ends. Returns its exit code."""
    child = subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert child.stdin and child.stdout
    to_agent, from_agent_stream = child.stdin, child.stdout
    locks = {"agent": threading.Lock(), "editor": threading.Lock()}

    def send(stream, name: str, data: bytes) -> None:
        with locks[name]:
            try:
                stream.write(data + b"\n")
                stream.flush()
            except (OSError, ValueError):
                pass  # the other side is gone; the loops below end

    def editor_to_agent() -> None:
        for line in sys.stdin.buffer:
            forward, reply = from_editor(line.rstrip(b"\r\n"), project)
            if forward is not None:
                send(to_agent, "agent", forward)
            if reply is not None:
                send(sys.stdout.buffer, "editor", reply)
        with contextlib.suppress(OSError):
            to_agent.close()  # the editor closed its side: the agent ends

    def agent_to_editor() -> None:
        for line in from_agent_stream:
            forward, reply = from_agent(line.rstrip(b"\r\n"))
            if forward is not None:
                send(sys.stdout.buffer, "editor", forward)
            if reply is not None:
                send(to_agent, "agent", reply)

    signal.signal(signal.SIGTERM, lambda *_: child.terminate())
    threading.Thread(target=editor_to_agent, daemon=True).start()
    forwarder = threading.Thread(target=agent_to_editor)
    forwarder.start()
    try:
        forwarder.join()
        code = child.wait()
    finally:
        if child.poll() is None:
            child.terminate()
    return code if code >= 0 else 128 - code
