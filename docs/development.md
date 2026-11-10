# Development

## How roke is built

The `roke` command is a Python package with no dependencies beyond the
standard library, so it only needs Python 3.10 or newer on the host.
`bin/roke` is a small launcher that checks the Python version and runs it.

| Module | What it does |
|---|---|
| `roke/cli.py` | Parses the arguments into a request and runs it |
| `roke/commands/` | Command handlers: `box.py` (sessions, logs, lifecycle), `doctor.py`, `settings.py`, `agent.py`, `service.py`, `mcp.py`, `network.py` and `setup.py` (init, update) |
| `roke/workspace.py` | A `Workspace`: the project, your configuration and what follows from them for a command. Its steps, in order: open (configuration, project, guards), settings, agent, services, network, docker compose |
| `roke/catalog/` | roke's catalogs: `agents.py` (the coding agents in `agents/`), `services.py` (the services) and `mcps.py` (the MCP servers, and how their definitions are resolved), each looked up in the project's configuration, yours and the repository |
| `roke/settings.py` | Reads and edits `roke.env`, `project.env` and `secrets.env` |
| `roke/project.py` | The project, its compose name and the guards against mounting too much |
| `roke/docker.py` | Everything that talks to Docker: checking it is there, the running projects, docker compose |
| `roke/paths.py` | Where roke and your configuration are, and helpers to read the catalog directories |
| `roke/urls.py` | The output of `roke urls` |
| `roke/ui/` | How roke presents things: messages, errors, the pager and colours (`__init__.py`), the help text (`help.py`) and the terminal Markdown renderer for the READMEs (`markdown.py`) |

Each command is a short function that builds a `Workspace` and calls the
steps it needs. For example, `roke service add` needs the project and its
guards, but neither the settings nor Docker.

Settings files are read by bash, as if sourced, so they keep behaving like
shell files: quotes, comments and variable references work as before.

The scripts that run inside the containers stay in bash: the box's
entrypoint (`docker/entrypoint.sh`), the gateway (`docker/gateway/gateway.sh`)
and each agent's `install.sh` and `setup.sh`.

### From a command to an agent session

For `roke run`, the path through the code is:

1. `bin/roke` starts Python in isolated mode, loading the package from the
   installed roke directory. `roke/cli.py` parses the request and dispatches
   it to `roke/commands/box.py`.
2. `Workspace.open()` resolves the project and checks the mount guards.
   Session starts and configuration edits also register its stable ID,
   retaining the original Compose name during first-use adoption. Read-only
   commands only look up existing registrations.
   `load_all()` reads global and project settings, chooses an agent, selects
   services and MCP servers, then builds the network allow list. Selected
   MCP servers can add services and network destinations.
3. `prepare_compose()` combines the base `compose.yaml`, selected service
   fragments, the project's own Compose override and a temporary port file
   when ports are published. `roke/docker.py` invokes Docker Compose with
   those files and the resolved environment.
4. Compose starts the gateway and selected services. The box shares the
   gateway's network namespace; only the gateway has an external route.
   `docker/entrypoint.sh` prepares project tools and agent instructions, then
   sources the selected agent's `setup.sh` and runs the agent.

The command does not read Compose overrides from the project repository:
they live in roke's configuration directory, outside the agent's writable
mount. The [security guide](security.md) explains this boundary, and the
[network guide](network.md) shows the container layout.

## Development tools

The root `VERSION` file is the single source of the application version,
read by `roke version` (also `roke --version`) and `roke doctor --yaml`.
Keep development versions marked with a `-dev` suffix until preparing a release. Agent and service
versions remain independent of roke's version.

Managed installations store their update channel in the installation's
local Git configuration (`roke.channel`), outside project settings. Stable
updates resolve GitHub's latest published release and check out its tag;
`main` updates only fast-forward. Both the installer and updater preserve
local changes and commits. Installer/update tests use local Git repositories
and simulated GitHub responses, without network access.

Before each commit, [pre-commit](https://pre-commit.com/) checks the
changed files:

| Tool | Checks |
|---|---|
| [ruff](https://docs.astral.sh/ruff/) | Python: lint (fixing what it can) and format |
| [mypy](https://mypy.readthedocs.io/) | Python: types |
| [ShellCheck](https://www.shellcheck.net/) | The shell scripts |
| [zizmor](https://docs.zizmor.sh/) | The GitHub Actions workflows: security issues |
| [check-jsonschema](https://check-jsonschema.readthedocs.io/) | The GitHub workflows, issue forms and `renovate.json`, against their official schemas |
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

## Dependency updates

[Renovate](https://docs.renovatebot.com/) keeps roke's dependencies up to
date, configured in `renovate.json`:

| What | Where |
|---|---|
| Service images | The defaults in each `compose.yaml`: `${POSTGRES_VERSION:-18}` |
| Base images | The `FROM` of each `Dockerfile` |
| Versions in the `Dockerfile`'s `ARG`s | The ones with a `# renovate:` comment above, such as Serena |
| Development tools | `.pre-commit-config.yaml` |
| GitHub Actions | The workflows, pinned by commit SHA |

It opens pull requests on Monday mornings, and nothing is merged
automatically: review each one. Minor and patch updates of the development
tools and actions come together in one pull request. Major versions of
service images are labelled `major`: projects keep the version they pinned
(see [Versions](../catalog/services/README.md#versions)), but check the release
notes for changes to the data format, and update the service's README if
it needs migration steps. The Dependency Dashboard issue lists what is
pending.

Each version lives in one place, so an update changes everything: the
services' READMEs point to their `compose.yaml` instead of repeating the
default, and `compose.yaml` passes the `Dockerfile`'s build arguments only
when they are set.

Renovate runs as the [Mend Renovate app](https://github.com/apps/renovate),
installed on the repository.

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
when there is none. GitHub Actions runs these tests on each push and pull
request (`.github/workflows/test.yml`).

The CI `test` job requires a working Compose binary and excludes the real
Docker integration directory. `ROKE_REQUIRE_COMPOSE=1` makes a missing or
broken Compose binary fail the run before tests start. Both CI jobs set
`ROKE_REQUIRE_NO_SKIPS=1`: an unexpected skip during collection or execution
fails the job instead of hiding missing coverage. These flags are unset in
normal local runs, where optional prerequisites can still cause skips.

### Real Docker tests

`tests/integration/` runs in a separate CI job with a Docker daemon. It
exercises the production gateway in restricted and open modes: internal
service access, allowed domains and ports, blocked DNS and direct IPs, DNS
redirection, service network isolation and web UI forwarding on host loopback.
It also uses the real roke launcher to write to the box's home volume, move
the project and verify that reattaching its ID retains the data.

These tests use local containers as external destinations, so test requests
do not depend on public endpoints. Images still need to be downloaded and
the gateway image built. On a machine with Docker, run:

```bash
docker compose -f tests/integration/compose.yaml build gateway
docker compose -f tests/integration/compose.yaml pull allowed
ROKE_DOCKER_TESTS=1 uvx pytest tests/integration -v
```

The default `uvx pytest` run skips this suite. It remains usable inside
roke's box, which has no Docker daemon. Each integration stack has a unique
project name; teardown prints container logs and removes its containers,
networks and test volumes, including after a test failure.

The tests describe what roke does from the outside, so they do not depend on
how it is written: any change to roke must keep them passing.

## Trying a change

Run your clone's `roke` by its path, in a test project
(`~/src/roke-dev/bin/roke`), so the `roke` you work with every day stays
the installed one; see [working on roke with roke](../CONTRIBUTING.md#working-on-roke-with-roke).
Box images use `roke:build-<hash>` tags derived from the recipe and build
arguments (`roke/images.py`). Identical inputs in both copies share an image;
different inputs get separate tags. The gateway uses `roke-gateway:latest`.
Python code, Compose
files and service definitions are read from the roke directory on each
command. The agents' `setup.sh` and instructions are mounted into the box,
so changes to them apply on its next start. The box's `Dockerfile` copies
`docker/entrypoint.sh` and runs the agents' `install.sh`; the gateway's
`Dockerfile` copies `docker/gateway/gateway.sh`. Changes to these files or
either Dockerfile need `roke build` before they reach a container.
