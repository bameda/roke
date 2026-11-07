# Elasticsearch (`elasticsearch`)

Search engine, single node, without security: for local development only.

**Inside the box**

| Variable | Value |
|---|---|
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` |

**Explore it**

```bash
curl -s "$ELASTICSEARCH_URL/_cluster/health" | jq
curl -s "$ELASTICSEARCH_URL/_cat/indices?v"
```

**Data**: persisted in the project's `elasticsearch-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `ELASTICSEARCH_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
