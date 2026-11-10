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

## Log in

Run `roke -a claude` and follow the login prompts. Claude shows a URL to
open in your host's browser and asks you to paste the code back into the
terminal. The credentials are kept in the project's home volume (`~/.claude/` and
`~/.claude.json`), not in your real `$HOME`, and persist for later sessions
of this project. A separate project has its own home and login.
Claude Code needs a Pro, Max, Team, Enterprise or Console account.
Alternatively, put `ANTHROPIC_API_KEY` in `~/.config/roke/secrets.env`;
Claude Code asks once whether to use it.

## Terminal

The terminal is the default. From the project directory on your host, run
`roke -a claude` to start a session or `roke continue -a claude` to resume
the last one. Omit `-a claude` if the project already uses Claude Code.

## Web, desktop and editors

### Browser and Claude Desktop

Start or resume a terminal session with the commands above and sign in with
your Claude account. Enter `/remote-control` and keep the box session running.
Open the URL that Claude prints in your browser, or select the connected
session in Claude Desktop with the same account. Remote Control relays the
session through Anthropic. [Claude Code Remote Control](https://code.claude.com/docs/en/remote-control)

To start a session directly from Claude Desktop, the **Code** tab supports
SSH. Running one in roke would require an SSH endpoint in the project's box.
The standard box has no SSH server. [Claude Desktop SSH sessions](https://code.claude.com/docs/en/desktop#ssh-sessions)

### VS Code

Start `roke shell -a claude` and leave it running. Attach VS Code to the
project's box with Dev Containers, open the project directory in the attached
window and install the Claude Code extension there. Use the terminal commands
or Remote Control when you need the MCP configuration and tool approval
arguments that roke passes when it starts Claude Code.
[Using a graphical editor](../README.md#using-a-graphical-editor) · [Claude Code in VS Code](https://code.claude.com/docs/en/vs-code)

## Your configuration

`~/.config/roke/agents/claude/` is linked into `~/.claude`: `settings.json`,
`CLAUDE.md` (instructions for Claude Code only), plus `agents/`, `commands/`,
`skills/` and `rules/` if you use them. It is mounted read-only, so edit it
on your host. Claude Code's own state (sessions, auto memory, the login)
stays in the project's home volume.

## Instructions, MCP servers and Serena

`roke mcp allow NAME` and `roke mcp ask NAME` generate per-session Claude
Code settings with `permissions.allow` or `permissions.ask` rules for that
server. They also apply to Serena. Existing deny and ask rules retain
Claude Code's precedence. See [Tool approvals](../../mcps/README.md#tool-approvals).

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
