# Redis (`redis`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add redis` (or `roke -s redis` for one run).

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

**Data**: not persisted. It survives between sessions while the container
runs, and is lost on `roke down`, which is usually what you want for a
cache.

**Settings**

| Variable | Default |
|---|---|
| `REDIS_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
