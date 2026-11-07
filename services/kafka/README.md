# Kafka (`kafka`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add kafka` (or `roke -s kafka` for one run).

A Kafka-compatible broker, using [Redpanda](https://www.redpanda.com/): a
single binary without ZooKeeper or a JVM, which starts in seconds. It
speaks the Kafka protocol, so Kafka clients and frameworks (Spring Kafka,
franz-go, librdkafka, KafkaJS...) work unchanged. It also includes a
Schema Registry.

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
| `REDPANDA_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
| `KAFKA_MEMORY` | `1G` |
