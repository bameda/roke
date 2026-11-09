# roke

> 🏝️ *Roke is the island of wizards in Ursula K. Le Guin's Earthsea: a place
> where power is learned and kept, guarded by a wind that lets no one in
> uninvited.*

Run coding agents, such as [Claude Code](catalog/agents/claude/README.md),
[Codex](catalog/agents/codex/README.md) or [OpenCode](catalog/agents/opencode/README.md),
inside a Docker container that **only sees the project you are working on**.
Your `$HOME`, SSH keys, dotfiles and every other project stay out of the
agent's reach.

- **Any agent**: choose the agent per project or per run. Agents are
  pluggable, so adding another one is a matter of adding a directory.
- **Isolated**: the project is the only host directory the agent can write
  to. Its `.git` is read-only, and the container runs without `sudo`,
  without capabilities and without access to Docker.
- **Services on demand**: databases, caches, queues, test email, tracing,
  API mocks, a simulated Kubernetes API and more, each in its own
  container, with separate data for every project.
- **MCP servers**: GitHub, Context7 and others, managed like the services
  and given to whichever agent you use, in its own format.
- **Restricted network**: by default, the agent only reaches the
  destinations you allow, with any protocol; `roke network blocked` shows what was
  denied and `roke network add` opens it.
- **Per-project tools**: languages and tools are installed with
  [mise](https://mise.jdx.dev) from the project's `mise.toml`.
- **Semantic code navigation**, optionally, with
  [Serena](https://github.com/oraios/serena).
- **Shareable**: your settings live in `~/.config/roke`, outside this
  repository, and can be kept in a private repository of their own.

## Quick start

1. Install Docker with the Compose plugin: see
   [Installation](docs/installation.md) for Arch, Debian, Ubuntu and others.
2. Install roke:

   ```fish
   curl -fsSL https://raw.githubusercontent.com/bameda/roke/main/install.sh | bash
   ```

3. Choose your default agent: `roke agent use claude --global`, `codex` or
   `opencode`.
4. Start it in a project, building the image the first time:

   ```fish
   cd ~/src/my-project
   roke build
   roke
   ```

   `build` prepares the images; `roke` opens the agent. If the agent needs
   authentication with its provider, follow its
   [instructions](catalog/agents/README.md). roke itself has no account.

Follow [First steps](docs/first-steps.md) to continue sessions, add services
and MCP tools, allow network destinations and start another project.

## Everyday use

```fish
roke                        # start the agent in the current project
roke continue               # resume its last session
roke -s postgres -p 5173    # this time with a database and the dev server's port
roke shell                  # bash inside the box
roke exec psql              # a single command inside the box
roke urls                   # where the app and the services are
roke project                # registered project IDs and their paths
roke settings show acme-api # another registered project's settings, from anywhere
roke service show postgres  # a service: version, address, variables, docs
roke settings edit          # edit the project's settings in your editor
roke service add postgres   # add a service to the project, for good
roke mcp add context7       # give the agent library documentation tools
roke agent use opencode     # use another agent in the project, for good
roke network blocked        # what the network denied
roke down                   # stop the project's containers (keeps data)
roke help                   # every command
```

Each project keeps its services, ports and other options in its own
directory, `~/.config/roke/projects/<id>/`. The ID defaults to the directory
name; use `roke --id NAME` to resolve a collision or reattach a moved project.
See [project IDs and moves](docs/configuration.md#project-ids-and-moves).

## Documentation

| Guide | What you will find |
|---|---|
| [Installation](docs/installation.md) | Docker on each distribution, installing and updating roke, rootless Docker |
| [First steps](docs/first-steps.md) | Start in your project, continue sessions and add services, MCP tools and network access |
| [Usage](docs/usage.md) | Every `roke` option, ports, git workflow, stopping and resetting |
| [Agents](catalog/agents/README.md) | The available agents, choosing one, how each logs in and is configured, adding another |
| [Configuration](docs/configuration.md) | `~/.config/roke`, keeping it in a private repo, per-project settings, tools, settings reference |
| [Services](catalog/services/README.md) | The service catalog, how to use each one and how to add your own |
| [MCP servers](catalog/mcps/README.md) | The MCP catalog, how they reach each agent and how to add your own |
| [Example projects](examples/projects/README.md) | Ready-made configurations: Ansible, Helm, Python, Node.js, Go, Rust, Rails, Spring Boot, Clojure |
| [Serena](docs/serena.md) | Semantic code navigation and editing |
| [Network](docs/network.md) | How the pieces fit, restricted and open mode, allowing destinations |
| [Security](docs/security.md) | What the container can and cannot reach |
| [Troubleshooting](docs/troubleshooting.md) | Common problems, known limitations and maintenance |
| [Development](docs/development.md) | Running the tests and trying changes |

## Security in a nutshell

The agent can read and write the project, but nothing else on your
machine, and by default it only reaches the network destinations you allow.
Anything it writes runs on your host if you later run it there: review the
diff before running the project's scripts or committing. Read
[Security](docs/security.md) and [Network](docs/network.md) for the
details.

## Contributing

Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md). To report
a security problem, follow [SECURITY.md](SECURITY.md) instead of opening an
issue.

## License

[MIT](LICENSE) © David Barragán Merino
