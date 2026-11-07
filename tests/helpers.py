"""Helpers to read the `docker compose` calls the fake docker records, and
the catalog's defaults."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def opt_values(args, flag):
    """Every value given to FLAG in ARGS (for example all the -f files)."""
    return [args[i + 1] for i, a in enumerate(args[:-1]) if a == flag]


def compose_files(call):
    return opt_values(call["args"], "-f")


def project_name(call):
    return opt_values(call["args"], "-p")[0]


def after(call, word):
    """The arguments after the first occurrence of WORD (e.g. "box")."""
    args = call["args"]
    return args[args.index(word) + 1 :]


def env_value(path, key):
    """The value of KEY in a settings file, or None."""
    for line in path.read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip('"')
    return None


def catalog_default(service, var):
    """The default of VAR in the catalog's SERVICE, as in ${VAR:-default}, so
    that tests keep passing when an update changes it."""
    text = (REPO / "services" / service / "compose.yaml").read_text()
    match = re.search(rf"\$\{{{var}:-([^}}]+)\}}", text)
    assert match, f"{var} has no default in services/{service}/compose.yaml"
    return match.group(1)
