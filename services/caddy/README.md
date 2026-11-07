# Caddy (`caddy`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add caddy` (or `roke -s caddy` for one run).

Caddy reverse proxy. You do not need it just to open your app: `ROKE_PORTS`
already publishes the dev server. Use it to serve several backends under one
address (for example, the frontend and an API under `/api`), to add headers,
or to try things that behave differently behind a proxy.

**Inside the box**

| Variable | Value |
|---|---|
| `PROXY_URL` | `http://127.0.0.1:8080` (the address on your host) |

**From your host**: <http://127.0.0.1:8080>, forwarded to `PROXY_UPSTREAM`,
which is the agent's dev server (`box:3000` by default). The dev server
must listen on `0.0.0.0`.

**Routing.** The configuration is in `services/caddy/Caddyfile` and is shared
by every project. For a project-specific one, mount your own in
`projects/<name>/compose.yaml`:

```yaml
services:
  caddy:
    volumes:
      - ${ROKE_PROJECT_CONFIG}/Caddyfile:/etc/caddy/Caddyfile:ro
```

For example, frontend and API under the same address:

```caddyfile
:80 {
	handle /api/* {
		reverse_proxy box:8000
	}
	handle {
		reverse_proxy box:5173
	}
}
```

Any service is reachable by name as an upstream (`mailpit:8025`,
`rustfs:9000`...).

**Settings**

| Variable | Default |
|---|---|
| `CADDY_PORT` | `8080` |
| `PROXY_UPSTREAM` | `box:3000` |
| `CADDY_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
