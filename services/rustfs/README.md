# RustFS (`rustfs`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=rustfs` in `~/.config/roke/projects/<name>/project.env`, or `roke -s rustfs`.

[RustFS](https://rustfs.com/), S3-compatible object storage with a web
console, for uploads and files your app would store in S3. It replaces
MinIO, whose open-source edition was archived in 2026.
[`seaweedfs`](../seaweedfs/README.md) is an alternative: both give the box
the same variables, so enable one or the other in a project, not both.

**Inside the box**

| Variable | Value |
|---|---|
| `S3_ENDPOINT`, `AWS_ENDPOINT_URL` | `http://rustfs:9000` |
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

**From your host**: web console at <http://127.0.0.1:9001>, user `dev`,
password `devdevdev`.

**Data**: persisted in the project's `rustfs-data` volume.

**Settings**

| Variable | Default |
|---|---|
| `RUSTFS_ACCESS_KEY` / `RUSTFS_SECRET_KEY` | `dev` / `devdevdev` |
| `RUSTFS_CONSOLE_PORT` | `9001` |
| `RUSTFS_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
