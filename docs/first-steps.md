# First steps with your project

Start in your own project's directory and add what you need as you go.
roke registers the project automatically; you do not need to copy an example
or create configuration files first.

## 1. Start your first session

You need Docker with Compose and roke installed: see
[Installation](installation.md) if you have not done that yet. If you have
not chosen a default agent yet, choose one once:

```bash
roke agent use claude --global   # or codex, or opencode
```

Run these commands in your terminal on the host, in the directory containing
your code:

```bash
cd ~/src/my-project
roke build
roke
```

`roke build` prepares the images. `roke` starts the agent inside the isolated
box, with access to your project. The project ID defaults to the directory
name, and roke remembers it for subsequent commands. If that ID is already
taken, choose another with `roke build --id my-project-work` before starting
the agent. See [project IDs and moves](configuration.md#project-ids-and-moves).

Your agent may need authentication with its provider. This is the agent's
account, not a roke account; follow its instructions:
[Claude Code](../catalog/agents/claude/README.md#log-in),
[Codex](../catalog/agents/codex/README.md#log-in) or
[OpenCode](../catalog/agents/opencode/README.md#log-in).
Credentials are kept in this project's own home volume and persist between
its sessions. If you already configured an API key, follow the relevant
agent's instructions for using it.

You can now work with the agent. Ask it to read the project, explain how to
run it, or make a change. It can install the project's language tools with
[mise](configuration.md#languages-and-tools).

## 2. Continue a session

Exit the agent to return to your host terminal. From the same project
directory, resume its last session with:

```bash
roke continue
```

Use `roke` instead to start a new conversation. You do not need to repeat
the project ID, agent choice or saved settings each time.

The following sections show optional additions. Run their `roke` commands
in your host terminal, after leaving the agent. Changes apply on the next
start: use `roke continue` to resume your conversation with the updated
environment, or `roke` for a new one.

## 3. Add a service

List the available services, add one to this project and inspect its
connection details:

```bash
roke service
roke service add postgres
roke service show postgres
```

PostgreSQL starts with your next session. The box receives its connection
variables, including `DATABASE_URL`; the app should use those rather than
connect to `localhost`. You can ask the agent to adapt the app to them.

Add more services as needed, for example `roke service add redis mailpit`.
You can run a client yourself inside the box with `roke exec psql`.
For more details, see the [service catalog](../catalog/services/README.md).

## 4. Add an MCP server

MCP servers give the agent additional tools. For example, Context7 provides
library documentation:

```bash
roke mcp
roke mcp add context7
roke mcp show context7
```

The MCP is available on the next session start. Some MCP servers need
credentials: `roke mcp show NAME` explains their requirements. Use
`roke settings edit secrets` to configure secrets for this project; see the
[MCP guide](../catalog/mcps/README.md) for each server's instructions.

## 5. Allow a network destination

The box has a restricted network by default. If a download or API request
fails, leave the agent and inspect what was blocked:

```bash
roke network blocked
```

Allow a destination you need, with a note explaining why:

```bash
roke network add api.example.com --note "API used by this project"
```

Replace `api.example.com` with the domain you need from the blocked report.
Use a domain, IP or address with a port, such as `db.example.com:5432`,
rather than a full URL with `https://` and a path. Start the session again
to apply the change. `roke network` shows the allowed destinations; the
[network guide](network.md) explains the policy in detail.

## 6. Open your app in the browser

If the agent runs a web app on port 5173, publish that port when starting
the session:

```bash
roke continue -p 5173
```

Ask the agent to make the dev server listen on `0.0.0.0`. Then open
`http://127.0.0.1:5173` in your browser. From another host terminal in the
project directory, `roke urls -p 5173` shows that address and any service
web UIs.

To save the port for future sessions, run `roke settings edit` and set
`ROKE_PORTS="5173"`. Services such as Mailpit publish their own web UIs;
their ports do not need `-p`.

## 7. Check the environment and finish for the day

From your host terminal:

```bash
roke settings              # the current project's effective settings
roke logs --tail 50         # recent gateway and service logs
roke doctor                # diagnose configuration and setup problems
git diff                   # review the agent's changes
roke down                  # stop the project's containers, keeping their data
```

By default, `.git` is read-only inside the box: review and commit changes
on the host. Exiting the agent keeps the project's services running;
`roke down` stops them. Your database data, agent credentials and sessions
remain available next time. `roke purge` deletes those volumes; see
[Usage](usage.md#projects-and-their-services) before using it.

## 8. Start another project

Enter another directory containing your code and start roke there:

```bash
cd ~/src/another-project
roke
```

Projects with the same box build settings reuse its image, so you usually
do not need to build it again. Different build settings use separate variants.
Some services have their own image build; their README explains what they
need. Each project has separate services, data, agent credentials and sessions.
Add its services, MCP servers and allowed destinations using the same commands
as above. `roke continue` resumes the session of the project you are in.

`roke project` lists registered IDs and paths. From any directory,
`roke settings show ID` shows a registered project's settings.

## Further configuration and examples

Once you need more customization, see [Configuration](configuration.md)
for saved settings, private instructions, Compose overrides and keeping
your configuration in a private repository. [Serena](serena.md) adds
optional semantic code navigation.

The [example projects](../examples/projects/README.md) show configurations
for common stacks. Use them as references, or copy one if it matches what
you need. They are optional; the commands above are enough to get started.
