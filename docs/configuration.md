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
`~/.config/roke`. To use another location, set `ROKE_CONFIG_DIR`. This
way the repository can be shared and updated with `git pull` without
conflicts.

```
~/.config/roke/
├── roke.env           global settings (agent, versions, ports, git identity...)
├── secrets.env         API keys; never committed
├── AGENTS.md           your instructions for every agent
├── agents/             each agent's own configuration
│   ├── claude/
│   └── opencode/
├── projects/           one directory per project (see below)
├── services/           optional: your own services
└── mcps/               optional: your own MCP servers
```

`install.sh` creates it from the repository's `examples/config`. You can
also run `roke init` at any time to add missing files: it never
overwrites existing ones.

The agent never sees this directory: `roke` refuses to mount a project that
contains it or is inside it, so the agent cannot change its own settings.

## Keeping it in a private repository

The configuration directory is meant to be a git repository of its own.
That gives you history for your settings and lets you use them on other
machines.

**Create it** (once):

```fish
cd ~/.config/roke
git init -b main
git add -A
git status          # no secrets.env may be listed
git commit -m "chore: initial roke configuration"
```

Create an **empty, private** repository on GitHub (or any git host), then
push to it:

```fish
git remote add origin git@github.com:<you>/roke-config.git
git push -u origin main
```

**Day to day**, commit whenever you add a project or change a setting:

```fish
cd ~/.config/roke
git add projects/my-app
git commit -m "chore: add my-app project"
git push
```

**On another machine**, pass the repository's URL to the installer (or to
`roke init`). It clones it into `~/.config/roke` and adds any missing
file from the examples:

```fish
curl -fsSL https://raw.githubusercontent.com/bameda/roke/main/install.sh \
  | ROKE_CONFIG_REPO=git@github.com:<you>/roke-config.git bash
```

**What stays out of it**:

- Every `secrets.env`, the global one and the projects', is listed in the
  directory's `.gitignore`. Recreate them by hand on each machine (or log in
  from inside the agent instead of using an API key).
- The agents' logins, sessions and caches live in each project's home
  volume, not here, so they are not synced either.

Keep the repository **private**: it lists your projects and their settings.

## Global settings and secrets

- **`roke.env`**: settings for every project, such as the agent to run,
  service versions, ports or your git identity. It is loaded first, so
  per-project settings take precedence. Safe to commit.
- **`secrets.env`**: API keys and other secrets. It is loaded after
  `roke.env` and has permissions `600`. Not needed if you log in from
  inside the agent.

Both are also passed as environment variables to the box.
Each one documents its own options in comments.

## Per-project settings

Each project has its own directory in `projects/`, named after its stable
**project ID**, which defaults to the directory name: for `~/src/my-app`,
`projects/my-app/`. Use `roke --id NAME` to choose another ID. Every file
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
  ROKE_PORTS="5173"
  ROKE_SERENA=1
  POSTGRES_DB=myapp
  ```

- **`secrets.env`**: secrets only this project uses, such as the key of an
  external API it talks to. It is ignored by git, like the global one.
- **`compose.yaml`**: a Docker Compose override, merged on top of the box's
  own, to tweak a service for this project (for example, PostGIS instead of
  plain PostgreSQL).
- **`AGENTS.md`**: instructions for the agent that apply only to this
  project and that should not go into the project's own repository, because
  it belongs to your team or a client. They are added after the box's
  instructions and your personal ones.
- **`services/`**: services only this project needs, with the same layout as
  the [catalog](../catalog/services/README.md). See
  [your own services](#your-own-services).

The settings files are loaded in this order, and the last one wins:
`roke.env`, `secrets.env`, the project's `project.env`, the project's
`secrets.env`. All of them are also passed to the box as
environment variables.

The repository has [example projects](../examples/projects/README.md) for
common cases (Ansible, Helm charts, Python, Node.js, Go, Rust, Rails, Spring
Boot, Clojure) and one that uses every piece. To add a project, copy the closest one and keep only
what you need:

```fish
cp -r ~/.local/share/roke/examples/projects/python-api ~/.config/roke/projects/my-app
```

Two details:

- **Paths.** In compose files, relative paths resolve against the
  roke repository. To refer to files in the project's directory, use
  `${ROKE_PROJECT_CONFIG}`, for example `${ROKE_PROJECT_CONFIG}/initdb`.
- **Names.** IDs distinguish projects even when their directory names match.
  A collision asks you to choose another ID with `roke --id NAME`.

These files live here, and not inside the project, on purpose. A compose
file can mount any host path, so if `roke` read one from the project, the
agent could write one that mounted `/` and escaped the container the next
time you launched it. For the same reason, only `AGENTS.md` is visible
inside the box: the rest of the project's directory, secrets included, is
not.

## Project IDs and moves

The first build, session, or command that edits a project's configuration registers
its ID, absolute path and Docker Compose project name in
`~/.config/roke/.local/projects.json` (under `ROKE_CONFIG_DIR` when set).
The ID defaults to the directory name. IDs start with a letter or digit and
contain only letters, digits, dots, underscores and hyphens.

The registry stays outside the mounted project. Its directory has its own
`.gitignore` excluding all local state: sync the settings in `projects/<id>/`,
but register each machine's paths locally. Read-only commands such as
`project`, `settings`, `doctor`, `logs` and `urls` do not create or update registrations.

`roke project` lists the registered IDs and paths from any directory, marking
paths that no longer exist as `missing`. It needs no Docker connection.
`roke project show NAME` shows one identity's details. Use this inventory
to recover an ID before reattaching a moved project.

If another path already owns the ID, choose a distinct one with `--id`:

```fish
cd ~/clients/contoso/api
roke --id contoso-api
roke logs                      # the registered ID is remembered for this path
roke settings show contoso-api  # inspect its settings from any directory
```

The project ID is remembered for its directory, so session commands normally
need no `--id`. Use `roke --id NAME` to choose an ID on the first start or
reattach a moved project. From the registered directory, `roke continue`,
`roke shell` and `roke exec CMD` find the ID automatically.
The first `roke build` also registers the project automatically, using its
directory name as the default ID. The optional `--id NAME` chooses a different
initial ID. Subsequent commands remember it without a flag.
`roke settings` keeps showing the current project's settings;
`roke settings show ID` reads a registered project's settings without changing
its path, even if that path is missing. It never prints secret values.

Existing projects are adopted automatically on first use at their original
path. Their Compose names are preserved, keeping the same volumes, databases
and agent sessions. If an explicit ID differs from the old directory name,
roke copies existing settings into `projects/<id>/` when that destination
does not exist and the old name is not already registered to another project.
The original settings remain available. When the old name belongs to another
registered project, its settings and secrets are never copied automatically.
If two legacy projects shared a settings directory, choose distinct IDs and
copy the desired configuration files to the new ID's directory yourself.

Register an existing project before moving it, so roke can retain its original
Compose name. Stop its containers first, move it on the host, then use the
existing ID from the new path:

```fish
cd ~/src/api
roke shell                      # adopts this project as api; exit the shell
roke down
mv ~/src/api ~/work/backend
cd ~/work/backend
roke --id api                    # reattaches api, retaining its settings and data
roke                            # no flag needed on subsequent starts
```

The old path must no longer exist. A second copy or worktree needs a separate
ID while the original is present. A registered path cannot be given another
ID through `--id`. Moving a project never copies Docker volumes or renames
its Compose project. Deleting the local registry loses these associations;
keep it when moving code, and do not use `purge` as part of a move.

## Your own services

Services are looked up in three places, and the first one found wins:

1. the project's `services/` (`projects/<name>/services/<service>/`);
2. your `services/` (`~/.config/roke/services/<service>/`);
3. the roke [catalog](../catalog/services/README.md).

Your services work exactly like the catalog's: `roke -s <name>` and
`ROKE_SERVICES` find them, and `roke service` marks them as `[project]` or
`[yours]`. Put a service in the project when only that project needs it,
and in yours when you use it in several projects. A service with the same
name as one further down the list replaces it. See
[adding your own service](../catalog/services/README.md#adding-your-own-service).

## Agent configuration

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

If you always need something that mise does not provide, add it to the
`apt-get install` in the `Dockerfile` and run `roke build --no-cache`.

## Settings reference

The variables roke itself reads. Set them in `roke.env` (every project) or
`projects/<name>/project.env` (one project). Each service has its own variables,
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
| `ROKE_NETWORK` | `restricted` | `restricted` or `open` (`--network`); see [Network](network.md) |
| `ROKE_NETWORK_ALLOW` | — | Allowed destinations, one per line with a `# note`, or space-separated; the project's add to the global ones (`roke network add`, see [Network](network.md#allowing-destinations)) |
| `ROKE_PORTS` | — | Ports to publish on 127.0.0.1, space-separated (`-p`) |
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
| `POSTGRES_CLIENT_VERSION` | `18` | PostgreSQL client tools in the image (rebuild after changing) |
| `SERENA_VERSION` | see `roke.env` | Serena version in the image (rebuild after changing) |
| `INSTALL_SERENA` | `1` | `0` builds the image without Serena |
