# Development

## How roke is built

The `roke` command is a Python package with no dependencies beyond the
standard library, so it only needs Python 3.10 or newer on the host.
`bin/roke` is a small launcher that checks the Python version and runs it.

| Module | What it does |
|---|---|
| `roke/cli.py` | Parses the arguments into a request and runs it |
| `roke/commands/` | The commands, one module per group of `roke help`: `box.py` (run, continue, shell, exec, urls, settings, build, down, purge), `agent.py`, `service.py`, `network.py` and `setup.py` (init, update) |
| `roke/workspace.py` | A `Workspace`: the project, your configuration and what follows from them for a command. Its steps, in order: open (configuration, project, guards), settings, agent, services, network, docker compose |
| `roke/agents.py` | The coding agents in `agents/` |
| `roke/services.py` | The services, and where each one is defined: the project's, yours or the catalog's |
| `roke/settings.py` | Reads and edits `roke.env`, `project.env` and `secrets.env` |
| `roke/project.py` | The project, its compose name and the guards against mounting too much |
| `roke/docker.py` | Everything that talks to Docker: checking it is there, the running projects, docker compose |
| `roke/paths.py` | Where roke and your configuration are, and helpers to read the catalog directories |
| `roke/urls.py` | The output of `roke urls` |
| `roke/ui.py` | Messages, errors and the help |

Each command is a short function that builds a `Workspace` and calls the
steps it needs. For example, `roke service add` needs the project and its
guards, but neither the settings nor Docker.

Settings files are read by bash, as if sourced, so they keep behaving like
shell files: quotes, comments and variable references work as before.

The scripts that run inside the containers stay in bash: the box's
entrypoint (`docker/entrypoint.sh`), the gateway (`docker/gateway/gateway.sh`)
and each agent's `install.sh` and `setup.sh`.

## Development tools

Before each commit, [pre-commit](https://pre-commit.com/) checks the
changed files:

| Tool | Checks |
|---|---|
| [ruff](https://docs.astral.sh/ruff/) | Python: lint (fixing what it can) and format |
| [mypy](https://mypy.readthedocs.io/) | Python: types |
| [ShellCheck](https://www.shellcheck.net/) | The shell scripts |
| [zizmor](https://docs.zizmor.sh/) | The GitHub Actions workflows: security issues |
| [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) | Trailing whitespace, final newlines, YAML, merge conflicts, shebangs |

Nothing needs installing besides [uv](https://docs.astral.sh/uv/): pre-commit
installs each tool in its own environment. Set it up once in your clone:

```fish
uvx pre-commit install
```

From then on, `git commit` runs the checks on the files it commits and
stops if one fails; ruff fixes and formats what it can, so add its changes
and commit again. To check everything:

```fish
uvx pre-commit run --all-files
```

The tools' settings live in `pyproject.toml` (ruff, mypy) and
`.pre-commit-config.yaml` (versions). The tools need Python 3.11 or newer;
roke itself only needs 3.10. GitHub Actions runs the same checks, then the
tests, on each push.

## Tests

The tests run the real `roke` command against a fake `docker`
(`tests/fakes/docker`), which records every call instead of running it, so
they need neither Docker nor any container. Each test gets an isolated home,
configuration and projects in a temporary directory.

```fish
uvx pytest                 # with uv
python3 -m pytest          # or with pytest installed
```

The tests that check the resolved configurations of the example projects,
and `roke urls`, also need a real Docker Compose binary; they are skipped
when there is none. GitHub Actions runs every test on each push, after the
checks above (`.github/workflows/test.yml`).

The tests describe what roke does from the outside, so they do not depend on
how it is written: any change to roke must keep them passing.

## Trying a change

Run `./install.sh` from your clone: it links `roke` to that clone, so your
changes apply at once. The scripts that run inside the containers
(`docker/entrypoint.sh`, `docker/gateway/gateway.sh`, the agents'
`setup.sh`) are mounted from the repository, so they apply on the next
start too; the `Dockerfile`s and the agents' `install.sh` need
`roke build`.
