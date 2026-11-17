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

The image also gets `claude-agent-acp`, the adapter editors use (see below).

## Log in

Run `roke -a claude` and follow the login prompts. Claude shows a URL to
open in your host's browser and asks you to paste the code back into the
terminal. The credentials are kept in the project's home volume (`~/.claude/`
and `~/.claude.json`), not in your real `$HOME`, and persist for later sessions
of this project. A separate project has its own home and login.
Claude Code needs a Pro, Max, Team, Enterprise or Console account.
Alternatively, put `ANTHROPIC_API_KEY` in `~/.config/roke/secrets.env`;
Claude Code asks once whether to use it.

## Web, phone and editors

- `roke --ui` starts [Remote Control](../../../docs/editors.md#claude-code-remote-control):
  the session stays in your terminal and you can continue it from claude.ai/code or
  the Claude app. It needs a claude.ai login, not an API key.
- `roke acp -a claude` serves Claude Code to an editor through the
  `claude-agent-acp` adapter, which runs the image's `claude` with the MCP
  servers and tool approvals described below. See
  [editors](../../../docs/editors.md).

## Your configuration

`~/.config/roke/agents/claude/` is linked into `~/.claude`: `settings.json`,
`CLAUDE.md` (instructions for Claude Code only), plus `agents/`, `commands/`,
`skills/` and `rules/` if you use them. It is mounted read-only, so edit it
on your host. Claude Code's own state (sessions, auto memory, the login)
stays in the project's home volume.

How roke gives Claude Code the instructions, MCP servers and approvals is in
[how roke configures each agent](../README.md#how-roke-configures-each-agent).

## Notes

- The combined instructions become the managed `CLAUDE.md`, which Claude Code
  loads before your `~/.claude/CLAUDE.md` and the project's, and which cannot be
  excluded. In the project, Claude Code reads its `CLAUDE.md`, or its `AGENTS.md`
  when there is no `CLAUDE.md`.
- The approvals `roke mcp allow` and `ask` generate also cover Serena. Your
  deny and ask rules keep Claude Code's precedence. See
  [tool approvals](../../mcps/README.md#tool-approvals).
- **Your claude.ai connectors are off.** Signed in with a claude.ai account,
  Claude Code adds its connectors (Gmail, Calendar, Drive...) as MCP servers,
  through `mcp-proxy.anthropic.com`. They are not in `roke mcp`, and their tools
  would act on your accounts from the box, so roke sets
  `ENABLE_CLAUDEAI_MCP_SERVERS=false`; it also saves some context in every
  session. To use them, set that variable to `true` in your settings and
  `roke network add mcp-proxy.anthropic.com`.
- **Telemetry.** Claude Code sends usage metrics to third-party logging
  services, such as `http-intake.logs.us5.datadoghq.com`. The restricted
  network blocks them, and `roke network blocked` marks them as harmless.
  Do not silence them with `DISABLE_TELEMETRY` or
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`: both also turn off the feature
  flags Remote Control needs.
- **Sandboxing.** Claude Code's own sandbox for shell commands may not work
  inside the box, which runs without Linux capabilities. The box itself is
  the sandbox: the agent cannot reach anything on your machine beyond the
  project, so its permission prompts guard the project, not your system.
