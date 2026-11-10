# Service name (`myservice`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add myservice`.

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
| `MYSERVICE_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
