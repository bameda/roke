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

## Terminal

The terminal is the default. From the project directory on your host, run
`roke -a opencode` to start a session or `roke continue -a opencode` to resume
the last one. Omit `-a opencode` if the project already uses OpenCode.

## Web, desktop and editors

Add the optional `--ui` flag to start a server inside the box for the
browser or OpenCode Desktop.

### Browser

```bash
roke -a opencode --ui
```

Leave the command running and open `http://127.0.0.1:4096` in your browser.
Use the password printed by OpenCode. [OpenCode web interface](https://opencode.ai/docs/cli/web/)

### OpenCode Desktop

Run the same `roke -a opencode --ui` command and leave it running. In
OpenCode Desktop on your host, use the server connection controls to connect
to `http://127.0.0.1:4096` with the server password. [Desktop downloads](https://opencode.ai/docs/#desktop)

In either graphical client, choose a previous conversation from the session
list. The server uses port 4096 on host loopback. If another roke project is
using it, run `roke down` in that project to free the port.

### Editors

The terminal commands also work in your editor's integrated terminal. To
run the editor's tools inside the box, start `roke shell -a opencode` and
attach to the running box. [Using a graphical editor](../README.md#using-a-graphical-editor)

## Your configuration

`~/.config/roke/agents/opencode/` is linked into `~/.config/opencode`:
`opencode.jsonc` (model, agents, permissions, MCP servers...), plus
`agents/`, `commands/` and `skills/` if you use them. It is mounted
read-only, so edit it on your host. The terminal client's own file
(`cli.json`) stays in the project's home volume.

## Instructions, MCP servers and Serena

`roke mcp allow NAME` and `roke mcp ask NAME` generate OpenCode 2 permission
rules for that server's tools and resource access, including Serena.
See [Tool approvals](../../mcps/README.md#tool-approvals).

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
  project's lint, typecheck and tests, and [Serena](../../../docs/serena.md)
  covers code navigation.
