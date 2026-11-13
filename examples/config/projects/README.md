# Projects

One directory per project, named after its **project ID**, which defaults to
the directory name: for `~/src/my-app`, `projects/my-app/`. Choose another ID
with `roke --id ID` on the first use. roke creates the configuration
when you edit it with `roke settings edit` or add services and MCP servers.
All files are optional:

```
projects/my-app/
├── project.env         settings: services, ports, Serena... and service variables
├── secrets.env         the project's secrets; never committed
├── compose.yaml        compose override: tweak a service for this project
├── AGENTS.md           private instructions for the agent in this project
├── services/<name>/    services only this project uses
└── ...                 any file the above refer to (initdb/, a Caddyfile...)
```

In compose files, refer to files in the project's directory with
`${ROKE_PROJECT_CONFIG}`; relative paths resolve against the roke
repository.

Keep Compose overrides here, outside the agent's writable project.

Full documentation:
[per-project settings](https://github.com/bameda/roke/blob/main/docs/configuration.md#per-project-settings).
