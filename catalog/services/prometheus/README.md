# Prometheus (`prometheus`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add prometheus` (or `roke -s prometheus` for one run).

[Prometheus](https://prometheus.io/) collects your app's metrics. It gets
them in two ways:

- **Pushed with OpenTelemetry (OTLP)**: the box's `OTEL_EXPORTER_OTLP_METRICS_*`
  variables point OpenTelemetry SDKs to Prometheus's OTLP receiver, so an
  instrumented app sends its metrics without configuration.
- **Scraped**: by default Prometheus reads `http://box:9464/metrics`, the
  default port of OpenTelemetry's Prometheus exporter. For another port or
  path, see "Your own configuration" below.

Add [`grafana`](../grafana/README.md) for dashboards, and
[`jaeger`](../jaeger/README.md) for traces: the OTLP variables of both
combine, so traces go to Jaeger and metrics to Prometheus.

**Inside the box**

| Variable | Value |
|---|---|
| `PROMETHEUS_URL` | `http://prometheus:9090` |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | `http://prometheus:9090/api/v1/otlp/v1/metrics` |
| `OTEL_EXPORTER_OTLP_METRICS_PROTOCOL` | `http/protobuf` |

**Explore it**

```bash
curl -s "$PROMETHEUS_URL/api/v1/targets" | jq '.data.activeTargets[] | {job: .labels.job, health}'
curl -s "$PROMETHEUS_URL/api/v1/query" --data-urlencode 'query=up' | jq '.data.result'
```

**From your host**: UI at <http://127.0.0.1:9090>.

**Your own configuration.** To scrape other targets, put a
`prometheus.yml` in the project's directory and mount it in its
`compose.yaml`:

```yaml
services:
  prometheus:
    volumes:
      - ${ROKE_PROJECT_CONFIG}/prometheus.yml:/etc/prometheus/prometheus.yml:ro
```

Targets are reachable by name: `box:<port>` for the app, or any service.

**Data**: persisted in the project's `prometheus-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `PROMETHEUS_UI_PORT` | `9090` |
| `PROMETHEUS_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
