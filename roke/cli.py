"""Command line: parse the arguments into a Request, then run it."""

import sys
from dataclasses import dataclass, field

from roke import commands
from roke.commands.settings import EDITABLE
from roke.ui import Fail, die
from roke.ui.help import USAGE, help_for

RUN_LIKE = ("run", "continue", "shell", "exec", "urls")
GROUPS: dict[str, dict[str, tuple[int, int | None]]] = {
    "agent": {"list": (0, 0), "show": (1, 1), "use": (1, 1), "reset": (0, 0)},
    "service": {
        "list": (0, 0),
        "show": (1, 1),
        "add": (1, None),
        "rm": (1, None),
        "upgrade": (0, None),
    },
    "mcp": {"list": (0, 0), "show": (1, 1), "add": (1, None), "rm": (1, None)},
    "network": {"list": (0, 0), "add": (1, 1), "rm": (1, 1), "blocked": (0, 0)},
}
USAGES = {
    "agent use": "roke agent use NAME [--global]",
    "agent show": "roke agent show NAME",
    "service show": "roke service show NAME",
    "mcp show": "roke mcp show NAME",
    "service add": "roke service add NAME...",
    "service rm": "roke service rm NAME...",
    "mcp add": "roke mcp add NAME... [--global]",
    "mcp rm": "roke mcp rm NAME... [--global]",
    "network add": "roke network add DEST [--global] [--note TEXT]",
    "network rm": "roke network rm DEST [--global]",
}


@dataclass
class Request:
    command: str = "run"
    sub: str = ""  # agent, service and network: list, use, add...
    project: str = ""  # -C DIR
    agent: str = ""  # -a
    services: str | None = None  # -s
    ports: list = field(default_factory=list)
    network: str = ""
    git_rw: bool = False
    serena: bool | None = None
    cmd: list = field(default_factory=list)  # shell and exec
    values: list = field(default_factory=list)  # names or destinations
    is_global: bool = False
    major: bool = False  # service upgrade --major
    note: str | None = None  # network add --note
    no_cache: bool = False
    all: bool = False
    help: str | None = None  # set when only the help is wanted


def _expect_no_more(req: Request, args: list) -> None:
    if args:
        if args[0].startswith("-"):
            die(f"unknown option for roke {req.command}: {args[0]} (see roke help)")
        die(f"unexpected argument for roke {req.command}: {args[0]} (see roke help {req.command})")


def _take(args: list, i: int, what: str) -> str:
    if i + 1 >= len(args):
        die(f"missing {what}")
    return args[i + 1]


def _run_options(req: Request, args: list) -> list:
    """Parse the run options at the start of ARGS; return the rest."""
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-a", "--agent"):
            req.agent = _take(args, i, "agent name")
            i += 2
        elif a in ("-s", "--services"):
            req.services = _take(args, i, "service list")
            i += 2
        elif a in ("-p", "--port"):
            req.ports.append(_take(args, i, "port"))
            i += 2
        elif a == "--network":
            req.network = _take(args, i, "network mode")
            i += 2
        elif a == "--git-rw":
            req.git_rw = True
            i += 1
        elif a == "--serena":
            req.serena = True
            i += 1
        elif a == "--no-serena":
            req.serena = False
            i += 1
        elif a in ("-h", "--help"):
            req.help = req.command
            return []
        else:
            break
    return args[i:]


def _flags(req: Request, args: list, allowed: dict) -> None:
    for a in args:
        if a in ("-h", "--help"):
            req.help = req.command
            return
        if a not in allowed:
            _expect_no_more(req, [a])
        setattr(req, allowed[a], True)


def parse(argv: list) -> Request:
    req = Request()
    args = list(argv)
    while args[:1] == ["-C"]:
        if len(args) < 2:
            die("-C needs a directory")
        req.project, args = args[1], args[2:]
    if args[:1] in (["-h"], ["--help"]):
        req.command, req.help = "help", ""
        return req
    if args and not args[0].startswith("-"):
        req.command, args = args[0], args[1:]

    c = req.command
    if c in RUN_LIKE:
        rest = _run_options(req, args)
        if req.help:
            return req
        if c == "shell":
            req.cmd = ["bash"]
        elif c == "exec":
            if rest[:1] == ["--"]:
                rest = rest[1:]
            if not rest:
                die("roke exec needs a command: roke exec psql")
            req.cmd, rest = rest, []
        _expect_no_more(req, rest)
    elif c == "settings" and args[:1] == ["edit"]:
        req.sub = "edit"
        for a in args[1:]:
            if a == "--global":
                req.is_global = True
            elif a in ("-h", "--help"):
                req.help = c
                return req
            else:
                req.values.append(a)
        if len(req.values) > 1 or (req.values and req.values[0] not in EDITABLE):
            die(f"usage: roke settings edit [{'|'.join(EDITABLE)}] [--global]")
    elif c in ("settings", "purge", "doctor"):
        _flags(req, args, {})
    elif c == "build":
        _flags(req, args, {"--no-cache": "no_cache"})
    elif c == "down":
        _flags(req, args, {"--all": "all"})
    elif c == "logs":
        if args in (["-h"], ["--help"]):
            req.help = c
        else:
            req.cmd = args
    elif c in GROUPS:
        req.sub = args[0] if args else "list"
        args = args[1:]
        if req.sub in ("-h", "--help"):
            req.help = c
            return req
        values = []
        arg_iter = iter(args)
        for a in arg_iter:
            if a == "--global":
                req.is_global = True
            elif a == "--major" and c == "service":
                req.major = True
            elif a == "--note" or a.startswith("--note="):
                note = a.partition("=")[2] if "=" in a else next(arg_iter, None)
                if note is None:
                    die("--note needs a text, such as --note 'why it is allowed'")
                req.note = note
            elif a in ("-h", "--help"):
                req.help = c
                return req
            else:
                values.append(a)
        if req.sub not in GROUPS[c]:
            die(f"unknown command: roke {c} {req.sub} (see roke help {c})")
        low, high = GROUPS[c][req.sub]
        if len(values) < low or (high is not None and len(values) > high):
            usage = USAGES.get(f"{c} {req.sub}")
            if usage:
                die(f"usage: {usage}")
            _expect_no_more(req, values)
        if req.major and req.sub != "upgrade":
            die("--major only applies to roke service upgrade")
        if req.note is not None and (c, req.sub) != ("network", "add"):
            die("--note only applies to roke network add")
        if c == "agent" and req.sub == "reset" and req.is_global:
            die(
                "roke agent reset applies to the project; the default agent is set "
                "with roke agent use NAME --global"
            )
        req.values = values
    elif c == "init":
        if len(args) > 1:
            die("usage: roke init [GIT_URL]")
        req.values = args
    elif c == "update":
        _expect_no_more(req, args)
    elif c == "help":
        req.help = args[0] if args else ""
    else:
        die(f"unknown command: {c} (see roke help)")
    return req


def main(argv: list) -> int:
    try:
        req = parse(argv)
        if req.help is not None:
            print(help_for(req.help) if req.help else USAGE, end="" if not req.help else "\n")
            return 0
        return commands.run(req)
    except Fail as e:
        print(f"roke: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
