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

Commands apply to the current directory; `-C DIR` selects another project.
Changes apply to that project unless you add `--global`.
`roke help COMMAND` shows help for a command.

Projects remember their ID. Use `--id NAME` on the first build or start to
choose one, or to [reattach a moved project](configuration.md#project-ids-and-moves).

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

`roke build` builds the box, gateway and selected services that have a
Dockerfile. It registers the project automatically; `--id NAME` optionally
chooses a different initial ID. It does not start the agent.

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
| `roke mcp show NAME` | An MCP server: its definition, tool approval policy and source, whether its secrets are set, and its README |
| `roke mcp add NAME... [--allow\|--ask]` | Give them to the agent; optionally set tool approvals. With `--global`, in every project |
| `roke mcp rm NAME...` | Take them away; with `--global`, from every project |
| `roke mcp allow NAME...` | Authorize their tools without prompting; with `--global`, by default in every project |
| `roke mcp ask NAME...` | Request confirmation for their tools; with `--global`, by default in every project |

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
| `-p`, `--port PORT` | Publish box ports on `127.0.0.1`; space-separated or repeatable |
| `--network MODE` | `restricted` or `open` |
| `--git-rw` | Let the agent write to `.git`, so it can commit |
| `--serena`, `--no-serena` | Enable or disable [Serena](serena.md) |

To keep an option for a project, use its setting instead: `roke service add`
for `-s`, and `ROKE_PORTS`, `ROKE_NETWORK`, `ROKE_GIT_RW` or `ROKE_SERENA` in
its `project.env`.

## Checking the settings

`roke settings` shows the current project's effective configuration and
where each value comes from. `roke settings show ID` inspects another
registered project from any directory, even if its path is missing.
Neither command prints secret values.

The ports listed here belong to the box. Use `roke urls` to include the
services' published ports, and `roke network` for allowed outgoing destinations.

## Editing the settings

`roke settings edit` opens a settings file of the current project in your
editor:

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

```fish
roke urls                   # published ports and addresses inside the box
roke service show postgres  # connection variables with your settings applied
```

`roke urls` reads running containers, including custom services, and shows
whether each port is local to your machine or bound to a network interface.
Host firewalls still apply to network bindings.

For a stopped project it shows configured ports. When running bindings differ
from the configuration, it shows both, so you can see what a restart will change.
`-s` and `-p` preview configuration without changing running containers.

### Colours

Set `ROKE_COLOR=auto`, `always` or `never` to control colours in catalog
READMEs. `auto` respects `NO_COLOR` and `TERM=dumb`.

## Choosing the agent

```fish
roke agent use claude --global  # default for projects without their own choice
roke agent use opencode         # this project
roke agent reset                # use the default again
roke --agent codex              # this session only
```

See [Agents](../catalog/agents/README.md) for installation, authentication
and what carries over when switching.

## Projects and their services

Each project has separate containers and volumes: two projects using
`postgres` get separate databases. Its registered ID preserves settings and
data when [moving the project](configuration.md#project-ids-and-moves).

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
must listen on `0.0.0.0`, not `localhost` (for example `vite --host 0.0.0.0`).

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

By default the project's `.git` is **read-only** inside the box. Review and
commit the agent's changes from your host:

```fish
git diff
git add <files>
git commit -s -m "feat: ..."
```

See [Security](security.md#how-it-is-locked-down) for what this protects.

To let the agent commit, use `--git-rw`, or `ROKE_GIT_RW=1` in the
project's settings. Set your git identity in `roke.env` (`GIT_AUTHOR_NAME`
and friends). Your host SSH keys are not mounted; use the host to push
and pull with them.
