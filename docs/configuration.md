# Configuration

- [The configuration directory](#the-configuration-directory)
- [Keeping it in a private repository](#keeping-it-in-a-private-repository)
- [Global settings and secrets](#global-settings-and-secrets)
- [Per-project settings](#per-project-settings)
- [Project IDs and moves](#project-ids-and-moves)
- [Your own services](#your-own-services)
- [Agent configuration](#agent-configuration)
- [Languages and tools](#languages-and-tools)
- [Settings reference](#settings-reference)

## The configuration directory

Everything personal lives outside the roke repository, in
`~/.config/roke`. To use another location, set `ROKE_CONFIG_DIR`.

```
~/.config/roke/
├── roke.env           global settings (agent, versions, ports, git identity...)
├── secrets.env         API keys; never committed
├── AGENTS.md           your instructions for every agent
├── agents/             each agent's own configuration
│   ├── claude/
│   ├── codex/
│   └── opencode/
├── projects/           one directory per project (see below)
├── services/           optional: your own services
└── mcps/               optional: your own MCP servers
```

`install.sh` creates it from the repository's `examples/config`. You can
also run `roke init` at any time to add missing files: it never
overwrites existing ones.

roke refuses to mount a project that contains this directory or is inside
it. Only selected agent configuration and instructions are mounted into
the box, read-only; settings and Compose files stay outside it.

## Keeping it in a private repository

Keep this directory in a **private** Git repository to track settings and
reuse them on other machines. Before committing, check that every
`secrets.env` is ignored; the generated `.gitignore` excludes them.

On a new machine, use `roke init GIT_URL`, or pass `ROKE_CONFIG_REPO` to the
[installer](installation.md#on-another-machine-with-your-configuration-repository).
Recreate secrets locally. Agent logins and sessions live in Docker volumes
and are not synced. The project registry stores local paths and is not
synced either.

## Global settings and secrets

- **`roke.env`**: settings for every project, such as the agent to run,
  service versions, ports or your git identity. Safe to commit.
- **`secrets.env`**: API keys and other secrets. It is loaded after
  `roke.env` and has permissions `600`. Not needed if you log in from
  inside the agent.

Both are also passed as environment variables to the box.
Each one documents its own options in comments.

## Per-project settings

Each project has its own directory in `projects/`, named after its stable
**project ID**, which defaults to the directory name: for `~/src/my-app`,
`projects/my-app/`. Use `roke --id ID` to choose another ID. Every file
in it is optional:

```
projects/my-app/
├── project.env         settings: services, ports, Serena... and service variables
├── secrets.env         the project's secrets; never committed
├── compose.yaml        compose override: tweak a service for this project
├── AGENTS.md           private instructions for the agent in this project
├── services/<name>/    services only this project uses
└── ...                 any file the above refer to (initdb/, a Caddyfile...)
```

- **`project.env`**: the project's defaults (services, ports, Serena, `.git`
  access...) plus any service variable (database name, versions, UI
  ports...). Command-line options take precedence.

  ```dotenv
  ROKE_SERVICES=postgres,mailpit
  ROKE_PORTS="5173 3000"
  ROKE_SERENA=1
  POSTGRES_DB=myapp
  ```

- **`secrets.env`**: secrets only this project uses, such as the key of an
  external API it talks to. It is ignored by git, like the global one.
- **`compose.yaml`**: a Docker Compose override, merged on top of the box's
  own, to tweak a service for this project (for example, PostGIS instead of
  plain PostgreSQL).
- **`AGENTS.md`**: private instructions for this project, added after the
  box's instructions and your personal ones.
- **`services/`**: services only this project needs, with the same layout as
  the [catalog](../catalog/services/README.md). See
  [your own services](#your-own-services).

The settings files are loaded in this order, and the last one wins:
`roke.env`, `secrets.env`, the project's `project.env`, the project's
`secrets.env`. All of them are also passed to the box as
environment variables.

The [example projects](../examples/projects/README.md) show optional
configurations for common stacks and custom services.

In Compose files, relative paths resolve against the roke repository. Use
`${ROKE_PROJECT_CONFIG}` for files in this project's configuration directory,
for example `${ROKE_PROJECT_CONFIG}/initdb`.

Settings and Compose overrides stay outside the mounted repository so the
agent cannot change what roke mounts on its next start; see [Security](security.md).

## Project IDs and moves

The first command that works on a project (a build, a session, or an edit such
as `roke service add`) registers its ID, path and Compose name. The ID defaults
to the directory name. It must start with a letter or digit and contain only
letters, digits, dots, underscores and hyphens.

`--id ID` works with any command that acts on a project's directory, so you
can choose the ID the first time, whichever command that is. This is how a
second directory with the same name gets its own ID:

```fish
cd ~/personal/api
roke service add postgres --id api-personal   # registers this directory as api-personal
roke                                          # later commands remember the ID
```

To change the ID of a registered project, rename it. Its settings move to the
new ID's directory, and its Compose name, so its containers and data, stay:

```fish
roke project rename api api-work
```

`roke project rm ID` forgets a project's registration, for one whose directory
is gone. It keeps the project's settings and its containers and data in
Docker, and prints how to delete them. Both commands refuse while the project
is running.

Use `roke project` to list registered IDs and paths, or `roke project show ID`
for one project's settings. Settings live in `projects/<id>/`; the local
registry is `~/.config/roke/.local/projects.json`. Keep that registry on this
machine when moving code; sync only configuration across machines.

Register an existing project before moving it, so roke can retain its original
Compose name. Stop its containers first, move it on the host, then use the
existing ID from the new path:

```fish
cd ~/src/api
roke shell                      # registers api if needed; exit the shell
roke down
mv ~/src/api ~/work/backend
cd ~/work/backend
roke --id api                    # reattaches api, retaining its settings and data
roke                            # no flag needed on subsequent starts
```

The old path must no longer exist. A second copy or worktree needs a separate
ID while the original is present. A registered path cannot be given another
ID through `--id`. Do not delete the registry or run `purge` as part of a
move: they would lose the identity associations or delete the data.

## Your own services

Services are looked up in three places, and the first one found wins:

1. the project's `services/` (`projects/<id>/services/<service>/`);
2. your `services/` (`~/.config/roke/services/<service>/`);
3. the roke [catalog](../catalog/services/README.md).

Your services work exactly like the catalog's: `roke -s <name>` and
`ROKE_SERVICES` find them, and `roke service` marks them as `[project]` or
`[yours]`. Put a service in the project when only that project needs it,
and in yours when you use it in several projects. A service with the same
name as one further down the list replaces it. See
[adding your own service](../catalog/services/README.md#adding-your-own-service).

## Agent configuration

Projects with the same box recipe and build settings share an image;
different settings use separate images. Run `roke build` after changing
installed agents, their versions or other build settings.

If you override `box.build` in a Compose file, also give `box.image` a
distinct tag for that custom recipe.

Two pieces of your configuration go to the agent:

- **`AGENTS.md`**, at the top of the configuration directory: your
  instructions for every agent. On every start they are added after the
  box's own instructions and before the project's private ones; see
  [instructions for the agent](../catalog/agents/README.md#instructions-for-the-agent).
- **`agents/<agent>/`**: each agent's own configuration (settings, custom
  agents, commands, skills...). Only the selected agent's directory is
  mounted, read-only, and linked where that agent reads it, so edit it on
  your host, not from inside the agent. The files the agent writes itself
  (login, sessions, UI state) stay in the project's home volume.

What goes in each agent's directory, and how it logs in, is explained in
its README: [Claude Code](../catalog/agents/claude/README.md),
[Codex](../catalog/agents/codex/README.md), [OpenCode](../catalog/agents/opencode/README.md).

## Languages and tools

The image includes:

- git, ripgrep, fd, jq and build-essential;
- python3, node and uv;
- the PostgreSQL client tools, from PostgreSQL's official repository;
- the mariadb/mysql, redis-cli and sqlite3 clients.

Everything else is installed per project with [mise](https://mise.jdx.dev).
If the project has a `mise.toml` or `.tool-versions`, `mise install` runs on
every start:

```toml
# mise.toml in the project
[tools]
node = "22"
java = "temurin-21"
clojure = "latest"
"pipx:ansible" = "latest"
```

Tools are kept in the project's home volume, so they are downloaded once
per project.
The agent can add tools itself with `mise use`. To skip the automatic
install, set `ROKE_MISE_INSTALL=0`.

## Settings reference

The variables roke itself reads. Set them in `roke.env` (every project) or
`projects/<id>/project.env` (one project). Each service has its own variables,
documented in its README in [services](../catalog/services/README.md).

| Variable | Default | Description |
|---|---|---|
| `ROKE_AGENT` | — | The coding agent to run (`--agent`); required when several are installed |
| `ROKE_SERVICES` | — | Services to start, comma-separated (`-s`) |
| `ROKE_COLOR` | `auto` | Colours in `roke ... show`: `auto` colours a terminal unless `NO_COLOR` is set or `TERM` is `dumb`; `always`; `never` |
| `ROKE_SERENA_USAGE_REPORTING` | `0` | 1 = let Serena send its anonymous usage statistics (allow `oraios-software.de` too); see [Serena](serena.md#usage-statistics) |
| `ROKE_EDITOR` | `$VISUAL`, `$EDITOR` | The editor `roke settings edit` opens, such as `code --wait` |
| `ROKE_PARALLEL_AGENTS` | — | Agents that may run at the same time in the project, comma-separated; see [several agents at once](../catalog/agents/README.md#several-agents-at-once) |
| `ROKE_MCPS` | — | MCP servers, comma-separated; the project's add to the global ones (`roke mcp add`) |
| `ROKE_MCP_APPROVALS` | — | Comma-separated `NAME=allow` or `NAME=ask` preferences, managed with `roke mcp allow/ask/reset`; project entries override global entries per name |
| `ROKE_NETWORK` | `restricted` | `restricted` or `open` (`--network`); see [Network](network.md) |
| `ROKE_NETWORK_ALLOW` | — | Allowed destinations, one per line with a `# note`, or space-separated; the project's add to the global ones (`roke network add`, see [Network](network.md#allowing-destinations)) |
| `ROKE_PORTS` | — | Ports to publish on 127.0.0.1, separated by spaces or commas (`-p`); `HOST_PORT:PORT` and `IP:HOST_PORT:PORT` choose the address |
| `ROKE_GIT_RW` | `0` | `1` mounts `.git` read-write (`--git-rw`) |
| `ROKE_SERENA` | `0` | `1` enables Serena (`--serena`) |
| `ROKE_SERENA_DASHBOARD` | `0` | `1` publishes Serena's web dashboard |
| `ROKE_SERENA_DASHBOARD_PORT` | `24282` | Host port for that dashboard |
| `ROKE_SERENA_CODEMODE` | `0` | OpenCode only: `1` exposes Serena's tools through Code Mode |
| `ROKE_MISE_INSTALL` | `1` | `0` skips `mise install` on start |
| `ROKE_HOST_UID` / `ROKE_HOST_GID` | your UID/GID | Container user; `0` for rootless Docker |
| `ROKE_CONFIG_DIR` | `~/.config/roke` | Configuration directory (set it in your shell, not in these files) |
| `ROKE_PROJECT_CONFIG` | set by `roke` | The project's configuration directory, for paths in compose files |
| `ROKE_AGENTS` | `claude codex opencode` | Agents installed in the image (rebuild after changing) |
| `ROKE_AGENT_VERSIONS` | — | Agent versions as `agent=version` pairs (rebuild after changing) |
| `POSTGRES_CLIENT_VERSION` | see [`Dockerfile`](../Dockerfile) | PostgreSQL client tools in the image (rebuild after changing) |
| `SERENA_VERSION` | see [`Dockerfile`](../Dockerfile) | Serena version in the image (rebuild after changing) |
| `INSTALL_SERENA` | `1` | `0` builds the image without Serena |
