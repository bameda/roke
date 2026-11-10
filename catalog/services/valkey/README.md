# Valkey (`valkey`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add valkey`.

Valkey, the open-source fork of Redis. It speaks the same protocol, so Redis
clients and `redis-cli` work with it unchanged.

**Inside the box**

| Variable | Value |
|---|---|
| `VALKEY_URL` | `redis://valkey:6379/0` |

If your app expects `REDIS_URL`, map it in `projects/<id>/compose.yaml`:

```yaml
services:
  box:
    environment:
      REDIS_URL: redis://valkey:6379/0
```

**Explore it**: as with [redis](../redis/README.md), using `"$VALKEY_URL"`.

**MCP**: `roke mcp add valkey` gives the agent tools for this service; see
the [`valkey` MCP](../../mcps/valkey/README.md).

**Data**: not persisted, as with redis.

**Settings**

| Variable | Default |
|---|---|
| `VALKEY_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
