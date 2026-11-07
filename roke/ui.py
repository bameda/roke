"""Messages, errors and the help text."""

import sys
from typing import NoReturn


class Fail(Exception):
    """An error to report to the user, ending the command."""


def info(message: str) -> None:
    print(f"[roke] {message}", file=sys.stderr, flush=True)


def die(message: str) -> NoReturn:
    raise Fail(message)


USAGE = """\
Usage: roke [-C DIR] [COMMAND] [OPTIONS]

Run a coding agent in a container that can only see the project in the
current directory (or DIR, with -C).

The project's box
  roke [run]                 Start the agent
  roke continue              Resume the agent's last session
  roke shell                 Open bash in the box
  roke exec CMD...           Run a command in the box
  roke urls                  Where the app and the services are
  roke settings              Every setting of the project and where it comes from
  roke build [--no-cache]    Build the images
  roke down [--all]          Stop the project's containers, or every project's;
                             their data is kept
  roke purge                 Stop them and delete all the project's data

Agents
  roke agent                 The agents, and the one this project uses
  roke agent use NAME        Use NAME in this project (--global: by default)
  roke agent reset           This project uses the default agent again

Services
  roke service               The services, and the ones this project uses
  roke service add NAME...   Add services to this project
  roke service rm NAME...    Remove them from it (their data is kept)

Network
  roke network               The network mode and the allowed destinations
  roke network add DEST      Allow a destination in this project (--global: in
                             every project): a domain, IP or CIDR, with an
                             optional :port, such as db.example.com:5432
  roke network rm DEST       Stop allowing it (--global: in every project)
  roke network blocked       What the project tried to reach and was denied

roke itself
  roke init [GIT_URL]        Create ~/.config/roke, cloning GIT_URL if given
  roke update                Update roke (then roke build)
  roke help [COMMAND]        This help, or a command's part of it

Options for run, continue, shell and exec, for this time only (-s and -p
also apply to roke urls):
  -a, --agent NAME           Use another agent
  -s, --services LIST        Start these services instead, comma-separated
  -p, --port PORT            Publish a port of the box on 127.0.0.1 (repeatable)
      --network MODE         restricted or open
      --git-rw               Let the agent write to .git, so it can commit
      --serena, --no-serena  Enable or disable Serena

Settings live in ~/.config/roke (or $ROKE_CONFIG_DIR): roke.env for every
project and projects/<dir-name>/ for each one. See docs/usage.md.
"""

BOX_COMMANDS = ("run", "continue", "shell", "exec", "urls", "settings", "build", "down", "purge")
SECTIONS = {
    **{c: "The project's box" for c in BOX_COMMANDS},
    "agent": "Agents",
    "service": "Services",
    "network": "Network",
    **{c: "roke itself" for c in ("init", "update", "help")},
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
    if section == "The project's box":
        text += "\n\n" + _block("Options for run")
    return text
