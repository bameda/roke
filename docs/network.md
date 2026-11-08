# Network

By default, a roke project can only reach the destinations you allow. The
agent, and every service it controls, cannot send your code or secrets
anywhere else, nor reach your LAN or your VPN.

- [How the pieces fit](#how-the-pieces-fit)
- [Restricted and open mode](#restricted-and-open-mode)
- [Allowing destinations](#allowing-destinations)
- [A port of your machine](#a-port-of-your-machine)
- [When something cannot connect](#when-something-cannot-connect)
- [Publishing ports](#publishing-ports)
- [Limitations](#limitations)

## How the pieces fit

```mermaid
flowchart LR
    you["Your browser<br/>and tools"]

    subgraph project["A roke project"]
        direction LR
        subgraph ns["Shared network namespace"]
            box["<b>box</b><br/>the coding agent<br/><i>no capabilities</i>"]
            gateway["<b>gateway</b><br/>firewall + DNS filter<br/>publishes the ports"]
        end
        subgraph internal["Internal network: no route out"]
            postgres[("postgres")]
            mailpit["mailpit"]
            more["...other services"]
        end
    end

    internet(("Allowed<br/>destinations"))
    blocked(("Everything else:<br/>internet, LAN, VPN"))

    you -- "127.0.0.1:&lt;port&gt;" --> gateway
    box --- gateway
    gateway <--> internal
    gateway -- "restricted mode:<br/>only what is allowed" --> internet
    gateway -. "denied" .-> blocked
```

- **The gateway** is the only container of the project with a route out.
  It runs the firewall (nftables) and a DNS filter (dnsmasq), and publishes
  the project's ports on `127.0.0.1`. It has `NET_ADMIN`, which it needs to
  set the firewall; the agent never runs in it.
- **The box**, where the agent runs, has no network of its own: it shares
  the gateway's. All its traffic therefore goes through the gateway's
  firewall, and it has no capabilities to change it.
- **The services** (databases, caches, Mailpit...) are on the project's
  internal network, which has no route out at all, in either mode. They can
  talk to the box and to each other, but not to the internet. This matters:
  a service the agent controls could otherwise be the way out, for example
  PostgreSQL running `COPY ... TO PROGRAM 'curl ...'`.

## Restricted and open mode

```dotenv
ROKE_NETWORK=restricted  # the default
ROKE_NETWORK=open        # no limits on the box's traffic
```

Set it in `roke.env` for every project, or in a project's `project.env`.
`roke --network open` overrides it for one run.

**Restricted** (default): the box can reach the project's services and the
allowed destinations, with any protocol (HTTPS, SSH, PostgreSQL, gRPC...).
Everything else is refused at once, so programs fail fast instead of hanging:

- **domains** that are not allowed do not resolve;
- **connections** to addresses that are not allowed are rejected, even if
  the program skips DNS or uses another DNS server: every DNS query from the
  box goes to the gateway's filter, whatever server it targets. This also
  stops data from leaking out through DNS queries.

**Open**: the box can reach anything your machine can, including your LAN
and your VPN. The services stay without a route out.

## Allowing destinations

The list of allowed destinations is built from several layers, so you only
add what is specific to you:

| Layer | Where | What it covers |
|---|---|---|
| Base | `docker/gateway/allow.txt` in this repository | What mise, the package managers and Serena need: GitHub, npm, PyPI, crates.io, Maven Central..., and Sigstore's trust root, with which mise verifies what it installs |
| Agent | `catalog/agents/<agent>/allow.txt` | The agent's API and login, and those of the agents in `ROKE_PARALLEL_AGENTS` (see [several agents at once](../catalog/agents/README.md#several-agents-at-once)) |
| Services | `catalog/services/<name>/allow.txt` | Rarely needed: services have no route out anyway |
| MCP servers | `allow` in `catalog/mcps/<name>/mcp.json` | What the project's [MCP servers](../catalog/mcps/README.md) need |
| Yours | `ROKE_NETWORK_ALLOW` in `roke.env` | Every project |
| The project's | `ROKE_NETWORK_ALLOW` in `project.env` | This project; adds to yours |

Each entry is one of:

| Entry | Allows |
|---|---|
| `example.com` | the domain and its subdomains, on any port |
| `*.example.com` | the same (written either way) |
| `db.example.com:5432` | the domain and its subdomains, on that port only |
| `203.0.113.10` | that address, on any port |
| `10.20.0.0/16:22` | that range, on that port only |
| `host:4401` | that port of your machine, the host (see [a port of your machine](#a-port-of-your-machine)) |

`roke settings` shows the resulting list for the current project, layer
by layer, so you can see where each entry comes from.

The quickest way to add one to the current project:

```fish
roke network add db.staging.example.com:5432
roke network add api.example.com
```

`roke network add` writes `ROKE_NETWORK_ALLOW` in the project's `project.env`. It
applies from the next start of the project. For every project, edit
`ROKE_NETWORK_ALLOW` in `roke.env`:

```dotenv
ROKE_NETWORK_ALLOW="api.example.com git.corp.example.com:22"
```

## A port of your machine

The box cannot reach your machine, the host, by design. To let it reach one
service running there, such as an MCP server or a development environment,
allow that port, one at a time:

```fish
roke network add host:4401
```

Inside the box, the host is `host.docker.internal`, so the agent reaches it
at `host.docker.internal:4401`. The whole host is never allowed: `host`
needs a port. The service on your machine must listen on an address Docker
can reach, such as `0.0.0.0`, not only on `127.0.0.1`.

## When something cannot connect

Run `roke network blocked` in the project, while it is running or right after:

```text
Domains the project looked up and were not allowed:
  registry.example.org                                 3 lookups

Addresses the project tried to connect to and were not allowed (last hour):
  203.0.113.7  tcp port 5432
```

Then allow what you need with `roke network add`, and start the project again.

Some tools look up destinations on their own, which roke blocks on purpose,
such as Serena's dashboard news. `roke network blocked` marks them with the
reason, so you can tell them from what you need. They are listed in
`docker/gateway/expected.txt`, for the tools in the box, and in an agent's
`catalog/agents/<agent>/expected.txt`.
If a project needs to reach many changing destinations, consider
`ROKE_NETWORK=open` in its `project.env`.

## Publishing ports

Since the box and the services have no ports of their own, the gateway
publishes them on `127.0.0.1`:

- **The box's**, with `-p` or `ROKE_PORTS`: the dev server listens in the
  gateway's network namespace, so `roke -p 5173` works as before.
- **The services' web UIs** (Mailpit, RustFS, Grafana, Jaeger...): each
  service's compose file asks the gateway to forward a port to it. See
  [publishing a service's port](../catalog/services/README.md#publishing-a-services-port).

## Limitations

- **Programs that resolve names on their own**, for example with DNS over
  HTTPS to a hardcoded address, or that connect to fixed IPs, need those
  addresses allowed as IPs or ranges.
- **IPv6** is not used: the gateway only answers IPv4 addresses.
- **CDNs**: allowing a domain allows the addresses it resolves to while the
  project runs. A CDN may serve other sites from the same addresses, so
  allowing a CDN-hosted domain implicitly allows those too.
- **Credentials** inside the box can still be sent to an allowed
  destination that accepts them, such as the agent's own API. Keep the
  allowed list short and use keys with spending limits.
