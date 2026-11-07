# Security

roke limits what the agent can touch on your machine. It is not a
full sandbox: read what it protects and what it does not.

- [The agent is not trusted](#the-agent-is-not-trusted)
- [What the container sees](#what-the-container-sees)
- [How it is locked down](#how-it-is-locked-down)
- [What it does NOT protect](#what-it-does-not-protect)

## What the container sees

| Path in the container | Comes from | Access |
|---|---|---|
| `<project path>` (same as on the host) | the project | read-write |
| `<project>/.git` | the project | **read-only** (unless `--git-rw`) |
| `/home/dev` | the project's own `home` volume | read-write; the box's home |
| `/run/roke/agent-config` | `~/.config/roke/agents/<agent>` | read-only |
| `/run/roke/user-AGENTS.md` | `~/.config/roke/AGENTS.md`, if any | read-only |
| `/run/roke/project-AGENTS.md` | the project's `AGENTS.md` in your configuration, if any | read-only |
| `/opt/roke/agents` | the repository's `agents/` (setup scripts, the box's instructions) | read-only |

Nothing else from your host is mounted: not your `$HOME`, not your SSH keys,
not your other projects, not your roke settings or secrets.

Each project has its own home volume, shared with nothing else: not with
other projects, not with your host. It holds the agents' logins and
sessions, the tools installed with mise and the caches (npm, maven,
cargo...). An agent working on one project therefore cannot read another
project's sessions, nor leave anything behind (a shell profile, an MCP
server in the agent's state, a poisoned cache) that another project would
pick up. `roke purge` deletes it along with the project's other data.

## The agent is not trusted

roke assumes the agent may misbehave, through a bug, a prompt injection in
something it reads, or a compromised dependency, and does not rely on the
agent's own safeguards. Several agents ship their own sandbox or permission
prompts; inside the box they are at most an extra layer, and the limits
described here hold whether they work or not. Everything that keeps the
agent away from your machine is enforced by Docker, from outside the
container, with files the agent cannot modify.

## How it is locked down

- The container runs with **your UID/GID** (files it creates are yours),
  **without `sudo`**, without Linux capabilities (`cap_drop: ALL`) and with
  `no-new-privileges`.
- **The Docker socket is never mounted**, so the agent cannot start
  containers or reach the Docker daemon.
- **`.git` is read-only** by default. Otherwise the agent could plant hooks,
  or settings such as `core.fsmonitor`, that would run on your host the next
  time you used git there.
- **Settings live outside the project.** `roke` only reads compose files
  and settings from `~/.config/roke` and from its own repository, and
  refuses to mount a project that contains either of them. A compose file
  written by the agent could otherwise mount any host path.
- **The network is restricted by default.** The box only reaches the
  destinations you allow, and the services have no route out at all; see
  [Network](network.md).
- **Published ports** listen on `127.0.0.1` by default, never on your
  network. Only a full mapping you write yourself (such as `-p 3000:3000`
  or `ports:` in a compose file) can change that.

## What it does NOT protect

- **Tokens you give to MCP servers.** An MCP server can do outside the box
  whatever its token allows, for example in GitHub. Give each token only
  the access the agent needs; see [MCP servers](../mcps/README.md).
- **Allowed destinations.** In restricted mode, the box can still reach
  the destinations you allow, and in open mode anything at all. See
  [Network](network.md).
- **What you run on the host afterwards.** The agent can edit any file in
  the project: `package.json`, `Makefile`, `.envrc`, scripts, tests... If
  you later run them outside the box, you run whatever it wrote. Review the
  diff first.
- **The `docker` group.** Being in it is equivalent to being root on the
  host. [Rootless Docker](installation.md#rootless-docker) avoids that.
- **Secrets you give it.** API keys in `secrets.env` and the agents' logins
  are available inside the box, so the agent can read them. Use keys with
  spending limits where your provider offers them.
