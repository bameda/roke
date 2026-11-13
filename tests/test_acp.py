"""roke acp: an editor talks to the agent in the box, and cannot use the host through it."""

import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import FAKES, REPO, ROKE

sys.path.insert(0, str(REPO))
from roke.acp import from_agent, from_editor  # noqa: E402

PROJECT = Path("/home/dev/shop")


def message(method, params=None, **extra):
    return json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params or {}, **extra}
    ).encode()


def parsed(line):
    return json.loads(line) if line is not None else None


# --- the filters ---------------------------------------------------------------------
def test_initialize_loses_the_editors_files_and_terminal():
    caps = {"fs": {"readTextFile": True, "writeTextFile": True}, "terminal": True, "plan": {}}
    line = message("initialize", {"protocolVersion": 1, "clientCapabilities": caps}, id=0)
    forward, reply = from_editor(line, PROJECT)
    assert reply is None
    assert parsed(forward)["params"]["clientCapabilities"] == {"plan": {}}
    assert parsed(forward)["params"]["protocolVersion"] == 1


@pytest.mark.parametrize("line", [b"not json", b"[1, 2]", b'"text"', message("x"), b"{}"])
def test_other_messages_pass_unchanged(line):
    assert from_editor(line, PROJECT) == (line, None)


def test_initialize_without_capabilities_passes_unchanged():
    line = message("initialize", {"protocolVersion": 1}, id=0)
    assert from_editor(line, PROJECT) == (line, None)


@pytest.mark.parametrize("method", ["fs/read_text_file", "fs/write_text_file", "terminal/create"])
def test_the_agent_cannot_use_the_editors_files_or_terminal(method):
    forward, reply = from_agent(message(method, {"path": "/x"}, id=7))
    assert forward is None
    error = parsed(reply)
    assert error["id"] == 7 and error["error"]["code"] == -32601
    assert "does not let the agent use the editor's files or terminal" in error["error"]["message"]


def test_notifications_for_the_host_are_dropped_silently():
    assert from_agent(message("terminal/output", {})) == (None, None)


@pytest.mark.parametrize(
    "line",
    [
        message("session/update", {"update": 1}),
        message("session/request_permission", id=3),
        b"junk",
    ],
)
def test_what_the_agent_says_to_the_editor_passes(line):
    assert from_agent(line) == (line, None)


def test_sessions_must_be_in_the_project(tmp_path):
    project = tmp_path / "shop"
    (project / "src").mkdir(parents=True)
    ok = message("session/new", {"cwd": str(project / "src"), "mcpServers": []}, id=1)
    assert from_editor(ok, project) == (ok, None)
    for cwd in (str(tmp_path), str(tmp_path / "shop-other"), "relative/dir", "/"):
        forward, reply = from_editor(message("session/new", {"cwd": cwd}, id=2), project)
        assert forward is None
        error = parsed(reply)["error"]
        assert error["code"] == -32602 and "outside the project" in error["message"]
        assert str(project) in error["message"] and "-C DIR" in error["message"]


def test_a_symlink_out_of_the_project_is_outside(tmp_path):
    project = tmp_path / "shop"
    project.mkdir()
    (project / "out").symlink_to(tmp_path)
    forward, reply = from_editor(
        message("session/new", {"cwd": str(project / "out")}, id=1), project
    )
    assert forward is None and "outside the project" in parsed(reply)["error"]["message"]


def test_additional_directories_are_checked_too(tmp_path):
    project = tmp_path / "shop"
    project.mkdir()
    params = {
        "cwd": str(project),
        "additionalDirectories": [str(project), str(tmp_path / "elsewhere")],
    }
    forward, reply = from_editor(message("session/new", params, id=1), project)
    assert forward is None and "elsewhere" in parsed(reply)["error"]["message"]


def test_a_refused_notification_gets_no_answer(tmp_path):
    forward, reply = from_editor(message("session/load", {"cwd": "/"}), tmp_path)
    assert forward is None and reply is None


# --- the whole command ---------------------------------------------------------------
class Editor:
    """What came back from a session: the protocol on standard output, roke's
    own messages on standard error, and what the agent received."""

    def __init__(self, out, err, code, agent_log, docker_calls):
        self.out, self.err, self.code = out, err, code
        self.agent_log, self.docker_calls = agent_log, docker_calls

    def run_args(self):
        return next(c["args"] for c in self.docker_calls if "run" in c["args"])


def converse(env, shop, lines, *args, wait_for=None, **extra):
    """Run `roke acp` like an editor: send LINES, wait until WAIT_FOR is true of
    the output so far (or the agent ends), then close the agent's input."""
    log = env.tmp / "agent.log"
    run_env = env.environment(
        {"FAKE_RUN_SCRIPT": str(FAKES / "acp_agent.py"), "FAKE_AGENT_LOG": str(log), **extra}
    )
    if env.log.exists():
        env.log.unlink()
    proc = subprocess.Popen(
        [str(ROKE), "acp", *args],
        cwd=shop,
        env=run_env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for line in lines:
        proc.stdin.write(line + "\n")
    proc.stdin.flush()
    # Read the descriptor itself: a buffered readline would hide lines that
    # arrive together from select, and from communicate afterwards.
    out, pending, deadline = [], b"", time.time() + 20
    while time.time() < deadline and proc.poll() is None:
        if wait_for and wait_for(out):
            break
        ready, _, _ = select.select([proc.stdout], [], [], 0.2)
        if ready:
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                break
            *complete, pending = (pending + chunk).split(b"\n")
            out += [json.loads(line) for line in complete if line]
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "editor/done"}) + "\n")
    proc.stdin.flush()
    rest, err = proc.communicate(timeout=20)  # which closes the agent's input
    out += [json.loads(line) for line in (pending.decode() + rest).splitlines() if line]
    agent_log = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    calls = (
        [json.loads(line) for line in env.log.read_text().splitlines()] if env.log.exists() else []
    )
    return Editor(out, err, proc.returncode, agent_log, calls)


def updated(out):
    return any(m.get("method") == "session/update" for m in out)


def initialize():
    caps = {"fs": {"readTextFile": True, "writeTextFile": True}, "terminal": True}
    return message("initialize", {"protocolVersion": 1, "clientCapabilities": caps}, id=0).decode()


def test_the_session_runs_in_the_box_with_the_protocol_on_standard_output(env):
    shop = env.project()
    new = message("session/new", {"cwd": str(shop.resolve()), "mcpServers": []}, id=1).decode()
    r = converse(env, shop, [initialize(), new], wait_for=lambda out: len(out) >= 3)
    assert r.code == 0, r.err
    run = r.run_args()
    assert "-T" in run and "ROKE_ACP=1" in run and "--rm" in run
    assert (
        run.index("--progress") < run.index("run") and run[run.index("--progress") + 1] == "quiet"
    )
    assert run[-1] == "box"  # no command: the box starts the agent's adapter
    assert [m.get("id") for m in r.out if "result" in m] == [0, 1]
    assert {"jsonrpc": "2.0", "method": "session/update", "params": {"update": "hello"}} in r.out
    assert "project:" in r.err  # roke's own messages are on standard error


def test_the_agent_never_reaches_the_host_through_the_editor(env):
    r = converse(env, env.project(), [initialize()], wait_for=updated)
    assert not [m for m in r.out if str(m.get("method", "")).startswith(("fs/", "terminal/"))]
    first = r.agent_log[0]
    assert first["method"] == "initialize"
    assert "fs" not in first["params"]["clientCapabilities"]
    assert "terminal" not in first["params"]["clientCapabilities"]
    answers = {m["id"]: m["error"]["code"] for m in r.agent_log if "error" in m}
    assert answers == {100: -32601, 101: -32601}


def test_a_folder_outside_the_project_is_refused_before_the_agent(env):
    shop, elsewhere = env.project(), env.project("elsewhere")
    new = message("session/new", {"cwd": str(elsewhere), "mcpServers": []}, id=1).decode()
    r = converse(
        env, shop, [initialize(), new], wait_for=lambda out: any(m.get("id") == 1 for m in out)
    )
    refusal = next(m for m in r.out if m.get("id") == 1)
    assert refusal["error"]["code"] == -32602
    assert "outside the project" in refusal["error"]["message"]
    assert not [m for m in r.agent_log if m.get("method") == "session/new"]


def test_the_exit_code_is_the_agents(env):
    r = converse(env, env.project(), [initialize()], wait_for=updated, FAKE_AGENT_EXIT="3")
    assert r.code == 3


@pytest.mark.parametrize("agent", ["claude", "codex", "opencode"])
def test_every_agent_is_served_the_same_way(env, agent):
    r = converse(env, env.project(), [initialize()], "-a", agent, wait_for=updated)
    assert r.code == 0, r.err
    assert f"agent: {agent}" in r.err
    assert next(c for c in r.docker_calls if "run" in c["args"])["env"]["ROKE_AGENT"] == agent


def test_acp_takes_the_run_options_and_no_command(env):
    shop = env.project()
    for args, message_ in [
        (("acp", "extra"), "unexpected argument"),
        (("acp", "--ui"), "unknown option"),
    ]:
        r = env.roke(*args, cwd=shop)
        assert r.code != 0 and message_ in r.err


def test_acp_does_not_start_while_another_agent_would_cut_a_session_off(env):
    shop = env.project()
    r = env.roke(
        "acp",
        "-a",
        "codex",
        cwd=shop,
        env={
            "FAKE_SESSIONS": "claude",
            "FAKE_RUNNING_HASHES": "gateway=h1",
            "FAKE_CONFIG_HASHES": "gateway=h2",
        },
        input="",
    )
    assert r.code != 0 and "ROKE_PARALLEL_AGENTS=claude,codex" in r.err
    assert not r.compose_calls("run")
