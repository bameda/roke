# shellcheck shell=bash disable=SC2034  # AGENT_* are read by the entrypoint
# Codex CLI: prepares its configuration on every start. Sourced by the
# entrypoint as the box user; see catalog/agents/README.md for the contract.

AGENT_COMMAND=(codex)
# Arguments that resume the last session (roke continue).
AGENT_CONTINUE=(resume --last)
# The adapter editors talk to (roke acp). It runs the codex installed in the
# image, which reads the same configuration as a normal session.
ACP_COMMAND=(env "CODEX_PATH=$(command -v codex || echo codex)" codex-acp)

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

# System configuration (/etc/codex/config.toml, the lowest layer: yours, in
# ~/.codex/config.toml, wins over every value here), rebuilt on every start.
mcp_args=(codex)
if ((SERENA_ENABLED)); then
  serena_command codex
  mcp_args+=(--serena "${SERENA_CMD[@]}")
fi
{
  # No update checks: the image decides the version.
  echo "check_for_update_on_startup = false"

  # Codex's own sandbox is off, and that is safe here. Do not be alarmed by
  # the name: "danger-full-access" means full access to what Codex can
  # reach, and inside roke's box that is only the project (and the network
  # destinations the project allows). The box is the security boundary: no
  # $HOME, no SSH keys, no other projects, no Docker socket, no Linux
  # capabilities. Codex's sandbox, built on bubblewrap, could not run in the
  # box anyway, since it needs Linux namespaces the box denies on purpose;
  # making it work would mean weakening the box. Codex's approvals are a
  # different setting and do not change: it still asks before running
  # commands, as your approval_policy says.
  # See catalog/agents/codex/README.md and docs/security.md.
  echo 'sandbox_mode = "danger-full-access"'

  # The project is trusted, so Codex does not ask about it on every new
  # home volume: whatever its own settings run, they run in the box too.
  # To treat a project as untrusted, set its trust_level in your config.
  echo
  echo "[projects.$(toml_string "$PWD")]"
  echo 'trust_level = "trusted"'

  # The project's MCP servers, built-in Serena and explicit approval policy.
  python3 /opt/roke/agents/mcp.py "${mcp_args[@]}"
} > /etc/codex/config.toml
