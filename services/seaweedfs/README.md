# SeaweedFS (`seaweedfs`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=seaweedfs` in `~/.config/roke/projects/<name>/project.env`, or `roke -s seaweedfs`.

[SeaweedFS](https://github.com/seaweedfs/seaweedfs), a mature distributed
storage system with an S3-compatible API, here as a single node. It is an
alternative to [`rustfs`](../rustfs/README.md): both give the box the same
variables, so enable one or the other in a project, not both.

**Inside the box**

| Variable | Value |
|---|---|
| `S3_ENDPOINT`, `AWS_ENDPOINT_URL` | `http://seaweedfs:8333` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `dev` / `devdevdev` |
| `AWS_REGION` | `us-east-1` |

AWS SDKs pick these variables up. Most SDKs also need **path-style
addressing** for a local S3 server: `forcePathStyle: true` in the
JavaScript SDK, `addressing_style: "path"` in boto3, and similar in others.

**Explore it.** The image has no S3 client; `uvx` fetches the AWS CLI on
first use, and it already uses `AWS_ENDPOINT_URL`:

```bash
uvx --from awscli aws s3 mb s3://uploads       # create a bucket
uvx --from awscli aws s3 ls s3://uploads
uvx --from awscli aws s3 cp README.md s3://uploads/
```

**From your host**: SeaweedFS's file browser (the filer) at
<http://127.0.0.1:8888>; buckets are under `/buckets`.

**Data**: persisted in the project's `seaweedfs-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `SEAWEEDFS_ACCESS_KEY` / `SEAWEEDFS_SECRET_KEY` | `dev` / `devdevdev` |
| `SEAWEEDFS_UI_PORT` | `8888` |
| `SEAWEEDFS_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
