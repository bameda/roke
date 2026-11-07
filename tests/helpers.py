"""Helpers to read the `docker compose` calls the fake docker records."""


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
