# Penpot (`penpot`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add penpot`.

[Penpot's hosted MCP server](https://help.penpot.app/mcp/) lets the agent
read and change your Penpot designs: inspect a design to write its code,
extract its tokens and styles, or create and edit screens from code. It
acts on the page you have open in Penpot, in your browser.

**Needs** `PENPOT_MCP_KEY` in `~/.config/roke/secrets.env`:

1. In Penpot, go to **Your account → Integrations → MCP Server**, turn it on
   and generate an MCP key. It is shown only once.
2. Add it to `secrets.env`: `PENPOT_MCP_KEY=...`.

**Using it**: in Penpot, open a design file and connect it with
**File → MCP Server → Connect**. The agent then works on the page you have
in focus. Penpot's [help](https://help.penpot.app/mcp/#agents-can-edit-designs)
recommends starting with read-only requests, since the agent can change
the design.

**Self-hosted Penpot**: set `PENPOT_URL` to your instance (for example
`PENPOT_URL=https://penpot.example.com` in `roke.env`), and allow its
domain with `roke network add penpot.example.com --global`.

**Network**: allows `design.penpot.app`.
