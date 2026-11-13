"""What each agent's setup.sh says about roke acp, run for real in a disposable filesystem."""

import json
import os
import subprocess
import sys

import pytest
from conftest import REPO


def run_setup(tmp_path, agent, acp, mcp=None):
    """Run the agent's setup.sh like the entrypoint does; returns ACP_COMMAND and
    the runtime directory (whose name has spaces and a quote, to be quoted right)."""
    home, config, project = tmp_path / "home", tmp_path / "config", tmp_path / "project"
    runtime = tmp_path / "run time 'x'"
    fakebin = tmp_path / "bin"
    for directory in (home, config, project, runtime, fakebin):
        directory.mkdir()
    for tool in ("codex", "claude"):
        (fakebin / tool).write_text('#!/bin/bash\nprintf "%s\\0" "$@" > "$CLAUDE_LOG"\n')
        (fakebin / tool).chmod(0o755)
    instructions = tmp_path / "instructions.md"
    instructions.write_text("# Instructions\n")
    mcp_file = tmp_path / "mcp.json"
    mcp_file.write_text(json.dumps(mcp or {"servers": {}}))
    adapter = tmp_path / "mcp.py"
    adapter.write_text(
        (REPO / "catalog/agents/mcp.py")
        .read_text()
        .replace('default="/run/roke/mcp.json"', f"default={str(mcp_file)!r}")
    )
    setup = (REPO / "catalog/agents" / agent / "setup.sh").read_text()
    setup = setup.replace("/opt/roke/agents/mcp.py", '"' + str(adapter) + '"')
    for path in ("/etc/codex", "/etc/claude-code", "/etc/opencode"):
        target = tmp_path / path.removeprefix("/")
        target.mkdir(parents=True)
        setup = setup.replace(path, str(target))
    entrypoint = (REPO / "docker/entrypoint.sh").read_text()
    helpers = "\n".join(
        f"{name}() {{" + entrypoint.split(f"{name}() {{", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
        for name in ("roke_link_config", "serena_command")
    )
    out = tmp_path / "acp-command"
    script = f'python3() {{ "{sys.executable}" "$@"; }}\nset -euo pipefail\nlog() {{ :; }}\n'
    script += helpers + "\nAGENT_ARGS=()\nACP_COMMAND=()\n" + setup
    script += '\nprintf "%s\\0" "${ACP_COMMAND[@]}" > "$ACP_FILE"\n'
    env = {
        **os.environ,
        "PATH": f"{fakebin}:{os.environ['PATH']}",
        "HOME": str(home),
        "AGENT_CONFIG": str(config),
        "AGENT_INSTRUCTIONS": str(instructions),
        "ROKE_RUNTIME": str(runtime),
        "SERENA_ENABLED": "0",
        "ROKE_ACP": "1" if acp else "0",
        "ACP_FILE": str(out),
    }
    result = subprocess.run(
        ["bash", "-c", script], cwd=project, env=env, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    command = [part for part in out.read_text().split("\0") if part]
    return command, runtime, fakebin, env


@pytest.mark.parametrize("acp", [False, True])
def test_opencode_speaks_acp_itself(tmp_path, acp):
    command, *_ = run_setup(tmp_path, "opencode", acp)
    assert command == ["opencode", "acp"]


@pytest.mark.parametrize("acp", [False, True])
def test_codex_adapter_runs_the_codex_of_the_image(tmp_path, acp):
    command, _, fakebin, _ = run_setup(tmp_path, "codex", acp)
    assert command == ["env", f"CODEX_PATH={fakebin / 'codex'}", "codex-acp"]


def test_claude_adapter_starts_claude_through_a_wrapper(tmp_path):
    command, runtime, *_ = run_setup(tmp_path, "claude", acp=True)
    wrapper = runtime / "claude-acp"
    assert command == ["env", f"CLAUDE_CODE_EXECUTABLE={wrapper}", "claude-agent-acp"]
    assert wrapper.stat().st_mode & 0o777 == 0o700


def test_claude_without_acp_makes_no_wrapper(tmp_path):
    command, runtime, *_ = run_setup(tmp_path, "claude", acp=False)
    assert command == ["claude-agent-acp"] and not (runtime / "claude-acp").exists()


def call_wrapper(runtime, env, tmp_path, *args):
    """Run the wrapper, with a claude that records its arguments; returns them."""
    log = tmp_path / "claude-args"
    log.unlink(missing_ok=True)
    result = subprocess.run(
        [str(runtime / "claude-acp"), *args],
        env={**env, "CLAUDE_LOG": str(log)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return [part for part in log.read_text().split("\0") if part]


def test_the_wrapper_gives_sessions_the_mcp_servers_and_approvals_but_not_auth_calls(tmp_path):
    mcp = {
        "servers": {
            "context7": {"type": "remote", "url": "https://example.invalid/mcp", "headers": {}}
        },
        "approvals": {"context7": "allow"},
    }
    _, runtime, _, env = run_setup(tmp_path, "claude", acp=True, mcp=mcp)
    extra = [
        "--mcp-config",
        str(runtime / "claude-mcp.json"),
        "--settings",
        str(runtime / "claude-permissions.json"),
    ]
    session = ["--output-format", "stream-json", "--permission-mode=auto"]
    assert call_wrapper(runtime, env, tmp_path, *session) == extra + session
    # The adapter's own calls take no such options.
    assert call_wrapper(runtime, env, tmp_path, "auth", "status", "--json") == [
        "auth",
        "status",
        "--json",
    ]
    assert json.loads((runtime / "claude-mcp.json").read_text())["mcpServers"]["context7"]


def test_the_wrapper_without_servers_passes_everything_through(tmp_path):
    _, runtime, _, env = run_setup(tmp_path, "claude", acp=True)
    assert call_wrapper(runtime, env, tmp_path, "--output-format", "stream-json") == [
        "--output-format",
        "stream-json",
    ]
    assert call_wrapper(runtime, env, tmp_path, "auth", "status") == ["auth", "status"]
