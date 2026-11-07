# Grafana (`grafana`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=grafana` in `~/.config/roke/projects/<name>/project.env`, or `roke -s grafana`.

[Grafana](https://grafana.com/), dashboards for your app's metrics and
traces. It comes with two data sources already configured, which work when
their services are enabled too:

- **Prometheus**, the default: enable [`prometheus`](../prometheus/README.md);
- **Jaeger**: enable [`jaeger`](../jaeger/README.md).

For the full set: `ROKE_SERVICES=prometheus,grafana,jaeger`.

**From your host**: <http://127.0.0.1:3001>, without login: it is local, so
everyone is an administrator. The host port is 3001 rather than Grafana's
usual 3000, which dev servers often use.

**Inside the box**

| Variable | Value |
|---|---|
| `GRAFANA_URL` | `http://grafana:3000` |

The agent can use Grafana's HTTP API, for example to create a dashboard:

```bash
curl -s "$GRAFANA_URL/api/datasources" | jq '.[].name'
```

**Your own dashboards and data sources.** Dashboards you create in the UI
are kept in the project's `grafana-data` volume. To provision them from
files, mount a provisioning directory in the project's `compose.yaml`; see
[Grafana's provisioning docs](https://grafana.com/docs/grafana/latest/administration/provisioning/).

**MCP**: `roke mcp add grafana` gives the agent tools for this service; see
the [`grafana` MCP](../../mcps/grafana/README.md).

**Data**: persisted in the project's `grafana-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `GRAFANA_UI_PORT` | `3001` |
| `GRAFANA_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
