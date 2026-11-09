# Projects

One directory per project, named after its **project ID**, which defaults to
the directory name: for `~/src/my-app`, `projects/my-app/`. Choose another ID
with `roke --id NAME` before starting it. To add a project, copy one of the
[example projects](https://github.com/bameda/roke/tree/main/examples/projects)
and adapt it, or create the directory with only the files you need. All of
them are optional:

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

These files live in your configuration, not in the project itself, on
purpose: a compose file can mount any host path, so if `roke` read one from
the project, the agent could write one and escape the container. For the
same reason, only `AGENTS.md` is visible inside the box; the rest of the
directory, secrets included, is not.

Full documentation:
[per-project settings](https://github.com/bameda/roke/blob/main/docs/configuration.md#per-project-settings).
