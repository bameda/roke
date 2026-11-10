# Serena

[Serena](https://github.com/oraios/serena) gives every agent language-server
tools to find definitions and references, inspect symbols and edit functions.
It also provides code navigation for agents without native language servers,
such as OpenCode 2.

## Enabling it

Serena is installed in the image. Enable it for a project, or for one session:

```fish
roke mcp add serena   # save for this project
roke --serena         # this session only
```

Use `roke mcp rm serena` to disable it. Tool approvals use the same
[`allow` and `ask` commands](../catalog/mcps/README.md#tool-approvals) as
other MCP servers. No native agent configuration is needed.

## Usage statistics

Usage reporting is disabled by default. To opt in, set
`ROKE_SERENA_USAGE_REPORTING=1` and allow `oraios-software.de`.

Dashboard news requests to that domain may still appear in
`roke network blocked`; leaving them blocked does not affect Serena's tools.

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
- **Dashboard.** Disabled by default. To use it,
  set `ROKE_SERENA_DASHBOARD=1` and open
  `http://127.0.0.1:24282/dashboard/` (the port can be changed with
  `ROKE_SERENA_DASHBOARD_PORT`).
- **Version.** Set `SERENA_VERSION` in `roke.env` and run `roke build`.
  With `INSTALL_SERENA=0`, the image is built without Serena.
