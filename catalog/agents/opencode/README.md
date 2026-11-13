# OpenCode 2 (`opencode`)

[OpenCode 2](https://opencode.ai/v2/docs/), an open-source coding agent that works with many model providers.

## Install and update

Installed from the `@opencode/cli` npm package. The version is
`ROKE_AGENT_VERSIONS="opencode=..."`: an npm version or tag, `latest` by
default.

## Log in

Run `/connect` inside OpenCode and follow the steps. The credentials are kept
in the project's home volume (`~/.local/share/opencode/auth.json`), not in your real
`$HOME`, and persist for later sessions of this project. A separate project
has its own home and login. Alternatively, put the provider's API
key in `~/.config/roke/secrets.env`.

## Web and editors

### Web interface and OpenCode Desktop

`--ui` starts a server in the box instead of the terminal client:

```bash
roke -a opencode --ui
```

Leave the command running and open `http://127.0.0.1:4096` in your browser,
with the password OpenCode prints. [OpenCode web interface](https://opencode.ai/docs/cli/web/)

OpenCode Desktop connects to the same address and password, in its server
connection controls. [Desktop downloads](https://opencode.ai/docs/#desktop)
In either client, choose a previous conversation from the session list. The
server uses port 4096 on host loopback: if another roke project is using it,
run `roke down` in that project to free the port.

### Editors

OpenCode speaks the Agent Client Protocol itself: `roke acp -a opencode`
serves it to an editor, with the same configuration as a terminal session.
See [editors](../../../docs/editors.md).

## Your configuration

`~/.config/roke/agents/opencode/` is linked into `~/.config/opencode`:
`opencode.jsonc` (model, agents, permissions, MCP servers...), plus
`agents/`, `commands/` and `skills/` if you use them. It is mounted
read-only, so edit it on your host. The terminal client's own file
(`cli.json`) stays in the project's home volume.

How roke gives OpenCode the instructions, MCP servers and approvals is in
[how roke configures each agent](../README.md#how-roke-configures-each-agent).

## Notes

- OpenCode 2 groups MCP tools behind its Code Mode by default; for Serena it is
  turned off so its tools show up directly. `ROKE_SERENA_CODEMODE=1` reverts that.
  `roke mcp allow` and `ask` generate permission rules for each server's tools
  and resources, including Serena. See
  [tool approvals](../../mcps/README.md#tool-approvals).
- OpenCode 2 does not run language servers, so there are no automatic
  diagnostics. The box's instructions ask it to validate changes with the
  project's lint, typecheck and tests, and [Serena](../../../docs/serena.md)
  covers code navigation.
