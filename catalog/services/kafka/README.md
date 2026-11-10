# Kafka (`kafka`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add kafka`.

A Kafka-compatible broker using [Redpanda](https://www.redpanda.com/),
with a Schema Registry.

**Inside the box**

| Variable | Value |
|---|---|
| `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_BROKERS` | `kafka:9092` |
| `SCHEMA_REGISTRY_URL` | `http://kafka:8081` |

**Explore it** with `kcat`, which is in the image:

```bash
kcat -b "$KAFKA_BOOTSTRAP_SERVERS" -L                       # brokers and topics
echo '{"id":1}' | kcat -b "$KAFKA_BOOTSTRAP_SERVERS" -t orders -P
kcat -b "$KAFKA_BOOTSTRAP_SERVERS" -t orders -C -o beginning -e
```

Topics are created automatically on first use. For anything else
(consumer groups, topic configuration), the broker's own CLI, `rpk`, is in
its container. Run it from your host: find the container with
`docker ps --filter name=kafka`, then `docker exec <container> rpk topic list`.

**Data**: persisted in the project's `kafka-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `REDPANDA_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
| `KAFKA_MEMORY` | `1G` |
