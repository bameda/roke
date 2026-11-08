# MongoDB (`mongodb`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add mongodb` (this project) or `roke mcp add mongodb --global`.

[MongoDB's official MCP server](https://github.com/mongodb-js/mongodb-mcp-server),
connected to the project's [`mongodb`](../../services/mongodb/README.md)
service, which it starts. The agent can list databases and collections,
inspect schemas and run queries and aggregations.

It runs **read-only** (`--readOnly`), as MongoDB recommends; the agent can
still change data with `mongosh` in the box. For write tools, use your own
copy of this MCP without that flag (see
[Adding your own MCP](../README.md#adding-your-own-mcp)).

**Network**: nothing to allow.
