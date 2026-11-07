# shellcheck shell=bash disable=SC2034  # AGENT_* are read by the entrypoint
# OpenCode 2: prepares its configuration on every start. Sourced by the
# entrypoint as the box user; see agents/README.md for the contract.

AGENT_COMMAND=(opencode)
# Arguments that resume the last session (roke continue).
AGENT_CONTINUE=(--continue)

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
# shellcheck disable=SC2016  # $schema is a literal key
system_config='{ "$schema": "https://opencode.ai/config.json", "update": "disable" }'
if ((SERENA_ENABLED)); then
  serena_command ide
  codemode=false
  [[ "${ROKE_SERENA_CODEMODE:-0}" == "1" ]] && codemode=true
  system_config="$(jq -n --argjson base "$system_config" --argjson codemode "$codemode" \
    --args '$base + { mcp: { servers: { serena: {
        type: "local",
        command: $ARGS.positional,
        codemode: $codemode,
        timeout: { startup: 120000 }
      } } } }' -- "${SERENA_CMD[@]}")"
fi
# The project's MCP servers (roke mcp); Serena's entry wins a name clash.
mcp_servers="$(python3 /opt/roke/agents/mcp.py opencode)"
system_config="$(jq --argjson extra "$mcp_servers" \
  '.mcp.servers = ($extra + (.mcp.servers // {}))' <<<"$system_config")"
printf '%s\n' "$system_config" > /etc/opencode/opencode.json
