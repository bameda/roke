# Valkey (`valkey`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=valkey` in `~/.config/roke/projects/<name>/project.env`, or `roke -s valkey`.

Valkey, the open-source fork of Redis. It speaks the same protocol, so Redis
clients and `redis-cli` work with it unchanged.

**Inside the box**

| Variable | Value |
|---|---|
| `VALKEY_URL` | `redis://valkey:6379/0` |

If your app expects `REDIS_URL`, map it in `projects/<name>/compose.yaml`:

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
| `VALKEY_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
