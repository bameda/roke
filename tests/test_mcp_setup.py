"""Run the real agent setup scripts in a disposable filesystem, without agents or Docker."""

import json
import os
import subprocess
import sys

import pytest
import tomllib
from conftest import REPO


@pytest.mark.parametrize("agent", ["codex", "claude", "opencode"])
@pytest.mark.parametrize("serena", [False, True])
def test_restarting_agent_regenerates_and_revokes_only_roke_mcp_preferences(
    tmp_path, agent, serena
):
    home = tmp_path / "home"
    config = tmp_path / "personal config"
    runtime = tmp_path / "runtime"
    project = tmp_path / "project with spaces"
    for directory in (home, config, runtime, project):
        directory.mkdir()
    instructions = tmp_path / "instructions.md"
    instructions.write_text("# Project instructions\n")
    personal_name = {
        "codex": "config.toml",
        "claude": "settings.json",
        "opencode": "opencode.jsonc",
    }[agent]
    personal = config / personal_name
    original = {
        "codex": "# personal configuration\n",
        "claude": '{"permissions": {}}\n',
        "opencode": '{"permissions": []}\n',
    }[agent]
    personal.write_text(original)
    personal.chmod(0o400)
    mcp_file = tmp_path / "mcp.json"
    # Redirect filesystem locations only. Both the adapter and setup bodies
    # are the repository's code, and the entrypoint's helpers are sourced verbatim.
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
    args_file = tmp_path / "args"
    script = "set -euo pipefail\nlog() { :; }\n" + helpers
    script += "\nAGENT_ARGS=()\n" + setup
    script += '\nprintf "%s\\0" "${AGENT_ARGS[@]}" > "$ARGS_FILE"\n'
    env = {
        **os.environ,
        "HOME": str(home),
        "AGENT_CONFIG": str(config),
        "AGENT_INSTRUCTIONS": str(instructions),
        "ROKE_RUNTIME": str(runtime),
        "SERENA_ENABLED": "1" if serena else "0",
        "ROKE_SERENA_CODEMODE": "1",
        "ROKE_SERENA_USAGE_REPORTING": "0",
        "ARGS_FILE": str(args_file),
    }
    # Use this interpreter for the setup scripts, which otherwise use python3.
    script = f'python3() {{ "{sys.executable}" "$@"; }}\n' + script
    for mode in ("allow", "ask", None):
        data = {
            "servers": {
                "context7": {"type": "remote", "url": "https://example.invalid/mcp", "headers": {}}
            }
        }
        if mode:
            data["approvals"] = {"context7": mode, "serena": mode}
        mcp_file.write_text(json.dumps(data))
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=project,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert personal.read_text() == original
        args = [arg for arg in args_file.read_text().split("\0") if arg]
        active = ["context7", "serena"] if serena else ["context7"]
        if agent == "codex":
            native = tomllib.loads((tmp_path / "etc/codex/config.toml").read_text())
            assert native["sandbox_mode"] == "danger-full-access"
            assert native["projects"][str(project)]["trust_level"] == "trusted"
            for name in active:
                policy = native["mcp_servers"][name].get("default_tools_approval_mode")
                assert policy == ({"allow": "approve", "ask": "prompt"}.get(mode))
            assert ("serena" in native["mcp_servers"]) == serena
        elif agent == "claude":
            assert args[:2] == ["--mcp-config", str(runtime / "claude-mcp.json")]
            native = json.loads((runtime / "claude-mcp.json").read_text())
            assert ("serena" in native["mcpServers"]) == serena
            if mode:
                assert args[2:] == ["--settings", str(runtime / "claude-permissions.json")]
                policy = json.loads((runtime / "claude-permissions.json").read_text())
                assert policy == {"permissions": {mode: [f"mcp__{name}__*" for name in active]}}
            else:
                assert "--settings" not in args
        else:
            native = json.loads((tmp_path / "etc/opencode/opencode.json").read_text())
            assert native["update"] == "disable"
            assert ("serena" in native["mcp"]["servers"]) == serena
            if serena:
                assert native["mcp"]["servers"]["serena"]["codemode"] is True
            if mode:
                assert all(rule["effect"] == mode for rule in native["permissions"])
                assert len(native["permissions"]) == len(active) * 3
            else:
                assert "permissions" not in native
