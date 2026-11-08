"""roke's output: messages, errors, the pager and colours. The help text
is in help.py, and the terminal Markdown renderer in markdown.py."""

import os
import shlex
import shutil
import subprocess
import sys
from typing import NoReturn


class Fail(Exception):
    """An error to report to the user, ending the command."""


def info(message: str) -> None:
    print(f"[roke] {message}", file=sys.stderr, flush=True)


def die(message: str) -> NoReturn:
    raise Fail(message)


def use_color(setting: str | None) -> bool:
    """Whether to colour the output. SETTING is ROKE_COLOR: "always" and
    "never" decide; "auto", the default, colours a terminal unless NO_COLOR
    is set or the terminal is dumb."""
    mode = (setting or "auto").lower()
    if mode not in ("auto", "always", "never"):
        die(f"ROKE_COLOR must be auto, always or never, not '{setting}'")
    if mode != "auto":
        return mode == "always"
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    return sys.stdout.isatty()


def page(text: str) -> None:
    """Print TEXT, through a pager ($PAGER, or less) when it does not fit in
    the terminal."""
    lines = text.count("\n") + 1
    if sys.stdout.isatty() and lines > shutil.get_terminal_size().lines - 1:
        pager = shlex.split(os.environ.get("PAGER") or "less -FRX")
        if shutil.which(pager[0]):
            subprocess.run(pager, input=text + "\n", text=True)
            return
    print(text)
