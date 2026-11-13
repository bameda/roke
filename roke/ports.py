"""The ports of the box that roke publishes, from -p and ROKE_PORTS."""

import ipaddress

from roke.ui import die


def _port(text: str) -> bool:
    return text.isdigit() and 1 <= int(text) <= 65535


def _valid_ip(text: str) -> bool:
    try:
        return isinstance(ipaddress.ip_address(text), ipaddress.IPv4Address)
    except ValueError:
        return False


def normalize(entries: list[str], source: str) -> list[str]:
    """Docker's mapping for each entry. A bare PORT is published on 127.0.0.1;
    HOST_PORT:PORT and IP:HOST_PORT:PORT, each with an optional /tcp or /udp,
    are passed on as written, so that you can choose another address."""
    mappings = []
    for entry in entries:
        body, slash, protocol = entry.partition("/")
        parts = body.split(":")
        valid = not slash or protocol in ("tcp", "udp")
        if len(parts) == 1 and not slash:
            valid = valid and _port(parts[0])
            mapping = f"127.0.0.1:{parts[0]}:{parts[0]}"
        elif len(parts) == 2:
            valid = valid and all(_port(p) for p in parts)
            mapping = entry
        elif len(parts) == 3:
            valid = valid and _valid_ip(parts[0]) and all(_port(p) for p in parts[1:])
            mapping = entry
        else:
            valid = False
        if not valid:
            die(
                f"invalid port '{entry}' in {source}: use a number from 1 to 65535, such as "
                "5173, or HOST_PORT:PORT, or IP:HOST_PORT:PORT; separate several with "
                "spaces or commas"
            )
        mappings.append(mapping)
    return mappings
