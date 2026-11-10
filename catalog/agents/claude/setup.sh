# shellcheck shell=bash disable=SC2034  # AGENT_* are read by the entrypoint
# Claude Code: prepares its configuration on every start. Sourced by the
# entrypoint as the box user; see catalog/agents/README.md for the contract.

AGENT_COMMAND=(claude)
# Arguments that resume the last session (roke continue).
AGENT_CONTINUE=(--continue)

# The image decides the version.
export DISABLE_UPDATES=1

# Your configuration (settings.json, CLAUDE.md, agents/, commands/,
# skills/...) is linked into ~/.claude. Claude Code keeps its own state
# (login, sessions, auto memory) there and in ~/.claude.json, in the box's
# volume.
roke_link_config "$AGENT_CONFIG" "$HOME/.claude"

# The box's instructions go to the managed CLAUDE.md, which Claude Code loads
# before your CLAUDE.md and the project's, and which cannot be excluded.
cp "$AGENT_INSTRUCTIONS" /etc/claude-code/CLAUDE.md

# The project's MCP servers (roke mcp) and Serena, through a per-start MCP
# configuration passed on the command line; MCP servers you add to Claude
# Code yourself keep working alongside them.
mcp_args=(claude)
if ((SERENA_ENABLED)); then
  serena_command claude-code
  mcp_args+=(--serena "${SERENA_CMD[@]}")
fi
mcp_servers="$(python3 /opt/roke/agents/mcp.py "${mcp_args[@]}")"
if [[ "$mcp_servers" != "{}" ]]; then
  mcp_config="$ROKE_RUNTIME/claude-mcp.json"
  jq '{ mcpServers: . }' <<<"$mcp_servers" > "$mcp_config"
  AGENT_ARGS=(--mcp-config "$mcp_config")
fi
permissions="$(python3 /opt/roke/agents/mcp.py --permissions "${mcp_args[@]}")"
if [[ "$permissions" != "{}" ]]; then
  permissions_file="$ROKE_RUNTIME/claude-permissions.json"
  printf '%s\n' "$permissions" > "$permissions_file"
  AGENT_ARGS+=(--settings "$permissions_file")
fi
