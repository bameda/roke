# Contributing to roke

Thanks for helping! Bug reports, documentation fixes, new services, new
agents and code are all welcome.

- [Before you start](#before-you-start)
- [Setting up](#setting-up)
- [Working on roke with roke](#working-on-roke-with-roke)
- [Guidelines](#guidelines)
- [Adding a service or an agent](#adding-a-service-or-an-agent)
- [Pull requests](#pull-requests)

## Before you start

- **Bugs and small fixes**: open a pull request directly, or an issue if you
  are not sure how to fix it.
- **Larger changes**, new commands or anything that changes how roke
  behaves: open an issue first, so we can agree on the approach before you
  spend time on it.
- **Security issues**: do not open a public issue. See [SECURITY.md](SECURITY.md).

## Setting up

You need Linux with Docker and its Compose plugin, Python 3.11 or newer (for
the development tools; roke itself needs 3.10), git, jq and
[uv](https://docs.astral.sh/uv/).

```fish
git clone https://github.com/bameda/roke.git ~/src/roke-dev
cd ~/src/roke-dev
uvx pre-commit install       # checks every commit
uvx pytest                   # runs the tests
```

To try your changes, run your clone's `roke` by its path, in a test
project: `~/src/roke-dev/bin/roke`. [Development](docs/development.md)
explains how roke is built, the development tools, dependency updates and
the tests.

## Working on roke with roke

You can work on roke with a coding agent, inside a roke box like any other
project. [AGENTS.md](AGENTS.md) gives agents what they need to know about
this repository; Codex, OpenCode and Claude Code read it (Claude Code
through `CLAUDE.md`).

roke refuses to run in its own installation, so that an agent cannot change
the tool that isolates it. Keep two copies:

- **the roke that isolates you**, installed with the
  [installer](docs/installation.md#install-roke), in `~/.local/share/roke`;
- **your development clone**, which is just a project for that roke.

```fish
cd ~/src/roke-dev
roke                         # the installed roke, with your development clone as the project
```

Inside the box, the agent can run the tests and pre-commit; there is no
Docker, so the tests that need a real Docker Compose skip themselves. The
installer's `ROKE_DIR` and `ROKE_VERSION` let you keep the installed copy on
a released version while you develop.

## Guidelines

**The box is the security boundary.** roke assumes the agent may misbehave
(see [Security](docs/security.md)). A change that widens what the box can
reach (mounts, capabilities, network, the guards against mounting too much)
needs a clear reason, and the pull request must say so.

**Tests.** A change in behaviour comes with tests. They run the real `roke`
command against a fake `docker` and describe what it does from the outside;
see [the tests](docs/development.md#tests).

**Documentation.** It is written in English and lives with the code: if
your change affects how roke is used, update the guides in the same pull
request. Each version lives in one place: service versions in their
`compose.yaml`, image versions in the `Dockerfile`s.

**Commits** follow [Conventional Commits](https://www.conventionalcommits.org/),
in English: `feat(services): add keycloak`, `fix: ...`, `docs: ...`. A
change that requires users to do something (rename a setting, rebuild,
migrate data) is marked with `!` (`feat!: ...`) and its message ends with a
`BREAKING CHANGE:` paragraph explaining what to do.

**Style** is checked by pre-commit: ruff formats and lints the Python code,
mypy checks its types, ShellCheck the shell scripts and zizmor the
workflows.

## Adding a service or an agent

- **A service**: follow [Adding your own service](catalog/services/README.md#adding-your-own-service).
  In short: copy `catalog/services/_template/`, keep the version in a `*_VERSION`
  variable with a fixed default, publish web UIs through the gateway, and
  add the service to the [catalog](catalog/services/README.md) and its README.
- **An agent**: follow [Adding an agent](catalog/agents/README.md#adding-an-agent).
  In short: copy `catalog/agents/_template/`, fill in `install.sh`, `setup.sh`,
  `allow.txt` (the destinations it needs) and its README, and add it to the
  agents' table.

- **An MCP server**: follow [Adding your own MCP](catalog/mcps/README.md#adding-your-own-mcp):
  copy `catalog/mcps/_template/`, fill in its `mcp.json` and README, and add it to
  the MCP catalog.

If you are not sure a service or an agent belongs in roke, open an issue
with the "Service or agent request" form first.

## Pull requests

- Keep each pull request to one change; several small ones are easier to
  review than a big one.
- Fill in the template: what changes, why, and how you tested it.
- The checks and the tests must pass on GitHub Actions.
