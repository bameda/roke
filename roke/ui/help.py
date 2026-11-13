"""The text of roke help, as a whole and by command."""

from roke.ui import die

USAGE = """\
Usage: roke [COMMAND] [OPTIONS]

Run a coding agent in a container that can only see the project in the
current directory (or DIR, with -C).
roke run is the explicit form of roke; both start a new agent session.

The project's box
  roke [run]                 Start the agent
                             (--ui starts the OpenCode web interface)
  roke continue              Resume the agent's last session
  roke shell                 Open bash in the box
  roke exec CMD...           Run a command in the box
  roke urls                  Where the app and the services are
  roke logs [OPTIONS] [SERVICE...]
                             Show project logs (Compose logs options)
  roke settings              The project's settings and where they come from
  roke doctor [--yaml]       Check prerequisites (--yaml: shareable report)
  roke settings edit [FILE]  Edit them in your editor (--global: yours): env
                             (default), secrets, compose, instructions, or
                             tools (the project's mise.toml)
  roke build [--no-cache]    Build the images
  roke down [--all]          Stop the project's containers, or every project's;
                             their data is kept
  roke purge                 Stop them and delete all the project's data

Projects
  roke project               The registered IDs and paths on this machine
  roke project show ID       A registered project's settings, from any directory
  roke project rename OLD NEW
                             Give a project another ID, keeping its data
  roke project rm ID         Forget a project's registration (its settings and
                             data are kept)

Images
  roke image                 The box images on this machine, and which projects
                             use each one
  roke image prune           Remove the ones no project uses

Agents
  roke agent                 The agents, and the one this project uses
  roke agent show NAME       An agent, and its documentation
  roke agent use NAME        Use NAME in this project (--global: by default)
  roke agent reset           This project uses the default agent again

Services
  roke service               The services, and the ones this project uses
  roke service show NAME     A service in this project: version, address,
                             variables, and its documentation
  roke service add NAME...   Add services to this project
  roke service rm NAME...    Remove them from it (their data is kept)
  roke service upgrade [NAME...]
                             Move this project's services, or some, to the
                             current versions (--major: also major versions of
                             services that keep data)

MCP servers
  roke mcp                   The MCP servers, and the ones this project uses
  roke mcp show NAME         An MCP server, tool approval policy, and documentation
  roke mcp add NAME...       Give them to the agent (--global: in every project)
                             --allow or --ask also sets tool approvals
  roke mcp rm NAME...        Take them away (--global: from every project)
  roke mcp allow NAME...     Allow their tools without prompting (--global:
                             by default in every project)
  roke mcp ask NAME...       Ask before using their tools (--global: by default)

Network
  roke network               The network mode and the allowed destinations
  roke network add DEST      Allow a destination in this project (--global: in
                             every project): a domain, IP or CIDR, with an
                             optional :port, such as db.example.com:5432;
                             --note TEXT says what it is for
  roke network rm DEST       Stop allowing it (--global: in every project)
  roke network blocked       What the project tried to reach and was denied

roke itself
  roke version               Show the installed roke version (also --version)
  roke init [GIT_URL]        Create ~/.config/roke, cloning GIT_URL if given
  roke update [--stable|--main]
                             Update within the saved channel, or switch it
                             (then roke build in your projects)
  roke help [COMMAND]        This help, or a command's part of it

Project selection, for every command that works on a project (for example:
roke settings -C DIR):
  -C DIR                     Work in DIR
      --id ID                This directory is the project ID: chosen on first
                             use, or to reattach it after a move
                             (remembered for subsequent commands)

Options for run, continue, shell and exec, for this time only (-s and -p
also apply to roke urls):
  -a, --agent NAME           Use another agent
  -s, --services LIST        Start these services instead, comma-separated
  -p, --port PORT            Publish a port of the box on 127.0.0.1 (repeatable)
      --network MODE         restricted or open
      --git-rw               Let the agent write to .git, so it can commit
      --serena, --no-serena  Enable or disable Serena

Settings live in ~/.config/roke (or $ROKE_CONFIG_DIR): roke.env for every
project and projects/<id>/ for each one. The ID defaults to the directory
name. See docs/usage.md.
"""

BOX_COMMANDS = (
    "run",
    "continue",
    "shell",
    "exec",
    "urls",
    "logs",
    "settings",
    "doctor",
    "build",
    "down",
    "purge",
)
SECTIONS = {
    "project": "Projects",
    "image": "Images",
    **{c: "The project's box" for c in BOX_COMMANDS},
    "agent": "Agents",
    "service": "Services",
    "mcp": "MCP servers",
    "network": "Network",
    **{c: "roke itself" for c in ("init", "update", "version", "help")},
}


def _block(title_prefix: str) -> str:
    """The lines of the help from the one starting with TITLE_PREFIX to the
    next blank line."""
    out: list[str] = []
    for line in USAGE.splitlines():
        if out and not line:
            break
        if out or line.startswith(title_prefix):
            out.append(line)
    return "\n".join(out)


def help_for(command: str) -> str:
    section = SECTIONS.get(command)
    if section is None:
        die(f"no help for '{command}' (commands: {' '.join(SECTIONS)})")
    text = _block(section)
    text += "\n\n" + _block("Project selection")
    if section == "The project's box":
        text += "\n\n" + _block("Options for run")
    return text
