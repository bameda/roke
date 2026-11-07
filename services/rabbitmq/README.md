# RabbitMQ (`rabbitmq`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=rabbitmq` in `~/.config/roke/projects/<name>/project.env`, or `roke -s rabbitmq`.

RabbitMQ message broker, for job queues and messaging between services.

**Inside the box**

| Variable | Value |
|---|---|
| `AMQP_URL` | `amqp://dev:dev@rabbitmq:5672/` |

**From your host**: management UI at <http://127.0.0.1:15672>, user `dev`,
password `dev`.

**From the box.** The management API is reachable too:

```bash
curl -s -u dev:dev http://rabbitmq:15672/api/overview | jq .rabbitmq_version
curl -s -u dev:dev http://rabbitmq:15672/api/queues | jq '.[] | {name, messages}'
```

**Data**: queues and messages are persisted in the project's
`rabbitmq-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `RABBITMQ_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
| `RABBITMQ_USER` / `RABBITMQ_PASSWORD` | `dev` / `dev` |
| `RABBITMQ_UI_PORT` | `15672` |
