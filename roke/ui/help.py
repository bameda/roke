"""The text of roke help, as a whole and by command, from one table: each
entry says which command it belongs to, so `roke help COMMAND` shows exactly
that command's lines."""

from roke.ui import die

# (command, usage, description lines)
Entry = tuple[str, str, tuple[str, ...]]

SECTIONS: tuple[tuple[str, tuple[Entry, ...]], ...] = (
    (
        "Sessions",
        (
            ("run", "roke [run]", ("Start the agent", "(--ui starts the OpenCode web interface)")),
            ("continue", "roke continue", ("Resume the agent's last session",)),
            ("shell", "roke shell", ("Open bash in the box",)),
            ("exec", "roke exec CMD...", ("Run a command in the box",)),
        ),
    ),
    (
        "The project",
        (
            ("settings", "roke settings", ("The project's settings and where they come from",)),
            (
                "settings",
                "roke settings edit [FILE]",
                (
                    "Edit them in your editor (--global: yours): env",
                    "(default), secrets, compose, instructions, or",
                    "tools (the project's mise.toml)",
                ),
            ),
            ("urls", "roke urls", ("Where the app and the services are",)),
            (
                "logs",
                "roke logs [OPTIONS] [SERVICE...]",
                ("Show project logs (Compose logs options)",),
            ),
            ("doctor", "roke doctor [--yaml]", ("Check prerequisites (--yaml: shareable report)",)),
            ("build", "roke build [--no-cache]", ("Build the images",)),
            (
                "down",
                "roke down [--all]",
                ("Stop the project's containers, or every project's;", "their data is kept"),
            ),
            ("purge", "roke purge", ("Stop them and delete all the project's data",)),
        ),
    ),
    (
        "Projects and images, on this machine",
        (
            ("project", "roke project", ("The registered IDs and paths",)),
            (
                "project",
                "roke project show ID",
                ("A registered project's settings, from any directory",),
            ),
            (
                "project",
                "roke project rename OLD NEW",
                ("Give a project another ID, keeping its data",),
            ),
            (
                "project",
                "roke project rm ID",
                ("Forget a project's registration (its settings and", "data are kept)"),
            ),
            (
                "image",
                "roke image",
                ("The images roke built, and which projects use each one",),
            ),
            ("image", "roke image prune", ("Remove the ones no project uses",)),
        ),
    ),
    (
        "Agents",
        (
            ("agent", "roke agent", ("The agents, and the one this project uses",)),
            ("agent", "roke agent show NAME", ("An agent, and its documentation",)),
            ("agent", "roke agent use NAME", ("Use NAME in this project (--global: by default)",)),
            ("agent", "roke agent reset", ("This project uses the default agent again",)),
        ),
    ),
    (
        "Services",
        (
            ("service", "roke service", ("The services, and the ones this project uses",)),
            (
                "service",
                "roke service show NAME",
                (
                    "A service in this project: version, address,",
                    "variables, and its documentation",
                ),
            ),
            ("service", "roke service add NAME...", ("Add services to this project",)),
            (
                "service",
                "roke service rm NAME...",
                ("Remove them from it (their data is kept)",),
            ),
            (
                "service",
                "roke service upgrade [NAME...]",
                (
                    "Move this project's services, or some, to the",
                    "current versions (--major: also major versions of",
                    "services that keep data)",
                ),
            ),
        ),
    ),
    (
        "MCP servers",
        (
            ("mcp", "roke mcp", ("The MCP servers, and the ones this project uses",)),
            (
                "mcp",
                "roke mcp show NAME",
                ("An MCP server, tool approval policy, and documentation",),
            ),
            (
                "mcp",
                "roke mcp add NAME...",
                (
                    "Give them to the agent (--global: in every project)",
                    "--allow or --ask also sets tool approvals",
                ),
            ),
            ("mcp", "roke mcp rm NAME...", ("Take them away (--global: from every project)",)),
            (
                "mcp",
                "roke mcp allow NAME...",
                ("Allow their tools without prompting (--global:", "by default in every project)"),
            ),
            (
                "mcp",
                "roke mcp ask NAME...",
                ("Ask before using their tools (--global: by default)",),
            ),
            (
                "mcp",
                "roke mcp reset NAME...",
                ("Back to the agent's default approval (--global: by", "default in every project)"),
            ),
        ),
    ),
    (
        "Network",
        (
            ("network", "roke network", ("The network mode and the allowed destinations",)),
            (
                "network",
                "roke network add DEST",
                (
                    "Allow a destination in this project (--global: in",
                    "every project): a domain, IP or CIDR, with an",
                    "optional :port, such as db.example.com:5432;",
                    "--note TEXT says what it is for",
                ),
            ),
            (
                "network",
                "roke network rm DEST",
                ("Stop allowing it (--global: in every project)",),
            ),
            (
                "network",
                "roke network blocked",
                ("What the project tried to reach and was denied",),
            ),
        ),
    ),
    (
        "roke itself",
        (
            (
                "version",
                "roke version",
                ("Show the installed roke version (also --version)",),
            ),
            (
                "init",
                "roke init [GIT_URL]",
                ("Create ~/.config/roke, cloning GIT_URL if given",),
            ),
            (
                "update",
                "roke update [--stable|--main]",
                (
                    "Update within the saved channel, or switch it",
                    "(then roke build in your projects)",
                ),
            ),
            ("help", "roke help [COMMAND]", ("This help, or a command's part of it",)),
        ),
    ),
)

SELECTION = """\
Project selection, for every command that works on a project (for example:
roke settings -C DIR):
  -C DIR                     Work in DIR
      --id ID                This directory is the project ID: chosen on first
                             use, or to reattach it after a move
                             (remembered for subsequent commands)"""

RUN_OPTIONS = """\
Options for run, continue, shell and exec, for this time only (-s and -p
also apply to roke urls):
  -a, --agent NAME           Use another agent
  -s, --services LIST        Start these services instead (commas or spaces)
  -p, --port PORT            Publish ports of the box on 127.0.0.1 (several:
                             3000,5173, or repeat the option); HOST:PORT picks
                             the host port; 0.0.0.0:HOST:PORT opens it to your
                             whole network
      --network MODE         restricted or open
      --git-rw               Let the agent write to .git, so it can commit
      --serena, --no-serena  Enable or disable Serena"""

# The commands with options of their own, and those that work on a project.
WITH_RUN_OPTIONS = ("run", "continue", "shell", "exec", "urls")
ON_A_PROJECT = (
    *WITH_RUN_OPTIONS,
    "logs",
    "settings",
    "doctor",
    "build",
    "down",
    "purge",
    "agent",
    "service",
    "mcp",
    "network",
)
COMMANDS = tuple(dict.fromkeys(command for _, entries in SECTIONS for command, _, _ in entries))


def _entry(usage: str, lines: tuple[str, ...]) -> list[str]:
    """One entry: the description beside the usage when it fits, below otherwise."""
    if len(usage) <= 25:
        out = [f"  {usage:<27}{lines[0]}"]
        lines = lines[1:]
    else:
        out = [f"  {usage}"]
    return out + [f"{' ' * 29}{line}" for line in lines]


def _text(entries: list[Entry]) -> str:
    return "\n".join(line for _, usage, lines in entries for line in _entry(usage, lines))


USAGE = (
    """\
Usage: roke [COMMAND] [OPTIONS]

Run a coding agent in a container that can only see the project in the
current directory (or DIR, with -C).
roke run is the explicit form of roke; both start a new agent session.

"""
    + "\n\n".join(f"{title}\n{_text(list(entries))}" for title, entries in SECTIONS)
    + f"""

{SELECTION}

{RUN_OPTIONS}

Settings live in ~/.config/roke (or $ROKE_CONFIG_DIR): roke.env for every
project and projects/<id>/ for each one. The ID defaults to the directory
name. See docs/usage.md.
"""
)


def help_for(command: str) -> str:
    """The lines of COMMAND, and the options that apply to it."""
    entries = [entry for _, items in SECTIONS for entry in items if entry[0] == command]
    if not entries:
        die(f"no help for '{command}' (commands: {' '.join(COMMANDS)})")
    text = _text(entries)
    if command in WITH_RUN_OPTIONS:
        text += "\n\n" + RUN_OPTIONS
    if command in ON_A_PROJECT:
        text += "\n\n" + SELECTION
    return text
