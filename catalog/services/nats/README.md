# NATS (`nats`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add nats`.

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
| `NATS_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
