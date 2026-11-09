"""Validation for destinations accepted by the gateway's allow list."""

import ipaddress
import re

LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")


def valid(value: str) -> bool:
    host, sep, port = value.rpartition(":")
    if sep:
        if not port.isascii() or not port.isdecimal() or not 1 <= int(port) <= 65535:
            return False
    else:
        host = value
    if host == "host":
        return bool(sep)
    if host.startswith("*."):
        host = host[2:]
    try:
        ipaddress.IPv4Network(host, strict=False)
        return True
    except ValueError:
        pass
    if re.fullmatch(r"[0-9.]+", host):
        return False
    if "/" in host or not host or len(host) > 253:
        return False
    return all(LABEL.fullmatch(label) for label in host.split("."))
