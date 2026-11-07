# My roke configuration

Personal configuration for [roke](https://github.com/bameda/roke):
global settings, the settings of each project and the configuration of each
coding agent. It lives in `~/.config/roke` (or wherever `ROKE_CONFIG_DIR`
points) and is meant to be its own private git repository.

```
~/.config/roke/
├── roke.env           global settings: agent, versions, ports, git identity...
├── secrets.env         API keys; never committed
├── AGENTS.md           personal instructions for every agent
├── agents/             each agent's own configuration
│   ├── claude/         settings.json, CLAUDE.md, agents/, commands/, skills/...
│   ├── codex/          config.toml, AGENTS.md, prompts/, skills/...
│   └── opencode/       opencode.jsonc, agents/, commands/, skills/...
├── projects/           one directory per project, named after the project's
│                       directory (see projects/README.md)
├── services/           optional: your own services, same layout as the catalog
└── mcps/               optional: your own MCP servers, same layout as the catalog
```

- **Agents**: the selected agent's directory is mounted read-only in the
  box and linked where the agent reads its configuration, so change it here,
  not from inside the agent. The agent's own state (login, sessions, files
  its UI writes) stays in the project's home volume.
- **Services**: a `services/<name>/compose.yaml` here is available to
  `roke -s <name>`, and replaces a catalog service with the same name. To
  refer to files in this directory from a compose file, use
  `${ROKE_CONFIG_DIR}` (relative paths resolve against the roke
  repository).

The agent cannot read or modify this directory, apart from the files above
that are mounted read-only: `roke` refuses to mount a project that contains
it or is inside it.

Full documentation:
[Configuration](https://github.com/bameda/roke/blob/main/docs/configuration.md).
