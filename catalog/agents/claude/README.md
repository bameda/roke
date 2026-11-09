# Claude Code (`claude`)

[Claude Code](https://code.claude.com/docs/en/overview), Anthropic's coding agent.

## Install and update

Installed from Anthropic's signed apt repository, whose key is checked
against its published fingerprint. The version is
`ROKE_AGENT_VERSIONS="claude=..."`:

- `stable` (default): about a week behind, skipping releases with major
  regressions;
- `latest`: every release as soon as it ships;
- an exact package version from the latest channel.

Run `roke build --no-cache` to fetch a newer release of the channel. Claude Code's
own updates are disabled (`DISABLE_UPDATES`), since the image decides the
version.

## Log in

Run `claude` and follow the login prompts: it shows a URL to open in your
browser, on your host, and asks you to paste the code back into the
terminal. The credentials are kept in the project's home volume (`~/.claude/` and
`~/.claude.json`), not in your real `$HOME`, and persist for later sessions
of this project. A separate project has its own home and login.
Claude Code needs a Pro, Max, Team, Enterprise or Console account.
Alternatively, put `ANTHROPIC_API_KEY` in `~/.config/roke/secrets.env`;
Claude Code asks once whether to use it.

## Your configuration

`~/.config/roke/agents/claude/` is linked into `~/.claude`: `settings.json`,
`CLAUDE.md` (instructions for Claude Code only), plus `agents/`, `commands/`,
`skills/` and `rules/` if you use them. It is mounted read-only, so edit it
on your host. Claude Code's own state (sessions, auto memory, the login)
stays in the project's home volume.

## Instructions, MCP servers and Serena

- **Instructions**: the combined instructions (see
  [agents](../README.md#instructions-for-the-agent)) become the managed
  `CLAUDE.md` (`/etc/claude-code/CLAUDE.md`), which Claude Code loads before
  your `~/.claude/CLAUDE.md` and the project's, and which cannot be
  excluded. In the project, Claude Code reads its `CLAUDE.md`, or its
  `AGENTS.md` when there is no `CLAUDE.md`.
- **MCP servers**: those of the project (`roke mcp`) are registered next to
  Serena, in the same place; see [MCP servers](../../mcps/README.md).
- **Serena**: passed on every start as an MCP configuration file
  (`--mcp-config`), with Serena's `claude-code` context. MCP servers you
  configure yourself keep working alongside it.

## Notes

- **Sandboxing.** Claude Code's own sandbox for shell commands may not work
  inside the box, which runs without Linux capabilities. The box itself is
  the sandbox: the agent cannot reach anything on your machine beyond the
  project, so its permission prompts guard the project, not your system.
- Resume the last session with `roke continue`.
