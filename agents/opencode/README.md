# OpenCode 2 (`opencode`)

[OpenCode 2](https://opencode.ai/v2/docs/), an open-source coding agent that works with many model providers.

## Install and update

Installed from the `@opencode/cli` npm package. The version is
`ROKE_AGENT_VERSIONS="opencode=..."`: an npm version or tag, `latest` by
default. With `latest`, run `roke build --no-cache` to fetch a newer one.

The box disables OpenCode's own updates, since the image decides the
version.

## Log in

Run `/connect` inside OpenCode and follow the steps. The credentials are kept
in the project's home volume (`~/.local/share/opencode/auth.json`), not in your real
`$HOME`, and work for every project. Alternatively, put the provider's API
key in `~/.config/roke/secrets.env`.

## Your configuration

`~/.config/roke/agents/opencode/` is linked into `~/.config/opencode`:
`opencode.jsonc` (model, agents, permissions, MCP servers...), plus
`agents/`, `commands/` and `skills/` if you use them. It is mounted
read-only, so edit it on your host. The terminal client's own file
(`cli.json`) stays in the project's home volume.

## Instructions, MCP servers and Serena

- **Instructions**: the combined instructions (see
  [agents](../README.md#instructions-for-the-agent)) become
  `~/.config/opencode/AGENTS.md`, OpenCode's global instructions file. The
  project's own `AGENTS.md` is read as usual.
- **MCP servers**: those of the project (`roke mcp`) are registered next to
  Serena, in the same place; see [MCP servers](../../mcps/README.md).
- **Serena**: registered as a local MCP server in OpenCode's system
  configuration (`/etc/opencode/opencode.json`, regenerated on every
  start), with Serena's `ide` context. OpenCode 2 groups MCP tools behind its
  Code Mode by default; for Serena it is turned off so its tools show up
  directly. `ROKE_SERENA_CODEMODE=1` reverts that.

## Notes

- OpenCode 2 does not run language servers, so there are no automatic
  diagnostics. The box's instructions ask it to validate changes with the
  project's lint, typecheck and tests, and [Serena](../../docs/serena.md)
  covers code navigation.
- Resume the last session with `roke continue`.
