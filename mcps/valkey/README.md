# Valkey (`valkey`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add valkey` (this project) or `roke mcp add valkey --global`.

[Redis's official MCP server](https://github.com/redis/mcp-redis),
connected to the project's [`valkey`](../../services/valkey/README.md)
service, which it starts, since Valkey speaks the same protocol. The
agent can read and write keys of every type, look at the server's state
and search with the query engine where the server supports it.

**Network**: nothing to allow.
