# Serena

[Serena](https://github.com/oraios/serena) is an MCP server that runs the
project's language servers and gives the agent symbol-level tools: find a
definition, list references, inspect a file's structure or replace the body
of a specific function. In large repositories it saves a lot of context
compared to `grep` and reading whole files. It works with every agent, and
is especially useful with those that do not run language servers themselves,
such as OpenCode 2.

## Enabling it

Serena is installed in the image, under `/opt` and out of the agent's reach,
and **enabled per project**:

```fish
roke --serena                      # once
```

To enable it for good, add `ROKE_SERENA=1` to the project's settings,
`~/.config/roke/projects/<name>/project.env`.

When enabled, the box registers Serena as an MCP server for the selected
agent, pinned to the current project and with the Serena context that suits
that agent. It is done on every start, so there is nothing to add to your
agent's configuration. Each [agent's README](../catalog/agents/README.md) explains
how it is registered there.

## Details

- **Language servers.** Serena downloads many of them by itself and keeps
  them in `~/.serena`, in the project's home volume, so only the first run
  of each project is slow.
  Some need the language's runtime: for Java or Clojure, declare `java` and
  `clojure` in the project's `mise.toml`. See Serena's
  [language support](https://oraios.github.io/serena/01-about/020_programming-languages.html).
- **Project data.** Serena stores `project.yml` and its "memories" (notes
  the agent writes about the project) in `.serena/` inside the project.
  Decide whether to commit it or add it to `.gitignore`.
- **Dashboard.** Disabled, since there is no browser in the box. To use it,
  set `ROKE_SERENA_DASHBOARD=1` and open
  `http://127.0.0.1:24282/dashboard/` (the port can be changed with
  `ROKE_SERENA_DASHBOARD_PORT`).
- **Version.** Set `SERENA_VERSION` in `roke.env` and run `roke build`.
  With `INSTALL_SERENA=0`, the image is built without Serena.
