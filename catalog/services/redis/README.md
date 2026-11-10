# Redis (`redis`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add redis`.

Redis in-memory store, for caches, sessions, queues and rate limiting.

**Inside the box**

| Variable | Value |
|---|---|
| `REDIS_URL` | `redis://redis:6379/0` |

**Explore it**

```bash
redis-cli -u "$REDIS_URL" ping
redis-cli -u "$REDIS_URL" --scan --pattern 'session:*'
redis-cli -u "$REDIS_URL" monitor   # watch commands live
redis-cli -u "$REDIS_URL" flushall  # empty it
```

**MCP**: `roke mcp add redis` gives the agent tools for this service; see
the [`redis` MCP](../../mcps/redis/README.md).

**Data**: kept in memory; lost on `roke down`.

**Settings**

| Variable | Default |
|---|---|
| `REDIS_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
