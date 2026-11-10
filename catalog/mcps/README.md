# MCP servers

MCP servers give the agent tools beyond the project: GitHub, documentation,
web pages... roke manages them like the services: you add them to a project,
or to every project, and each agent gets them in its own format, so
switching agents keeps them.

```fish
roke mcp                         # the catalog, marking what the project uses
roke mcp add github              # this project
roke mcp add context7 --global   # every project
roke mcp rm github
```

They apply from the next start of the project. `roke settings` lists the
project's MCP servers, and marks those left out because a secret they need
is not set.

## Catalog

Online services:

| MCP | What it gives the agent | Needs |
|---|---|---|
| [`context7`](context7/README.md) | Up-to-date documentation and code examples of libraries | Optionally `CONTEXT7_API_KEY` |
| [`fetch`](fetch/README.md) | Web pages as markdown, from the allowed destinations | — |
| [`github`](github/README.md) | Repositories, issues, pull requests and Actions | `GITHUB_PAT` |
| [`penpot`](penpot/README.md) | Read and change your Penpot designs | `PENPOT_MCP_KEY` |

For the project's [services](../services/README.md), each one starting the
service it talks to and using the project's settings (database, user,
password...):

| MCP | Service | What it gives the agent |
|---|---|---|
| [`grafana`](grafana/README.md) | `grafana` | Dashboards, data sources and their queries |
| [`mariadb`](mariadb/README.md) | `mariadb` | Schemas and SQL |
| [`mongodb`](mongodb/README.md) | `mongodb` | Collections, queries and aggregations, read-only |
| [`postgres`](postgres/README.md) | `postgres` | Schemas and SQL |
| [`redis`](redis/README.md) | `redis` | Keys, values and commands |
| [`valkey`](valkey/README.md) | `valkey` | Keys, values and commands |

[Serena](../../docs/serena.md) is an MCP server too, but it is installed in the
image and enabled with `ROKE_SERENA` or `--serena`.

## Tool approvals

MCP activation and tool approval are separate settings. Set both when adding
a server, or change its approval policy later:

```bash
roke mcp add context7 --allow
roke mcp add github --ask
roke mcp allow serena
roke mcp ask serena
roke mcp show serena
```

`allow` preauthorizes the server's tools; `ask` requests confirmation and
revokes roke's preauthorization while keeping the server enabled. Both
commands accept several names. `add --allow` or `add --ask` applies the
policy to every name being added; the flags are mutually exclusive.
Adding a server without either flag preserves its approval preference.

Preferences are per project. `--global` sets defaults for every project;
an explicit project preference wins for that server, so `roke mcp ask NAME`
can override a global `allow`. `roke mcp show NAME` displays the effective
policy and its source. With no preference, the agent's own defaults apply.
Removing a server clears its approval preference at the same scope.
If it remains enabled globally, project approval overrides are kept.

Serena supports the same commands: `roke mcp add serena --allow` enables
the built-in server and preauthorizes its tools. `roke mcp rm serena`
disables it in that scope. `allow` and `ask` alone do not enable a server.
The existing `--serena` and `ROKE_SERENA` settings remain available.

Changes apply on the next session start. roke stores preferences outside
the project repository and translates them into Codex server approval
settings, Claude Code permission rules, and OpenCode 2 permission rules.
Separately configured tool rules and managed policies retain their agent's
native precedence. MCP authentication and interactive server requests use
their own flows. To clear a native permission saved independently by an
agent, use that agent's permission controls.

Approval preferences require current agents supporting these settings.
Names must use letters, digits, hyphens and underscores. If server names
produce overlapping tool patterns, the adapter reports the ambiguity
instead of authorizing another server's tools.

The native mechanisms are documented in
[Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp),
[Claude Code permissions](https://code.claude.com/docs/en/permissions) and
[OpenCode permissions](https://opencode.ai/docs/permissions/).

## How it works

Each MCP server is a directory with an `mcp.json` that does not depend on
the agent:

```json
{
  "description": "GitHub: repositories, issues, pull requests and Actions",
  "url": "https://api.githubcopilot.com/mcp/",
  "headers": { "Authorization": "Bearer ${GITHUB_PAT}" },
  "requires": ["GITHUB_PAT"],
  "allow": ["api.githubcopilot.com"]
}
```

| Field | What it is |
|---|---|
| `description` | One line, shown by `roke mcp` |
| `command` | A **local** server: the command that starts it, which runs in the box (`npx` and `uvx` are available) |
| `url` | A **remote** server: its URL |
| `env` | Variables for a local server |
| `headers` | HTTP headers for a remote server |
| `requires` | Variables that must be set for it to start; otherwise it is left out, with a warning |
| `allow` | Network destinations it needs, added to the [allowed destinations](../../docs/network.md) |
| `services` | [Services](../services/README.md) it needs, started with it: for example the database it reads, as `postgres` does |

`command` must be a non-empty list of strings; `url` must be a non-empty
string. Use `env` only with `command` and `headers` only with `url`; both
are maps of names to strings. `requires`, `allow` and `services` are lists
of strings. roke checks these fields when it reads the definition and
reports the file and field if one is malformed.

When the project starts, roke replaces each `${VAR}` with the variable's
value from your settings, usually a token in `~/.config/roke/secrets.env`
(or the project's `secrets.env`), so tokens never go in these files.
`${VAR:-default}` works as in compose files: the services' MCP servers use
it to follow the project's settings with the same defaults as the service. An
`env` entry or a header whose variables are not set is left out, which
makes optional keys possible (see `context7`). Then each agent's `setup.sh`
translates the servers into its format: OpenCode's system configuration,
Claude Code's `--mcp-config`, and Codex's system `config.toml`.

**Security.** The box keeps the agent away from your machine, but not from
what a token allows: an MCP server with a GitHub token can do in GitHub
whatever the token allows. Give each token only the access the agent needs.

## Adding your own MCP

Copy [`_template/`](_template/) to one of these places, then fill in its
`mcp.json` and `README.md`:

- `~/.config/roke/projects/<name>/mcps/<mcp>/`: for one project;
- `~/.config/roke/mcps/<mcp>/`: for all your projects;
- `catalog/mcps/<mcp>/` in this repository: for everyone (see
  [CONTRIBUTING.md](../../CONTRIBUTING.md)).

They are looked up in that order, so yours replace a catalog MCP with the
same name; `roke mcp` marks them as `[project]` or `[yours]`. Pin the
versions of local servers (`uvx package==1.2.3`, `npx -y package@1.2.3`),
so Renovate can update them.

A local server can reach the project's services by name, for example a
database MCP with `postgresql://dev:dev@postgres:5432/shop`.
