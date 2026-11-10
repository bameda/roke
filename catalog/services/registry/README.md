# OCI registry (`registry`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add registry`.

A local OCI registry ([Distribution](https://distribution.github.io/distribution/)),
for pushing and pulling Helm charts and other OCI artifacts without
publishing anything. It uses plain HTTP and no authentication.

**Inside the box**

| Variable | Value |
|---|---|
| `OCI_REGISTRY` | `registry:5000` |

**Explore it**

```bash
helm package ./chart
helm push mychart-0.1.0.tgz "oci://$OCI_REGISTRY/charts" --plain-http
helm pull "oci://$OCI_REGISTRY/charts/mychart" --version 0.1.0 --plain-http
curl -s "http://$OCI_REGISTRY/v2/_catalog" | jq
```

There is no Docker daemon in the box, so the agent cannot build container
images. It can copy existing ones with tools such as
[crane](https://github.com/google/go-containerregistry/tree/main/cmd/crane),
installable with mise.

**From your host**: the registry is also published on `127.0.0.1:5000`, so
you can pull what the agent pushed (`helm pull
oci://127.0.0.1:5000/charts/mychart --plain-http`).

**Data**: persisted in the project's `registry-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `REGISTRY_PORT` | `5000` (host port) |
| `REGISTRY_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
