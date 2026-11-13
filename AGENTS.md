# Working on roke

Instructions for AI coding agents working on this repository, and a quick
orientation for anyone new to it. roke runs coding agents in a Docker
container that only sees one project: [README.md](README.md) says what it
does, `docs/` how, and [CONTRIBUTING.md](CONTRIBUTING.md) how to contribute.

## Layout

| Path | What it is |
|---|---|
| `bin/roke` | Launcher: checks Python 3.10 or newer and runs the `roke` package |
| `roke/` | The `roke` command. `cli.py` parses the arguments, `commands/` has one module per group of `roke help`, `workspace.py` the steps every command shares, `catalog/` the agents, services and MCP servers |
| `catalog/agents/<agent>/` | Each coding agent: `install.sh` (at image build), `setup.sh` (on every start, in the box), `allow.txt` and a README. `catalog/agents/AGENTS.md` holds the box's instructions to the agents, and `catalog/agents/mcp.py` translates MCP servers into each agent's format |
| `catalog/services/<name>/` | The service catalog: a compose fragment and a README each |
| `catalog/mcps/<name>/` | The MCP catalog: an `mcp.json` and a README each |
| `Dockerfile`, `compose.yaml` | The box's image, and the base Compose file: the box and the gateway |
| `docker/` | The box's entrypoint, and the gateway (the project's network policy) |
| `scripts/release.py` | Prepares and publishes releases, in CI; see `docs/releases.md` |
| `CHANGELOG.md`, `VERSION` | The release notes, written by the release script, and the current version |
| `examples/` | The configuration template (`roke init`) and example projects |
| `tests/` | Black-box tests of the `roke` command, against a fake `docker`; `tests/integration/` runs against a real Docker daemon, in CI |
| `docs/` | The user guides, and `development.md` for contributors |

## Commands

```bash
uvx pytest                       # the tests: no Docker needed
uvx pre-commit run --all-files   # ruff, mypy, ShellCheck, zizmor, schemas
```

Run both before you finish. ruff fixes and formats what it can: when
pre-commit reports changed files, run it again. The tests that need a real
Docker Compose skip themselves when there is none, as inside roke's box.

## Rules

- **The box is the security boundary.** roke assumes the agent in the box
  may misbehave. Do not widen what the box can reach (mounts, capabilities,
  network, the guards in `roke/project.py`) without a clear reason, stated
  in the commit message and the pull request.
- **roke is standard-library Python 3.10.** No third-party dependencies in
  `roke/`. Code must pass ruff and mypy.
- **What runs in the containers stays in bash** (`docker/`, the agents'
  `install.sh` and `setup.sh`), and must pass ShellCheck.
- **Every change in behaviour comes with tests** in `tests/`. They run the
  real `bin/roke` against `tests/fakes/docker`, which records each call, and
  check the calls, the output and the files written. Tests must not depend
  on the catalog's versions (use `catalog_default` from `tests/helpers.py`)
  nor on the current git branch: both change under them.
- **Documentation is English and changes with the code.** Examples of
  output in the guides are copied from real output.
- **Each version lives in one place**: service images in their
  `compose.yaml` defaults (`${POSTGRES_VERSION:-18}`), image builds in the
  `Dockerfile`'s `ARG`s, MCP packages pinned in their `mcp.json`. Renovate
  updates them; do not repeat them elsewhere.
- **Services have no route out**, and publish their web UIs through the
  gateway (`ROKE_FORWARD_<NAME>`), never with `ports:` of their own.
- **Commits follow Conventional Commits**, in English. A change that
  requires users to do something is marked with `!` and ends with a
  `BREAKING CHANGE:` paragraph saying what to do.

## Release recommendations

When proposing changes, assess whether they justify a release using
[Version selection](docs/releases.md#version-selection). Consider the
accumulated changes since the last published release, not just the current
commit, and recommend the increment with the greatest compatibility impact:

- **Major**: incompatible changes requiring users to adapt commands,
  configuration or workflows. From `1.0.0` onward, include migration steps.
- **Minor**: new functionality that preserves existing usage, such as a
  command, optional flag, service or agent. Below `1.0.0`, incompatible
  changes also use minor and still require migration instructions.
- **Patch**: compatible fixes and maintenance without new functionality,
  including documentation corrections and compatible dependency updates.

A release recommendation should explain the benefit to users, the proposed
increment and any migration needed. Important fixes and useful new features
can justify a release; internal refactoring, tests or CI changes alone can
usually wait and be grouped with later changes. Not every commit needs a
release. The maintainer selects the increment and starts release preparation.

## Adding a service, an agent or an MCP server

Follow [Adding your own service](catalog/services/README.md#adding-your-own-service),
[Adding an agent](catalog/agents/README.md#adding-an-agent) or
[Adding your own MCP](catalog/mcps/README.md#adding-your-own-mcp): each starts from
a `_template/` directory. Add the new entry to its catalog's table too.

## Working on roke inside roke

roke refuses to run in its own installation, so that an agent cannot change
the tool that isolates it. Work on a separate clone, isolated by an
installed roke (see [CONTRIBUTING.md](CONTRIBUTING.md#working-on-roke-with-roke)).
Inside the box there is no Docker: the tests and pre-commit work, and the
tests that need a real Docker Compose skip themselves.
