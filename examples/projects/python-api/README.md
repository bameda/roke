# Example: Python API

For a Python web API (FastAPI, Flask, Django...) with PostgreSQL and Redis,
managed with [uv](https://docs.astral.sh/uv/).

## What it sets up

- **`project.env`**: `postgres` and `redis`, port 8000 for the dev server,
  and Serena.
- **`compose.yaml`**: database URLs in the forms SQLAlchemy expects (see
  below), plus a separate database URL for the tests.
- **`AGENTS.md`**: how to run, test and migrate the project.

## In the project

Add a `mise.toml` to pin the Python version (uv is already in the box):

```toml
[tools]
python = "3.13"
```

Read the database and Redis settings from the environment, for example
`SQLALCHEMY_DATABASE_URL` and `REDIS_URL`. The box's `DATABASE_URL` starts
with `postgres://`, which works for Django (`dj-database-url`) and most
libraries, but SQLAlchemy only accepts `postgresql://` or a driver-specific
scheme such as `postgresql+psycopg://`. That is why `compose.yaml` defines
`SQLALCHEMY_DATABASE_URL`: adapt its scheme to your driver.

The dev server must listen on `0.0.0.0` to be reachable at
`http://127.0.0.1:8000`, for example
`uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.

## Check it

From `roke shell`:

```bash
createdb app_test        # once: the database for the tests
uv sync
uv run pytest
```
