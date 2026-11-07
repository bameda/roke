# Context7 (`context7`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add context7` (this project) or `roke mcp add context7 --global`.

[Context7](https://context7.com/) gives the agent up-to-date documentation
and code examples for the libraries a project uses, instead of what the
model remembers from its training.

**Optional** `CONTEXT7_API_KEY` in `~/.config/roke/secrets.env`, a free key
from [its dashboard](https://context7.com/dashboard) for higher rate limits.
Without it, the header is left out and the server works with the default
limits.

**Network**: allows `mcp.context7.com`.
