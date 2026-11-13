# shellcheck shell=bash disable=SC2034  # AGENT_* are read by the entrypoint
# OpenCode 2: prepares its configuration on every start. Sourced by the
# entrypoint as the box user; see catalog/agents/README.md for the contract.

AGENT_COMMAND=(opencode)
# Arguments that resume the last session (roke continue).
AGENT_CONTINUE=(--continue)
# OpenCode speaks the Agent Client Protocol itself (roke acp).
ACP_COMMAND=(opencode acp)

# Your configuration (opencode.jsonc, agents/, commands/, skills/...) is
# linked into ~/.config/opencode, where the TUI can still write its own
# files, such as cli.json. The global AGENTS.md is the instructions file
# OpenCode 2 reliably loads.
cfg="$HOME/.config/opencode"
roke_link_config "$AGENT_CONFIG" "$cfg"
cp "$AGENT_INSTRUCTIONS" "$cfg/AGENTS.md"

# System configuration (/etc/opencode, highest precedence), rebuilt on every
# start: updates off, since the image decides the version, the project's MCP
# servers (roke mcp), and Serena when enabled.
mcp_args=(opencode)
if ((SERENA_ENABLED)); then
  serena_command ide
  mcp_args+=(--serena "${SERENA_CMD[@]}")
fi
# shellcheck disable=SC2016  # $schema is a literal key
system_config="$(python3 /opt/roke/agents/mcp.py "${mcp_args[@]}" \
  | jq '. + { "$schema": "https://opencode.ai/config.json", "update": "disable" }')"
printf '%s\n' "$system_config" > /etc/opencode/opencode.json
