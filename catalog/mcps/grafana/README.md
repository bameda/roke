# Grafana (`grafana`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add grafana`.

[Grafana's official MCP server](https://github.com/grafana/mcp-grafana),
connected to the project's [`grafana`](../../services/grafana/README.md)
service, which it starts. The agent can search and create dashboards, look
at the data sources, and query them, for example Prometheus metrics or
Jaeger traces when those services are enabled too.

**Needs**: nothing. The project's Grafana has no login, so the server needs
no token.

**Network**: nothing to allow; it runs in the box and talks to Grafana in
the project's network.
