# WireMock (`wiremock`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=wiremock` in `~/.config/roke/projects/<name>/project.env`, or `roke -s wiremock`.

[WireMock](https://wiremock.org/) simulates the HTTP APIs your app depends
on (payments, email providers, third-party services...), so it can be
developed and tested without calling them. Point your app at `WIREMOCK_URL`
instead of the real API and define the responses.

**Inside the box**

| Variable | Value |
|---|---|
| `WIREMOCK_URL` | `http://wiremock:8080` |

**Define responses** through its admin API, from your tests or from
`roke shell`:

```bash
curl -s -X POST "$WIREMOCK_URL/__admin/mappings" -d '{
  "request":  { "method": "GET", "urlPath": "/v1/customers/42" },
  "response": { "status": 200, "jsonBody": { "id": 42, "name": "Ada" },
                "headers": { "Content-Type": "application/json" } }
}'
curl -s "$WIREMOCK_URL/v1/customers/42"
curl -s "$WIREMOCK_URL/__admin/requests" | jq '.requests | length'  # calls received
curl -s -X POST "$WIREMOCK_URL/__admin/reset"                       # start over
```

To load mappings from files instead, keep them in the project (for
example in `wiremock/mappings/`) and mount that directory in the project's
`compose.yaml`. Create the directory first: if it does not exist, Docker
creates it owned by root.

```yaml
services:
  wiremock:
    volumes:
      - ${PROJECT_DIR}/wiremock:/home/wiremock:ro
```

**Data**: mappings created through the API are lost on `roke down`.

**Settings**

| Variable | Default |
|---|---|
| `WIREMOCK_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
