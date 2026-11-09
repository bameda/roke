# Coding agents

The coding agents roke can run. Each one lives in its own directory
under `agents/`, and none is the default: you choose one with `ROKE_AGENT`
(in `roke.env` or a project's `project.env`) or with `roke --agent`.

See [switching between agents](#switching-between-agents) to change from
one to another.

| Agent | Command | Docs |
|---|---|---|
| Claude Code | `claude` | [claude](claude/README.md) |
| Codex CLI | `codex` | [codex](codex/README.md) |
| OpenCode 2 | `opencode` | [opencode](opencode/README.md) |

Everything else is the same whichever agent runs: the isolation, the
services, the tools installed with mise, Serena, the read-only `.git` and
the project settings.

## Choosing and installing agents

```dotenv
# ~/.config/roke/roke.env
ROKE_AGENT=claude                     # the agent to run
ROKE_AGENTS="claude codex opencode"   # agents in the image (rebuild after changing)
ROKE_AGENT_VERSIONS="opencode=2.2.5"  # optional versions (rebuild after changing)
```

- **`ROKE_AGENT`** is required when the image has more than one agent. A
  project can use a different one in its `project.env`, and `--agent`
  overrides both for one run.
- **`ROKE_AGENTS`** lists the agents installed in the image, all of them by
  default. Keep only the ones you use to make the image smaller.
- **`ROKE_AGENT_VERSIONS`** pins versions as `agent=version` pairs. Each
  agent's README explains which values it accepts and its default.

## Switching between agents

There is a default agent, and any project can have its own, so different
projects can use different agents with the same configuration. Switching
takes one command:

```fish
roke agent use claude --global  # the default, for projects without their own
roke agent use opencode         # this project's own agent
roke agent reset                # this project uses the default again
roke --agent opencode           # this run only
roke agent                      # the agents, and which one runs here and why
```

`roke agent use --global` writes `ROKE_AGENT` in `roke.env`, and `roke agent use` in
the project's `project.env`; you can also edit them by hand. The agent must
be in the image: if it is not, add it to `ROKE_AGENTS` and run
`roke build`.

**What carries over when you switch:**

- the project, its services and their data, its tools (mise) and Serena;
- the box's instructions, your `AGENTS.md` and the project's private one,
  which every agent receives;
- the project's own instructions, if they are in an `AGENTS.md`: Codex and
  OpenCode read it, and so does Claude Code when the project has no
  `CLAUDE.md`.
  Prefer `AGENTS.md` in projects where you use several agents.

**What does not:**

- **Sessions and history.** Each agent keeps its own; a conversation started
  with one cannot be continued with another. Start the new one with a short
  summary of where you were, or ask the first agent to write one into the
  project before switching.
- **Login.** Each agent has its own, made once.
- **Agent-specific configuration** in `~/.config/roke/agents/<agent>/`:
  model, permissions, your own MCP servers, custom commands and skills use
  each agent's format, so configure each agent separately.

## Several agents at once

Each project runs one agent at a time by default. To have two agents work
on the same project at the same time, one in each terminal, list them in the
project's `project.env`:

```dotenv
ROKE_PARALLEL_AGENTS=claude,codex
```

The project's network then allows the destinations of all of them, whichever
starts, so starting the second does not change the network under the first.
Without that line, each agent gets only its own destinations: working with a
single agent keeps the network as narrow as possible.

roke never cuts off a session that is running: if starting another one would
recreate a container the first is using (the gateway, because of a
different agent or different `-p` ports, or a service), it refuses and says
why. Finish the first session, or stop the project with `roke down`, then
start again.

Both agents edit the same files and share the services and the network, so
give them tasks in different parts of the project, and do not start two dev
servers on the same port. For fully separate work, give the second agent a
[git worktree](https://git-scm.com/docs/git-worktree), which roke treats as
a project of its own, with its own services and data:

```fish
git worktree add ../shop-experiment -b experiment
cd ../shop-experiment
roke --agent codex
```

Each worktree has its own registered ID. The default is its directory name;
if that ID is already taken, choose one with `roke --id shop-experiment`.
Settings live in `~/.config/roke/projects/<id>/`. See
[project IDs and moves](../../docs/configuration.md#project-ids-and-moves).

## Instructions for the agent

On every start, the box builds the agent's instructions from four parts, in
this order:

1. the box's own instructions, [`AGENTS.md`](AGENTS.md) in this directory:
   the container, the services, the read-only `.git`...;
2. the agent's own, `catalog/agents/<agent>/AGENTS.md`, if it has one;
3. yours, `~/.config/roke/AGENTS.md`, for every agent, followed by the
   `AGENTS.md` in `~/.config/roke/agents/<agent>/`, if any, for this agent;
4. the project's private ones, `~/.config/roke/projects/<name>/AGENTS.md`.

Each agent's `setup.sh` puts the result where that agent reads it. The
project's own `AGENTS.md` or `CLAUDE.md`, in its repository, is read by the
agent as usual.

## Adding an agent

Copy [`_template/`](_template/) to `catalog/agents/<name>/` and fill in its files:

| File | Runs | Does |
|---|---|---|
| `install.sh` | at build time, as root | Installs the agent. Receives the version from `ROKE_AGENT_VERSIONS`, or `default` |
| `setup.sh` | on every start, as the box's user, sourced by the entrypoint | Links your configuration, places the instructions, registers Serena, and sets `AGENT_COMMAND` |
| `AGENTS.md` | — | Optional: instructions for this agent only |
| `allow.txt` | — | Destinations the agent needs in restricted network mode: its API, its login (see [Network](../../docs/network.md)) |
| `expected.txt` | — | Optional: destinations the agent looks up but does not need, such as telemetry, as `DOMAIN  REASON` lines; `roke network blocked` marks them as blocked on purpose |
| `README.md` | — | How to use it; its first line is shown by `roke agent` |

`setup.sh` receives these variables and helpers:

| Name | What it is |
|---|---|
| `AGENT_CONFIG` | Your configuration for this agent (`~/.config/roke/agents/<name>/`), mounted read-only; may be empty |
| `AGENT_INSTRUCTIONS` | The combined instructions file described above |
| `SERENA_ENABLED` | `1` when Serena is enabled for the project |
| `serena_command CONTEXT` | Sets the array `SERENA_CMD` to the command that starts Serena's MCP server for the project |
| `python3 /opt/roke/agents/mcp.py FORMAT` | Prints the project's [MCP servers](../mcps/README.md) in an agent's format (`opencode`, `claude` or `codex`); add a format there for a new agent |
| `roke_link_config SRC DEST` | Links every entry of `SRC` into `DEST`, keeping `DEST` writable for the agent's own files |
| `ROKE_RUNTIME` | A per-container directory for generated files |

and must set:

| Name | What it is |
|---|---|
| `AGENT_COMMAND` | Array: the command that starts the agent, for example `(claude)` |
| `AGENT_ARGS` | Optional array: arguments added whenever the agent runs, for example an MCP configuration file |
| `AGENT_CONTINUE` | Optional array: arguments that resume the last session, for `roke continue`; for example `(--continue)` |

Then add it to `ROKE_AGENTS` and run `roke build`.
