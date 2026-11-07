# PostgreSQL (`postgres`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=postgres` in `~/.config/roke/projects/<name>/project.env`, or `roke -s postgres`.

PostgreSQL relational database. Requires PostgreSQL 18 or newer.

**Inside the box**

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgres://dev:dev@postgres:5432/app` |
| `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` | the same, split up |

Most frameworks and drivers read `DATABASE_URL` directly. The `PG*` variables
make the client tools connect without arguments.

**Explore it**

```bash
psql                                                    # interactive shell on the project DB
psql -c '\dt'                                           # list tables
createdb app_test                                       # extra database, e.g. for tests
psql -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm'
pg_dump -Fc -f .db.dump                                 # backup
pg_restore --clean -d "$PGDATABASE" .db.dump
dropdb --force "$PGDATABASE" && createdb "$PGDATABASE"  # empty the DB
```

**MCP**: `roke mcp add postgres` gives the agent tools for this service; see
the [`postgres` MCP](../../mcps/postgres/README.md).

**Data**: persisted in the project's `pgdata` volume.

**Settings**

| Variable | Default |
|---|---|
| `POSTGRES_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
| `POSTGRES_CLIENT_VERSION` | psql and pg_dump in the image: the [`Dockerfile`](../../Dockerfile)'s by default; set it in `roke.env` and rebuild to change it |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | `dev` / `dev` |
| `POSTGRES_DB` | `app` |

**Initial SQL.** To run scripts when the database is created, mount them in
`projects/<name>/compose.yaml`. They only run on an empty database:

```yaml
services:
  postgres:
    volumes:
      - ${ROKE_PROJECT_CONFIG}/initdb:/docker-entrypoint-initdb.d:ro
```

**PostGIS or other images.** Swap the image in the project's
`compose.yaml`, as in the
[`reference`](../../examples/projects/reference/compose.yaml) example. It
must be based on PostgreSQL 18 or newer.

## Major upgrades

The major version is pinned instead of following `latest`, because each
major keeps its data in its own subdirectory: moving to a new major starts
with an **empty database**. For a development DB, the simplest option is to
re-run your migrations and seeds. To keep the data, dump it first:

```fish
cd ~/src/my-project
roke exec -s postgres pg_dumpall -f .pg-upgrade.sql       # with the old version
# set POSTGRES_VERSION=19 and POSTGRES_CLIENT_VERSION=19 in roke.env, then:
roke build -s postgres -- psql -d postgres -f .pg-upgrade.sql
rm .pg-upgrade.sql
```

Errors about the role or database already existing are expected. The old
major's files stay in the volume until you run `roke purge`.
