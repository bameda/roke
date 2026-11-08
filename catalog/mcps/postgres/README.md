# PostgreSQL (`postgres`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add postgres` (this project) or `roke mcp add postgres --global`.

[MCP Toolbox for Databases](https://github.com/googleapis/genai-toolbox),
by Google, with its ready-made PostgreSQL tools, connected to the project's
[`postgres`](../../services/postgres/README.md) service, which it starts.
The agent can list schemas and tables, explain queries and run SQL.

It uses the project's database and credentials (`POSTGRES_DB`,
`POSTGRES_USER`, `POSTGRES_PASSWORD`), so it follows your settings. Its SQL
tool can also change data: it is the project's development database.

**Network**: nothing to allow.
