"""Where the project's app and services are, from the resolved compose
configuration: the URLs to open from the host, and each service's address
and variables inside the box. Each service's variables are told apart by
comparing the configuration with and without it."""

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
    """The URLs published on the host: (what, url, note)."""
    gateway = full.get("services", {}).get("gateway", {})
    fwd = forwards(full)
    rows = []
    for p in gateway.get("ports") or []:
        host, published, target = p.get("host_ip") or "", p.get("published"), str(p.get("target"))
        url = f"http://127.0.0.1:{published}"
        note = "" if host == "127.0.0.1" else "(also reachable from your network)"
        if target in fwd:
            label = fwd[target].split(":")[0]
        elif target == SERENA_DASHBOARD:
            label, url = "serena", url + "/dashboard/"
        else:
            label, note = "app", f"(box port {target}) {note}".strip()
        rows.append((label, url, note))
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


def render(project: str, running: bool, full: dict, base: dict, services: dict) -> str:
    rows = host_urls(full)
    labels = list(services) + ["app", "serena"] + [label for label, _, _ in rows]
    col = max(12, *(len(x) for x in labels)) + 1
    out = [
        f"{project} ({'running' if running else 'not running: start it with roke'})",
        "",
        "Open from your browser",
    ]
    if not rows:
        out.append("  nothing published: roke -p PORT for the app; services publish their UIs")
    out += [f"  {label:<{col}}{url} {note}".rstrip() for label, url, note in rows]
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
