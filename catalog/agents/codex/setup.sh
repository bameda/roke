# shellcheck shell=bash disable=SC2034  # AGENT_* are read by the entrypoint
# Codex CLI: prepares its configuration on every start. Sourced by the
# entrypoint as the box user; see catalog/agents/README.md for the contract.

AGENT_COMMAND=(codex)
# Arguments that resume the last session (roke continue).
AGENT_CONTINUE=(resume --last)

# Your configuration (config.toml, prompts/, skills/...) is linked into
# ~/.codex, where Codex keeps its own state too (auth.json, sessions...), in
# the project's home volume. ~/.codex/AGENTS.md holds Codex's global
# instructions: the combined instructions go there.
roke_link_config "$AGENT_CONFIG" "$HOME/.codex"
cp "$AGENT_INSTRUCTIONS" "$HOME/.codex/AGENTS.md"

# toml_string VALUE: VALUE as a TOML basic string.
toml_string() {
  local v="${1//\\/\\\\}"
  printf '"%s"' "${v//\"/\\\"}"
}

# System configuration (/etc/codex/config.toml, the lowest layer, under
# yours), rebuilt on every start: no update checks, since the image decides
# the version, and Serena when enabled.
{
  echo "check_for_update_on_startup = false"
  if ((SERENA_ENABLED)); then
    serena_command codex
    echo
    echo "[mcp_servers.serena]"
    echo "command = $(toml_string "${SERENA_CMD[0]}")"
    printf 'args = ['
    sep=""
    for arg in "${SERENA_CMD[@]:1}"; do printf '%s%s' "$sep" "$(toml_string "$arg")"; sep=", "; done
    echo "]"
    echo "startup_timeout_sec = 120"
  fi
  # The project's MCP servers (roke mcp).
  python3 /opt/roke/agents/mcp.py codex
} > /etc/codex/config.toml
