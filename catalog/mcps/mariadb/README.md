# MariaDB (`mariadb`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add mariadb`.

[MCP Toolbox for Databases](https://github.com/googleapis/genai-toolbox),
by Google, with its ready-made MySQL tools, which work with MariaDB,
connected to the project's [`mariadb`](../../services/mariadb/README.md)
service, which it starts. The agent can list tables and run SQL.

It uses the project's database and credentials (`MARIADB_DATABASE`,
`MARIADB_USER`, `MARIADB_PASSWORD`). Its SQL tool can also change data: it
is the project's development database.

**Network**: nothing to allow.
