# Usage

- [Command line](#command-line)
- [Checking the settings](#checking-the-settings)
- [Editing the settings](#editing-the-settings)
- [Finding the services and ports](#finding-the-services-and-ports)
- [Choosing the agent](#choosing-the-agent)
- [Projects and their services](#projects-and-their-services)
- [Opening the app in your browser](#opening-the-app-in-your-browser)
- [Running other commands](#running-other-commands)
- [Git workflow](#git-workflow)

## Command line

```text
roke [COMMAND] [OPTIONS]
```

roke works on the project in the current directory, or in `DIR` with
`-C DIR`. Commands follow three rules, so you can guess the ones you do not
remember:

1. **What you do with the project's box is a verb:** `roke shell`,
   `roke down`, `roke build`.
2. **What you manage is a noun and a verb:** `roke service add`,
   `roke agent use`, `roke network add`. The noun alone lists it:
   `roke service`.
3. **Changes apply to the current project; `--global`, to every project.**

`roke help` lists every command, and `roke help COMMAND` one of them.
`roke version` (or `roke --version`) shows the installed roke version from
any directory, without Docker or project configuration.

`-C DIR` chooses the project's directory, for example `roke settings -C DIR`.
The project ID is remembered for its directory. Use `roke --id acme-api`
to choose an ID on the first start or reattach a moved project. Subsequent
commands such as `roke continue`, `roke shell` and `roke exec CMD` find the
ID automatically. To inspect another project's
settings, use `roke settings show ID`. See
[project IDs and moves](configuration.md#project-ids-and-moves).
For `exec`, put roke options before the command to execute; for `logs`, put
them before the arguments passed to Compose.

**The project's box**

`roke run` is the explicit form of `roke`: both start a new agent session.

| Command | Description |
|---|---|
| `roke` or `roke run` | Start the agent |
| `roke continue` | Resume the agent's last session |
| `roke shell` | Open bash in the box |
| `roke exec CMD...` | Run a command in the box |
| `roke urls` | Where the app and the services are |
| `roke logs [OPTIONS] [SERVICE...]` | Show project logs; passes arguments to [`docker compose logs`](https://docs.docker.com/reference/cli/docker/compose/logs/) |
| `roke settings` | The project's settings and where they come from |
| `roke settings edit [FILE]` | Edit them in your editor; see [editing the settings](#editing-the-settings) |
| `roke settings show ID` | The effective settings of a registered project, from any directory |
| `roke build [--no-cache]` | Build the images; `--no-cache` also updates the agents |
| `roke down [--all]` | Stop the project's containers, or every project's; their data is kept |
| `roke purge` | Stop them and delete all the project's data |
| `roke doctor [--yaml]` | Check prerequisites and report what needs fixing; `--yaml` produces a shareable report. Returns nonzero when something needs attention |

Projects with the same box recipe and build arguments share an image. roke
automatically assigns different image tags to different build settings, so
building another project's agent versions does not replace yours. The gateway
image is shared. `roke build` also
builds selected services that have a Dockerfile and applies the current
project's configuration. The first build registers the project automatically,
using its directory name as the default ID. The optional `--id NAME` chooses
a different initial ID, for example `roke build --id acme-api`.

If Compose rejects a service name, `roke logs` shows the available names from
the resolved Compose configuration. This includes the gateway, selected
services and any services added in the project's `compose.yaml`.

**Projects** (see [project IDs and moves](configuration.md#project-ids-and-moves))

| Command | Description |
|---|---|
| `roke project` | List registered IDs and paths on this machine, marking missing directories; works from anywhere without Docker |
| `roke project show ID` | Show a registered project's path, settings directory and Compose name |

**Agents** (see [choosing the agent](#choosing-the-agent))

| Command | Description |
|---|---|
| `roke agent` | The agents, and the one this project uses |
| `roke agent show NAME` | An agent: whether it is installed and used, what it allows, and its README |
| `roke agent use NAME` | Use `NAME` in this project; with `--global`, by default in every project |
| `roke agent reset` | This project uses the default agent again |

**Services** (see [Services](../catalog/services/README.md))

| Command | Description |
|---|---|
| `roke service` | The services, marking the ones this project uses |
| `roke service show NAME` | A service in this project: its version, address, web UI and variables, and its README |
| `roke service add NAME...` | Add services to this project |
| `roke service rm NAME...` | Remove them from it; their data is kept until `roke purge` |
| `roke service upgrade [NAME...]` | Move the project's services, or some, to roke's current versions; `--major` also for major versions of services that keep data (see [Versions](../catalog/services/README.md#versions)) |

**MCP servers** (see [MCP servers](../catalog/mcps/README.md))

| Command | Description |
|---|---|
| `roke mcp` | The MCP servers, marking the ones this project uses |
| `roke mcp show NAME` | An MCP server: its definition, whether its secrets are set, and its README |
| `roke mcp add NAME...` | Give them to the agent in this project; with `--global`, in every project |
| `roke mcp rm NAME...` | Take them away; with `--global`, from every project |

**Network** (see [Network](network.md))

| Command | Description |
|---|---|
| `roke network` | The network mode and the allowed destinations, by layer |
| `roke network add DEST` | Allow a destination in this project; with `--global`, in every project; `--note TEXT` says what it is for |
| `roke network rm DEST` | Stop allowing it; with `--global`, in every project |
| `roke network blocked` | What the project tried to reach and was denied |

**roke itself**

| Command | Description |
|---|---|
| `roke init [GIT_URL]` | Create the [configuration directory](configuration.md), cloning it if a URL is given |
| `roke version` or `roke --version` | Show the installed roke version |
| `roke update [--stable\|--main]` | Update within the saved channel, or switch it; then `roke build` rebuilds the images |
| `roke help [COMMAND]` | The help |

**Options** for `run`, `continue`, `shell` and `exec`, for this time only
(`-s` and `-p` also apply to `roke urls`):

| Option | Description |
|---|---|
| `-a`, `--agent NAME` | Use another agent |
| `-s`, `--services LIST` | Start these services instead, comma-separated |
| `-p`, `--port PORT` | Publish a port of the box on `127.0.0.1` (repeatable) |
| `--network MODE` | `restricted` or `open` |
| `--git-rw` | Let the agent write to `.git`, so it can commit |
| `--serena`, `--no-serena` | Enable or disable [Serena](serena.md) |

To keep an option for a project, use its setting instead: `roke service add`
for `-s`, and `ROKE_PORTS`, `ROKE_NETWORK`, `ROKE_GIT_RW` or `ROKE_SERENA` in
its `project.env`.

Examples:

```fish
roke continue               # resume the agent's last session
roke exec -s postgres psql  # a single command, with a service
roke urls -C ~/src/shop     # another project, from anywhere
```

## Checking the settings

`roke settings` inspects the current project. `roke settings show ID` uses a
registered identity instead, from any directory, without changing its path
or registration. It also works when the registered directory is missing.

`roke settings` shows what applies to the current project and where each
value comes from: the agent, the network mode, the services, the ports, the
MCP servers, the settings files found, and the allowed network
destinations, layer by layer.

```text
Project   /home/me/src/shop (running)
ID        shop
Compose   roke-shop-f39b23e3
Settings  /home/me/.config/roke: roke.env secrets.env projects/shop/project.env
Agent     claude (default agent, roke.env)
Network   restricted (built-in default): 29 destinations allowed (roke network)
Services  postgres 18, mailpit v1.33.0
MCPs      github
Secrets   GITHUB_PAT (global)
Box ports 5173 (all published ports: roke urls)
Serena    on
.git      read-only
```

`Box ports` lists the configured ports of the box. `roke urls` includes the
services' published ports too. `Compose` identifies the project in Docker.

`roke network` shows the allowed outgoing destinations, and `roke agent` and
`roke service` what is available and what the project uses.

## Editing the settings

`roke settings edit` opens a settings file of the current project in your
editor, creating it from a commented template the first time:

| Command | File |
|---|---|
| `roke settings edit` | The project's `project.env`; with `--global`, `roke.env` |
| `roke settings edit secrets` | The project's `secrets.env` (always readable only by you); with `--global`, yours |
| `roke settings edit compose` | The project's own `compose.yaml` |
| `roke settings edit instructions` | The project's private `AGENTS.md`; with `--global`, yours |
| `roke settings edit tools` | The project's `mise.toml`, in its repository (see [Languages and tools](configuration.md#languages-and-tools)) |

The editor is `ROKE_EDITOR` (in `roke.env`), then `$VISUAL`, then `$EDITOR`,
then `nano` or `vi`; `ROKE_EDITOR="code --wait"` works too. When you close
an `.env` file, roke checks it: settings files are read by bash, and a
syntax error, such as an unclosed quote, would stop roke until fixed.

## Finding the services and ports

`roke urls` shows the ports published by the current project's running
containers, their destinations and whether they bind only to your machine
or also to a network interface:

```text
shop (running)

Published ports (running containers)
  app          http://127.0.0.1:5173 → box:5173 (tcp, local only)
  mailpit      http://127.0.0.1:18025 → mailpit:8025 (tcp, local only)

Reach from inside the box
  postgres     postgres:5432
  mailpit      mailpit:1025 · mailpit:8025

The variables each service gives the box: roke service show NAME
```

It includes ports published by custom containers in the project's
`compose.yaml`. HTTP addresses are shown for the app and forwarded service
UIs; other bindings use `tcp://` or `udp://` addresses. `network access`
means the port binds to a non-loopback interface; host firewalls still apply.

If the project is stopped, it shows configured ports instead. If the running
bindings differ from the current configuration, a separate `Configured ports
(next start)` section shows the expected bindings after restarting. Options
such as `-s` and `-p` apply to that configuration, so `roke urls -s redis`
shows what that run would look like without changing running containers.
Docker and Compose are required; the project does not need to be running.

The variables each service gives the box, with your settings applied, are
in `roke service show NAME`, followed by the service's README:

```text
postgres: PostgreSQL · postgres:5432 · DATABASE_URL, PGHOST/PGUSER/PGPASSWORD/PGDATABASE

In this project: used
  POSTGRES_VERSION=18 (pinned)
  inside the box: postgres:5432
  variables in the box:
    DATABASE_URL=postgres://dev:dev@postgres:5432/shop
    PGDATABASE=shop
    PGHOST=postgres
    PGPASSWORD=dev
    PGPORT=5432
    PGUSER=dev
  ...
```

### Colours

`roke service show`, `roke mcp show` and `roke agent show` print each entry's
README rendered for the terminal: headings, emphasis, code, links, lists
and tables in colour, through your pager when it does not fit. Colours
follow `ROKE_COLOR` (in `roke.env`, or for one command): `auto`, the default,
colours a terminal unless `NO_COLOR` is set or `TERM` is `dumb`; `always`
colours even when piped (for example to `less -R`); `never` prints plain
Markdown.

```fish
ROKE_COLOR=never roke service show postgres
```

## Choosing the agent

No agent is the default. The one that runs comes from, in order of
precedence:

1. `--agent NAME` on the command line;
2. `ROKE_AGENT` in the project's `project.env`;
3. `ROKE_AGENT` in `roke.env`.

If none is set and the image has a single agent, that one runs.
`roke agent` shows which agent will run in the current project and where
that choice comes from.

To change the agent without editing files:

```fish
roke agent use claude --global  # the default (roke.env)
roke agent use opencode         # this project's own (project.env)
roke agent reset                # this project uses the default again
```

All the agents of a project share its home volume, so you can switch
between them freely: each keeps its own login and sessions there. See
[switching between agents](../catalog/agents/README.md#switching-between-agents) for
what carries over and what does not.

## Projects and their services

Each project gets its own set of containers and volumes. Its Compose name
starts as `roke-<name>-<hash>`, calculated from the original path, and is then
stored in the local ID registry. Reattaching the ID after a move keeps that
name and its data. Two projects using `postgres` get separate databases.

When you exit the agent, the project's services **keep running**, so the
next session starts instantly with the same data. Stop them when you are
done:

| Command | Services | Data (databases, buckets, queues...) and the box's home |
|---|---|---|
| exit the agent | keep running | kept |
| `roke down` | stopped and removed | kept |
| `roke purge` | stopped and removed | **deleted** |

The box's home is the project's own volume with the agents' logins and
sessions and the tools installed with mise, so after `roke purge` you log in
again and tools are downloaded again.

`roke down --all` attempts to stop every listed project, even if one fails.
It returns a nonzero status and lists the failed projects when any could not
be stopped. A failed Docker query is reported as an error.

Some services do not keep data at all (Redis, Mailpit...); each
[service's README](../catalog/services/README.md) says what it keeps.

## Opening the app in your browser

When the agent starts a dev server, it runs inside the box. To open it from
your browser, publish its port, either once with `-p` or for good with
`ROKE_PORTS` in the project's settings:

```fish
roke -p "5173 3000"
```

Or set them in `roke settings edit`:

```dotenv
ROKE_PORTS="5173 3000"
```

Then open `http://127.0.0.1:5173` or `http://127.0.0.1:3000`. The server
must listen on `0.0.0.0`, not `localhost` (for example `vite --host 0.0.0.0`);
the box's instructions already tell the agent so.

Services with a web UI (Mailpit, RustFS, Grafana...) publish it themselves;
do not add their ports to `-p`. See the [service catalog](../catalog/services/README.md).

## Running other commands

```fish
roke shell      # interactive bash in the box
roke exec psql  # one command, then exit
```

The shell has the same environment as the agent: the project's tools, the
services' variables (`DATABASE_URL`...) and network access to the services
by name. It is the place to check things by hand or to run what the agent
would run.

## Git workflow

By default the project's `.git` is **read-only** inside the box. The agent
can run `git status`, `git diff` or `git log`, but it cannot commit,
switch branches, stash or change the git configuration. You review its
changes and commit them from your host:

```fish
git diff
git commit -am "feat: ..."
```

This also protects your host: hooks or settings planted in `.git` would run
the next time you used git outside the box (see [Security](security.md)).

To let the agent commit, use `--git-rw`, or `ROKE_GIT_RW=1` in the
project's settings. Set your git identity in `roke.env` (`GIT_AUTHOR_NAME`
and friends). There are no SSH keys in the box, so `git push` and
`git pull` always happen on the host.
