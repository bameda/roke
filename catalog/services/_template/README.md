# Service name (`myservice`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add myservice` (or `roke -s myservice` for one run).

One or two sentences: what the service is and what a project uses it for.

**Inside the box**

| Variable | Value |
|---|---|
| `MYSERVICE_URL` | `http://myservice:8080` |

How an app connects: which variables it reads, driver options to watch out
for.

**Explore it**

```bash
# commands to inspect or reset it from roke shell
```

**From your host**: web UI address, if it publishes one.

**Data**: persisted in the project's `myservice-data` volume, or not
persisted.

**Settings**

| Variable | Default |
|---|---|
| `MYSERVICE_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
