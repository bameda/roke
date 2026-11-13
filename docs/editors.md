# Editors, the web and your phone

Besides the terminal, you can use the agent in the box from your editor, a
browser or a phone. What is available depends on the agent:

| | Terminal | Editors (`roke acp`) | Web and phone (`roke --ui`) |
|---|---|---|---|
| Claude Code | `roke` | yes | yes: [Remote Control](#claude-code-remote-control) |
| Codex CLI | `roke` | yes | no |
| OpenCode 2 | `roke` | yes | yes: [its web interface](../catalog/agents/opencode/README.md#web-and-editors) |

In every case the agent runs in the box, with the same isolation, network,
services, MCP servers and tool approvals as in the terminal. Nothing
changes in what it can reach.

- [Editors](#editors)
- [Log in first](#log-in-first)
- [Zed](#zed)
- [JetBrains IDEs](#jetbrains-ides)
- [VS Code](#vs-code)
- [Claude Code Remote Control](#claude-code-remote-control)
- [What roke keeps in the box](#what-roke-keeps-in-the-box)
- [Troubleshooting](#troubleshooting)

## Editors

Editors that support the [Agent Client Protocol](https://agentclientprotocol.com/)
(ACP) start an agent as a program and talk to it over its standard input and
output. `roke acp` is that program: it starts the project's box and the
agent's ACP adapter in it, and passes the conversation along.

```fish
roke acp                  # the project's agent, in the current directory
roke acp -a codex         # another agent
roke acp -C ~/src/shop    # another directory
```

You do not run it yourself: you tell your editor to. It takes the options of
`roke` that make sense for a session (`-a`, `-s`, `--network`...), and works on
the directory where the editor starts it. If your editor starts agents
somewhere else, add `-C` with the project's directory. Use the full path to
`roke` (`command -v roke`), since an editor started from a launcher may not have
your `PATH`.

The first time, the image needs the adapters: run `roke build` after updating
roke. They are part of the Claude Code and Codex installs; OpenCode has its own.

## Log in first

An editor cannot show a login that happens inside the box, so log in once per
project from the terminal, the way the agent's README explains, and the editor
uses that login:

```fish
roke exec -a claude claude auth login
roke exec -a codex codex login --device-auth
roke -a opencode            # then /connect
```

Or put the provider's API key in `~/.config/roke/secrets.env`.

## Zed

Add one entry per agent to `~/.config/zed/settings.json`
([Zed's documentation](https://zed.dev/docs/ai/external-agents)):

```json
{
  "agent_servers": {
    "Claude Code (roke)": {
      "type": "custom",
      "command": "/home/you/.local/bin/roke",
      "args": ["acp", "-a", "claude"],
      "env": {}
    },
    "Codex (roke)": {
      "type": "custom",
      "command": "/home/you/.local/bin/roke",
      "args": ["acp", "-a", "codex"],
      "env": {}
    }
  }
}
```

Open the agent panel, start a new thread and choose the entry. **`dev: open
acp logs`** shows the messages between Zed and the agent.

## JetBrains IDEs

In **AI Chat**, open the menu at the top right and choose **Add Custom Agent**.
It opens `~/.jetbrains/acp.json`
([JetBrains' documentation](https://www.jetbrains.com/help/ai-assistant/acp.html)):

```json
{
  "default_mcp_settings": {},
  "agent_servers": {
    "Claude Code (roke)": {
      "command": "/home/you/.local/bin/roke",
      "args": ["acp", "-a", "claude"]
    }
  }
}
```

Use the full path to `roke`, and restart the IDE if the agent does not
appear. **Get ACP Logs**, in the same menu, collects the logs. JetBrains does
not support ACP agents in WSL.

## VS Code

VS Code does not support ACP by itself yet, so it relies on extensions, which
differ in their settings. One that follows Zed's format, with its
`${workspaceFolder}` placeholder, takes this in `settings.json`
([its documentation](https://marketplace.visualstudio.com/items?itemName=strato-space.acp-plugin)):

```json
{
  "agent_servers": {
    "Claude Code (roke)": {
      "type": "custom",
      "command": "/home/you/.local/bin/roke",
      "args": ["acp", "-a", "claude", "-C", "${workspaceFolder}"]
    }
  }
}
```

Check your extension's documentation for its own keys. Whichever you use,
the command is `roke` with `acp` as its first argument.

Without an extension, run `roke` in VS Code's integrated terminal: the editor
sees the agent's changes through the project's directory, which the box shares
with your machine.

## Other editors

Neovim and Emacs have plugins for ACP agents; the command to give them is the
same: `roke` with the arguments `acp -a NAME`.

## Claude Code Remote Control

`roke --ui -a claude` starts Claude Code with
[Remote Control](https://code.claude.com/docs/en/remote-control): the session
stays in your terminal and you can also continue it from
[claude.ai/code](https://claude.ai/code) or the Claude app on your phone.
Claude Code prints the session's URL, and a QR code is one keypress away.

- It needs a Pro, Max, Team or Enterprise login with your claude.ai account.
  API keys are not supported, and roke says so if `ANTHROPIC_API_KEY` is set.
- The box makes outbound connections only; no port is published.
  The conversation passes through Anthropic and is stored there while Remote
  Control is connected, as [its documentation](https://code.claude.com/docs/en/remote-control#connection-and-security)
  explains. The files and commands stay in the box.
- `roke continue --ui -a claude` resumes the last session.
- If it cannot connect, `roke network blocked` shows what the box was denied.

For OpenCode, `--ui` publishes its web interface on `127.0.0.1`; see
[its README](../catalog/agents/opencode/README.md#web-and-editors). Codex has
no `--ui`: use it from an editor.

Running the agent from the ChatGPT or Claude desktop apps over SSH is not
supported: the box has no SSH server.

## What roke keeps in the box

ACP lets an editor offer the agent its own file and terminal methods, which
would run on your machine, outside the box. `roke acp` does not allow it: it
tells the agent the editor offers neither and refuses any such request, so the
agent uses its own tools, in the box. A session for a folder outside the
project is refused too, with a message saying what to open.

Some things are worth knowing:

- The editor and the agent share the project's directory, so the editor sees
  every change, and the agent can change any file in it.
- MCP servers you configure in the editor are passed to the agent and run in
  the box, with its restricted network. Those that need programs or paths of your
  machine will not work there; use [`roke mcp`](../catalog/mcps/README.md).
- Tool approvals work as usual, through the editor's permission prompts
  and [`roke mcp allow`](../catalog/mcps/README.md#tool-approvals).

## Troubleshooting

- **The agent does not start**: run `roke acp` in the project's directory in a
  terminal. It waits for the editor's messages; a startup error, such as a
  missing login or image, is printed on its standard error, which editors show
  in their logs.
- **"refusing to mount your whole $HOME"**: the editor started `roke` in your
  home directory. Add `-C` with the project's directory.
- **"outside the project"**: the editor's folder is not the project's. Open the
  project's folder, or give `roke acp` the right `-C`.
- **"the project is already running ... its network does not allow ..."**: two
  agents are open in the project; see
  [several agents at once](../catalog/agents/README.md#several-agents-at-once).
- **The agent says a domain does not resolve**: see
  [network](network.md#when-something-cannot-connect).
