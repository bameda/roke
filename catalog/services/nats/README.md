# NATS (`nats`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add nats` (or `roke -s nats` for one run).

[NATS](https://nats.io/) messaging server, with
[JetStream](https://docs.nats.io/nats-concepts/jetstream) enabled for
persistent streams and key-value stores.

**Inside the box**

| Variable | Value |
|---|---|
| `NATS_URL` | `nats://nats:4222` |
| `NATS_MONITOR_URL` | `http://nats:8222` (monitoring endpoints) |

NATS client libraries read `NATS_URL` or take it as their server address.
There is no authentication.

**Explore it.** The `nats` CLI is not in the image; declare it in the
project's `mise.toml` (`"aqua:nats-io/natscli" = "latest"`). It reads
`NATS_URL` by itself:

```bash
nats sub 'orders.>'  # watch messages
nats pub orders.created '{"id":1}'
nats stream ls       # JetStream streams
curl -s "$NATS_MONITOR_URL/varz" | jq '.connections'
```

**Data**: JetStream streams are persisted in the project's `nats-data`
volume. Plain messages are not stored.

**Settings**

| Variable | Default |
|---|---|
| `NATS_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
