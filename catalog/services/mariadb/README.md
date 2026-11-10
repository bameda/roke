# MariaDB (`mariadb`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add mariadb`.

MariaDB, a MySQL-compatible relational database.

**Inside the box**

| Variable | Value |
|---|---|
| `MYSQL_URL` | `mysql://dev:dev@mariadb:3306/app` |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | the same, split up |

MySQL drivers and frameworks connect through `MYSQL_URL` or the individual
variables. A `~/.my.cnf` is generated on every start, so the client tools
connect without arguments.

**Explore it**

```bash
mariadb                                   # interactive shell (also: mysql)
mariadb -e 'SHOW TABLES'
mariadb-dump "$MYSQL_DATABASE" > .db.sql  # backup
mariadb < .db.sql                         # restore
```

The `dev` user only has access to its own database. To create another one
(for tests, say), use the root account:

```bash
mariadb -u root -proot -e "CREATE DATABASE app_test; GRANT ALL ON app_test.* TO 'dev'@'%'"
```

**MCP**: `roke mcp add mariadb` gives the agent tools for this service; see
the [`mariadb` MCP](../../mcps/mariadb/README.md).

**Data**: persisted in the project's `mariadb-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `MARIADB_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
| `MARIADB_USER` / `MARIADB_PASSWORD` | `dev` / `dev` |
| `MARIADB_DATABASE` | `app` |
| `MARIADB_ROOT_PASSWORD` | `root` |
