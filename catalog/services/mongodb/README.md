# MongoDB (`mongodb`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add mongodb`.

MongoDB document database.

**Inside the box**

| Variable | Value |
|---|---|
| `MONGODB_URL` | `mongodb://dev:dev@mongodb:27017/?authSource=admin` |

The user is created as an administrator in the `admin` database, hence
`authSource=admin`. To pick a default database in the URL, put it before the
query string: `mongodb://dev:dev@mongodb:27017/myapp?authSource=admin`.

**Explore it.** The image has no MongoDB shell; `npx` fetches it on first use:

```bash
npx -y mongosh "$MONGODB_URL"
npx -y mongosh "$MONGODB_URL" --quiet --eval 'db.adminCommand({ listDatabases: 1 })'
```

**MCP**: `roke mcp add mongodb` gives the agent tools for this service; see
the [`mongodb` MCP](../../mcps/mongodb/README.md).

**Data**: persisted in the project's `mongodb-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `MONGO_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
| `MONGO_USER` / `MONGO_PASSWORD` | `dev` / `dev` |
