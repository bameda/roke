# Jaeger (`jaeger`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=jaeger` in `~/.config/roke/projects/<name>/project.env`, or `roke -s jaeger`.

[Jaeger](https://www.jaegertracing.io/) collects
[OpenTelemetry](https://opentelemetry.io/) traces from your app and shows
them in a web UI: which calls a request made, how long each took, where it
failed.

**Inside the box**

| Variable | Value |
|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://jaeger:4318` |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` |
| `JAEGER_QUERY_URL` | `http://jaeger:16686` |

These are the standard OpenTelemetry variables, so the SDKs of every
language send traces to Jaeger without configuration. Set
`OTEL_SERVICE_NAME` in the project's `project.env` to name your app in the
UI. OTLP over gRPC is also available, on `jaeger:4317`.

**From your host**: open the UI at <http://127.0.0.1:16686>.

**From the box.** The query API lets the agent check the traces of a
request it just made:

```bash
curl -s "$JAEGER_QUERY_URL/api/services" | jq
curl -s "$JAEGER_QUERY_URL/api/traces?service=my-app&limit=5" | jq '.data[].spans | length'
```

**Data**: kept in memory, so it is lost on `roke down`.

**Settings**

| Variable | Default |
|---|---|
| `JAEGER_UI_PORT` | `16686` |
| `JAEGER_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
