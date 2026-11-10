# Example: Go service

For a Go service with PostgreSQL and NATS.

## What it sets up

- **`project.env`**: `postgres` and `nats`, port 8080 for the service, and
  Serena.
- **`AGENTS.md`**: building, testing and linting.

## In the project

Add a `mise.toml`. Serena needs `gopls`, Go's language server:

```toml
[tools]
go = "1.25"                               # the version in your go.mod
golangci-lint = "latest"
"go:golang.org/x/tools/gopls" = "latest"
```

Read the settings from the environment: `DATABASE_URL` works as is with
pgx and lib/pq, and `NATS_URL` with nats.go. The service must listen on
`0.0.0.0:8080` (or `:8080`) to be reachable at `http://127.0.0.1:8080`.

## Check it

From `roke shell`:

```bash
go build ./...
go test ./...
golangci-lint run
```
