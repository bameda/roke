# Example: Rust API

For a Rust web API (axum, actix-web...) using PostgreSQL through
[sqlx](https://github.com/launchbadge/sqlx).

## What it sets up

- **`project.env`**: `postgres`, port 8080, and Serena.
- **`compose.yaml`**: a separate build directory for the box (see below).
- **`AGENTS.md`**: building, testing, linting and sqlx's offline data.

## In the project

Add a `mise.toml`. The components give the box Clippy, rustfmt and
rust-analyzer, which Serena uses:

```toml
[tools]
rust = { version = "stable", components = "clippy,rustfmt,rust-analyzer" }
"cargo:sqlx-cli" = "latest"
```

Two things work differently from a usual setup:

- **sqlx checks queries at compile time.** Its `query!` macros connect to
  the database while compiling, using `DATABASE_URL`, which the box already
  provides. Run `cargo sqlx prepare` after changing queries and commit the
  `.sqlx/` directory: builds without a database (CI, or your host) then use
  it with `SQLX_OFFLINE=true`.
- **Separate build artifacts.** `compose.yaml` sets `CARGO_TARGET_DIR` to the
  project's home volume, avoiding conflicts with the host's toolchain.

The API must listen on `0.0.0.0:8080` to be reachable at
`http://127.0.0.1:8080`.

## Check it

From `roke shell`:

```bash
sqlx database create && sqlx migrate run
cargo test
cargo clippy --all-targets -- -D warnings
```
