"""roke urls: where the project's app and services are, from the resolved
compose configuration. Each service's variables are told apart by comparing
the configuration with and without it."""

import re


def render(project: str, running: bool, full: dict, base: dict, services: dict) -> str:
    full_services = full.get("services", {})
    box_env = full_services.get("box", {}).get("environment") or {}
    base_env = base.get("services", {}).get("box", {}).get("environment") or {}
    gateway = full_services.get("gateway", {})
    forwards = {}
    for key, value in (gateway.get("environment") or {}).items():
        if key.startswith("ROKE_FORWARD_") and value:
            port, target = value.split(None, 1)
            forwards[str(port)] = target

    labels = list(services) + ["app", "serena"] + [t.split(":")[0] for t in forwards.values()]
    col = max(12, *(len(x) for x in labels)) + 1
    out = [
        f"{project} ({'running' if running else 'not running: start it with roke'})",
        "",
        "Open from your browser",
    ]

    rows = []
    for p in gateway.get("ports") or []:
        host, published, target = p.get("host_ip") or "", p.get("published"), str(p.get("target"))
        url = f"http://127.0.0.1:{published}"
        note = "" if host == "127.0.0.1" else "(also reachable from your network)"
        if target in forwards:
            label = forwards[target].split(":")[0]
        elif target == "24282":
            label, url = "serena", url + "/dashboard/"
        else:
            label, note = "app", f"(box port {target}) {note}".strip()
        rows.append((label, url, note))
    if not rows:
        out.append("  nothing published: roke -p PORT for the app; services publish their UIs")
    for label, url, note in sorted(rows):
        out.append(f"  {label:<{col}}{url} {note}".rstrip())

    out += ["", "Reach from inside the box"]
    if not services:
        out.append("  no services: roke service add NAME, or -s LIST for one run")
    for name, conf in services.items():
        env = conf.get("services", {}).get("box", {}).get("environment") or {}
        own = [k for k in env if k not in base_env]

        def value(key: str, env: dict = env) -> str:
            """The variable's resolved value in the full configuration."""
            return str(box_env.get(key, env.get(key, "")))

        ports = {int(m) for k in own for m in re.findall(rf"\b{re.escape(name)}:(\d+)", value(k))}
        ports |= {int(t.split(":")[1]) for t in forwards.values() if t.split(":")[0] == name}
        for k in own:  # pairs such as SMTP_HOST=mailpit and SMTP_PORT=1025
            if k.endswith("_HOST") and value(k) == name:
                port = str(box_env.get(k[:-5] + "_PORT", env.get(k[:-5] + "_PORT", "")))
                if port.isdigit():
                    ports.add(int(port))
        out.append(f"  {name:<{col}}" + (" · ".join(f"{name}:{p}" for p in sorted(ports)) or name))
        out += [" " * (2 + col) + f"{k}={value(k)}" for k in own]

    others = sorted(n for n in full_services if n not in ("box", "gateway") and n not in services)
    if others:
        out += ["", "Other containers of the project (from its compose.yaml): " + ", ".join(others)]
    return "\n".join(out)
