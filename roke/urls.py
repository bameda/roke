"""Where the project's app and services are, from the resolved compose
configuration: the URLs to open from the host, and each service's address
and variables inside the box. Each service's variables are told apart by
comparing the configuration with and without it."""

import ipaddress
import re

SERENA_DASHBOARD = "24282"


def forwards(full: dict) -> dict[str, str]:
    """The gateway's forwards: its port -> the service's host:port."""
    gateway = full.get("services", {}).get("gateway", {})
    out = {}
    for key, value in (gateway.get("environment") or {}).items():
        if key.startswith("ROKE_FORWARD_") and value:
            port, target = value.split(None, 1)
            out[str(port)] = target
    return out


def host_urls(full: dict) -> list[tuple[str, str, str]]:
    """All host bindings: (what, address, destination and scope)."""
    fwd = forwards(full)
    rows = []
    for name, service in full.get("services", {}).items():
        for p in service.get("ports") or []:
            host = p.get("host_ip") or "0.0.0.0"
            published, target = p.get("published"), str(p.get("target"))
            if published is None:
                continue
            protocol = p.get("protocol", "tcp")
            scope = "local only" if ipaddress.ip_address(host).is_loopback else "network access"
            if host in ("0.0.0.0", "::"):
                scope += f", bind {host}"
            address = "127.0.0.1" if host == "0.0.0.0" else host
            address = "::1" if address == "::" else address
            address = f"[{address}]" if ":" in address else address
            scheme = "http" if name == "gateway" and protocol == "tcp" else protocol
            url = f"{scheme}://{address}:{published}"
            label, destination = name, f"{name}:{target}"
            if name == "gateway":
                if target in fwd:
                    destination = fwd[target]
                    label = destination.split(":")[0]
                elif target == SERENA_DASHBOARD:
                    label, destination, url = "serena", f"box:{target}", url + "/dashboard/"
                else:
                    label, destination = "app", f"box:{target}"
            rows.append((label, url, f"→ {destination} ({protocol}, {scope})"))
    return sorted(rows)


def service_info(name: str, own_conf: dict, base: dict, full: dict) -> tuple[list[str], dict]:
    """A service's addresses inside the box and the variables it gives the
    box, from the configuration with only that service (own_conf), without
    it (base) and the whole project's (full, for the values that apply)."""
    env = own_conf.get("services", {}).get("box", {}).get("environment") or {}
    base_env = base.get("services", {}).get("box", {}).get("environment") or {}
    box_env = full.get("services", {}).get("box", {}).get("environment") or {}
    own = [k for k in env if k not in base_env]

    def value(key: str) -> str:
        return str(box_env.get(key, env.get(key, "")))

    ports = {int(m) for k in own for m in re.findall(rf"\b{re.escape(name)}:(\d+)", value(k))}
    ports |= {int(t.split(":")[1]) for t in forwards(full).values() if t.split(":")[0] == name}
    for k in own:  # pairs such as SMTP_HOST=mailpit and SMTP_PORT=1025
        if k.endswith("_HOST") and value(k) == name:
            port = value(k[:-5] + "_PORT")
            if port.isdigit():
                ports.add(int(port))
    return [f"{name}:{p}" for p in sorted(ports)] or [name], {k: value(k) for k in own}


def render(
    project: str, running: bool, full: dict, base: dict, services: dict, published: dict
) -> str:
    configured = host_urls(full)
    rows = host_urls(published) if running else configured
    labels = list(services) + ["app", "serena"] + [label for label, _, _ in rows]
    col = max(12, *(len(x) for x in labels)) + 1
    out = [
        f"{project} ({'running' if running else 'not running: start it with roke'})",
        "",
        "Published ports (running containers)" if running else "Configured ports (project stopped)",
    ]
    if not rows:
        out.append(
            "  none" if running else "  none: roke -p PORT for the app; services publish their UIs"
        )
    out += [f"  {label:<{col}}{url} {note}".rstrip() for label, url, note in rows]
    if running and rows != configured:
        out += ["", "Configured ports (next start)"]
        out += [f"  {label:<{col}}{url} {note}" for label, url, note in configured] or ["  none"]
        out.append("  Settings differ from the running containers; applied on the next start.")
    out += ["", "Reach from inside the box"]
    if not services:
        out.append("  no services: roke service add NAME, or -s LIST for one run")
    for name, conf in services.items():
        addresses, _ = service_info(name, conf, base, full)
        out.append(f"  {name:<{col}}" + " · ".join(addresses))
    others = sorted(
        n for n in full.get("services", {}) if n not in ("box", "gateway") and n not in services
    )
    if others:
        out += ["", "Other containers of the project (from its compose.yaml): " + ", ".join(others)]
    if services:
        out += ["", "The variables each service gives the box: roke service show NAME"]
    return "\n".join(out)
