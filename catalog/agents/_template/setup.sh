# shellcheck shell=bash disable=SC2034  # AGENT_* are read by the entrypoint
# Prepares the agent on every start. Sourced by the entrypoint as the box's
# user; see catalog/agents/README.md for the variables and helpers available.

AGENT_COMMAND=(myagent)
# Arguments that resume the last session (roke continue), if the agent can.
AGENT_CONTINUE=(--continue)

# Link your configuration where the agent reads it:
# roke_link_config "$AGENT_CONFIG" "$HOME/.config/myagent"

# Put the combined instructions where the agent reads them:
# cp "$AGENT_INSTRUCTIONS" "$HOME/.config/myagent/AGENTS.md"

# Register Serena when enabled, with the Serena context that suits the agent:
# if ((SERENA_ENABLED)); then
#   serena_command agent
#   ... write an MCP configuration using "${SERENA_CMD[@]}" ...
#   AGENT_ARGS=(--mcp-config "$ROKE_RUNTIME/mcp.json")
# fi
