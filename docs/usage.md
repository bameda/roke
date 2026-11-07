# Usage

- [Command line](#command-line)
- [Checking the settings](#checking-the-settings)
- [Finding the services and ports](#finding-the-services-and-ports)
- [Choosing the agent](#choosing-the-agent)
- [Projects and their services](#projects-and-their-services)
- [Opening the app in your browser](#opening-the-app-in-your-browser)
- [Running other commands](#running-other-commands)
- [Git workflow](#git-workflow)

## Command line

```text
roke [-C DIR] [COMMAND] [OPTIONS]
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

**The project's box**

| Command | Description |
|---|---|
| `roke` or `roke run` | Start the agent |
| `roke continue` | Resume the agent's last session |
| `roke shell` | Open bash in the box |
| `roke exec CMD...` | Run a command in the box |
| `roke urls` | Where the app and the services are |
| `roke settings` | Every setting of the project and where it comes from |
| `roke build [--no-cache]` | Build the images; `--no-cache` also updates the agents |
| `roke down [--all]` | Stop the project's containers, or every project's; their data is kept |
| `roke purge` | Stop them and delete all the project's data |

**Agents** (see [choosing the agent](#choosing-the-agent))

| Command | Description |
|---|---|
| `roke agent` | The agents, and the one this project uses |
| `roke agent use NAME` | Use `NAME` in this project; with `--global`, by default in every project |
| `roke agent reset` | This project uses the default agent again |

**Services** (see [Services](../services/README.md))

| Command | Description |
|---|---|
| `roke service` | The services, marking the ones this project uses |
| `roke service add NAME...` | Add services to this project |
| `roke service rm NAME...` | Remove them from it; their data is kept until `roke purge` |
| `roke service upgrade [NAME...]` | Move the project's services, or some, to roke's current versions; `--major` also for major versions of services that keep data (see [Versions](../services/README.md#versions)) |

**Network** (see [Network](network.md))

| Command | Description |
|---|---|
| `roke network` | The network mode and the allowed destinations, by layer |
| `roke network add DEST` | Allow a destination in this project; with `--global`, in every project |
| `roke network rm DEST` | Stop allowing it; with `--global`, in every project |
| `roke network blocked` | What the project tried to reach and was denied |

**roke itself**

| Command | Description |
|---|---|
| `roke init [GIT_URL]` | Create the [configuration directory](configuration.md), cloning it if a URL is given |
| `roke update` | Update roke; then `roke build` rebuilds the images |
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
roke -C ~/src/shop urls     # another project, from anywhere
```

## Checking the settings

`roke settings` shows what applies to the current project and where each
value comes from: the agent, the network mode, the services, the ports, the
settings files found, and the allowed network destinations, layer by layer.

```text
Project   /home/me/src/shop
Settings  /home/me/.config/roke: roke.env secrets.env projects/shop/project.env
Agent     claude (default agent, roke.env)
Network   restricted (built-in default)
Services  postgres, mailpit
Ports     5173
Serena    on
.git      read-only

Allowed destinations (restricted mode), by layer:
  base       docker/gateway/allow.txt
             adoptium.net
             cache.ruby-lang.org
             clojars.org
             ...
  agent      agents/claude/allow.txt
             api.anthropic.com
             claude.ai
             platform.claude.com
  ...
```

`roke network` shows only the network part, and `roke agent` and
`roke service` what is available and what the project uses.

## Finding the services and ports

`roke urls` shows where everything is in the current project, with the
values that actually apply (your ports, your database name...):

```text
shop (running)

Open from your browser
  app          http://127.0.0.1:5173 (box port 5173)
  mailpit      http://127.0.0.1:18025

Reach from inside the box
  postgres     postgres:5432
               DATABASE_URL=postgres://dev:dev@postgres:5432/shop
               PGDATABASE=shop
               PGHOST=postgres
               PGPASSWORD=dev
               PGPORT=5432
               PGUSER=dev
  mailpit      mailpit:1025 · mailpit:8025
               MAILPIT_API=http://mailpit:8025/api
               SMTP_HOST=mailpit
               SMTP_PORT=1025
```

It reads the project's resolved configuration, so it needs Docker and the
box's image (`roke build`), but not the project running. Options such as
`-s` and `-p` apply, so `roke urls -s redis` shows what that run would
look like.

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
[switching between agents](../agents/README.md#switching-between-agents) for
what carries over and what does not.

## Projects and their services

Each project gets its own set of containers, named `roke-<name>-<hash>`
after its path. Two projects using `postgres` therefore get two separate
databases, and you can have several projects open at once.

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

Some services do not keep data at all (Redis, Mailpit...); each
[service's README](../services/README.md) says what it keeps.

## Opening the app in your browser

When the agent starts a dev server, it runs inside the box. To open it from
your browser, publish its port, either once with `-p` or for good with
`ROKE_PORTS` in the project's settings:

```fish
roke -p 5173
```

Then open `http://127.0.0.1:5173`. The server must listen on `0.0.0.0`, not
`localhost` (for example `vite --host 0.0.0.0`); the box's instructions
already tell the agent so.

Services with a web UI (Mailpit, RustFS, Grafana...) publish it themselves;
do not add their ports to `-p`. See the [service catalog](../services/README.md).

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
