# Services

The catalog of auxiliary services: databases, caches, mail, storage, queues
and test infrastructure. Each one lives in its own directory under
`catalog/services/`, with a `compose.yaml` that defines it and a `README.md` that
explains how to use it. `roke service` shows what is available.

## Catalog

| Service | What for | Inside the box | On your host |
|---|---|---|---|
| [`playwright`](playwright/README.md) | Browsers for Playwright tests, which the box cannot run | `PW_TEST_CONNECT_WS_ENDPOINT` | — |
| [`postgres`](postgres/README.md) | PostgreSQL database | `postgres:5432`, `DATABASE_URL`, `PG*` | |
| [`mariadb`](mariadb/README.md) | MySQL-compatible database | `mariadb:3306`, `MYSQL_URL`, `MYSQL_*` | |
| [`mongodb`](mongodb/README.md) | Document database | `mongodb:27017`, `MONGODB_URL` | |
| [`redis`](redis/README.md) | Cache, sessions, queues | `redis:6379`, `REDIS_URL` | |
| [`valkey`](valkey/README.md) | Open-source Redis fork | `valkey:6379`, `VALKEY_URL` | |
| [`memcached`](memcached/README.md) | Key-value cache | `memcached:11211`, `MEMCACHED_SERVERS` | |
| [`ldap`](ldap/README.md) | OpenLDAP for tests, with example users | `ldap:10389`, `LDAP_URL`, `LDAP_BIND_DN` | — |
| [`mailpit`](mailpit/README.md) | Catches outgoing email | `mailpit:1025`, `SMTP_HOST`, `SMTP_PORT` | inbox at `127.0.0.1:8025` |
| [`rustfs`](rustfs/README.md) | S3-compatible storage | `rustfs:9000`, `S3_ENDPOINT`, `AWS_*` | console at `127.0.0.1:9001` |
| [`seaweedfs`](seaweedfs/README.md) | S3-compatible storage (alternative to `rustfs`) | `seaweedfs:8333`, `S3_ENDPOINT`, `AWS_*` | file browser at `127.0.0.1:8888` |
| [`rabbitmq`](rabbitmq/README.md) | Message broker | `rabbitmq:5672`, `AMQP_URL` | UI at `127.0.0.1:15672` |
| [`kafka`](kafka/README.md) | Kafka-compatible broker (Redpanda) | `kafka:9092`, `KAFKA_BOOTSTRAP_SERVERS` | |
| [`nats`](nats/README.md) | Messaging with JetStream | `nats:4222`, `NATS_URL` | |
| [`jaeger`](jaeger/README.md) | OpenTelemetry traces | `jaeger:4318`, `OTEL_EXPORTER_OTLP_ENDPOINT` | UI at `127.0.0.1:16686` |
| [`prometheus`](prometheus/README.md) | Metrics, scraped or pushed with OTLP | `prometheus:9090`, `OTEL_EXPORTER_OTLP_METRICS_*` | UI at `127.0.0.1:9090` |
| [`grafana`](grafana/README.md) | Dashboards, with Prometheus and Jaeger preconfigured | `grafana:3000`, `GRAFANA_URL` | UI at `127.0.0.1:3001` |
| [`wiremock`](wiremock/README.md) | Mock of external HTTP APIs | `wiremock:8080`, `WIREMOCK_URL` | |
| [`caddy`](caddy/README.md) | Reverse proxy | `PROXY_URL` | `127.0.0.1:8080` |
| [`kwok`](kwok/README.md) | Simulated Kubernetes API, for charts and manifests | `kwok:8080`, `KUBECONFIG` | |
| [`registry`](registry/README.md) | OCI registry, for Helm charts and artifacts | `registry:5000`, `OCI_REGISTRY` | `127.0.0.1:5000` |
| [`ssh-target`](ssh-target/README.md) | Disposable host for Ansible tests | `ssh-target:22`, `SSH_TARGET_*`, `ANSIBLE_*` | |

## How services work

Paths such as `projects/<id>/project.env` refer to your configuration
directory, `~/.config/roke` (see [Configuration](../../docs/configuration.md)).

**Enable** services for the project, or use `roke -s postgres,redis` for one run:

```fish
roke service add postgres redis mailpit
```

**Each service runs in its own container** and is
reachable from the box by its name (`postgres`, `redis`...). Its connection
details are set as environment variables in the box.

**`roke service show NAME`** shows, for the current project, the
service's version, its address inside the box, its web UI and the
variables it gives the box, with your settings applied, followed by its
README. `roke urls` lists the addresses and URLs of all the project's
services.

**Credentials** are for development; each service lists its defaults.
Published ports bind to `127.0.0.1` unless you override their mappings.

**Settings** (versions, credentials, ports) are changed through variables:
in `roke.env` for every project, or in `projects/<id>/project.env` for
one. Each service's README lists them with their defaults.

**Data** is per project: two projects using `postgres` get separate
databases. Services keep running when you exit the agent.

| Command | Effect |
|---|---|
| `roke down` | Stops the project's services. Data in volumes is kept. |
| `roke purge` | Stops them and deletes all their data. |

**No internet.** Services are on the project's internal network, with no
route out, so the agent cannot use one of them to send data out. They can
talk to the box and to each other. See [Network](../../docs/network.md).

**From your host.** Services with a web UI publish it on `127.0.0.1`
through the project's gateway (see each service's README). Databases are not
published by default; to connect a desktop tool (DBeaver, TablePlus,
RedisInsight...), publish the port as shown below.

### Versions

Each project keeps the versions of its services: updating roke never
changes them. The first time a project uses a service (`roke service add`,
or starting it), roke writes its version in the project's `project.env`,
using its `*_VERSION` variable. Versions you set yourself are kept.

When roke's default moves on, `roke service` shows it next to the project's
version, and you move the project on when you choose:

```fish
roke service upgrade postgres      # one service
roke service upgrade               # every service of the project
```

A major version of a service that keeps data (PostgreSQL, MongoDB, MariaDB...) may change the format of that data, so `upgrade`
skips it with a warning unless you add `--major`. Back the data up and read
the service's README first.

### Publishing a service's port

The project's network is internal, so a service cannot publish ports
itself: it asks the gateway to forward one. In `projects/<id>/compose.yaml`,
or in the service's own compose file:

```yaml
services:
  gateway:
    environment:
      ROKE_FORWARD_POSTGRES: "45432 postgres:5432"   # gateway port, then service:port
    ports:
      - "127.0.0.1:15432:45432"                      # host port -> gateway port
```

Use a gateway port that nothing else in the project uses (the catalog's
services use ports from 45000 up), and a host port that does not clash with
other projects or with services running on your machine.

## Adding your own service

Any image can become a service. Copy `catalog/services/_template/` and fill in its
two files: `compose.yaml` (the service) and `README.md` (how to use it).
Where you put the copy decides who can use it:

| Location | Available to |
|---|---|
| `~/.config/roke/projects/<id>/services/<name>/` | that project only |
| `~/.config/roke/services/<name>/` | all your projects |
| `catalog/services/<name>/` in this repository | everyone using roke (send a pull request) |

They are looked up in that order and the first one found wins, so a
project's service can replace one of yours, and yours can replace one from
the catalog. `roke service` marks them as `[project]` or `[yours]`.

The rules are few:

1. The service has the same name as its directory; that is its hostname.
2. It must be in the `depends_on` of `box`, which is what makes `roke`
   start it (with `service_healthy` if it has a healthcheck).
3. Connection variables go in the `environment` of `box`.
4. Volumes without `name:` are per project. To publish a port (a web UI),
   ask the gateway to forward it, as in
   [publishing a service's port](#publishing-a-services-port), with the host
   port in a variable so it can be changed.
5. The first comment line is the description shown by `roke service`.
6. The image's version goes in a variable ending in `_VERSION`, with a
   default: `image: example/thing:${THING_VERSION:-1.2.3}`. roke pins it in
   each project (see [Versions](#versions)), and a fixed version rather than
   `latest` is what makes that useful.
7. Relative paths resolve against the roke repository. To refer to
   files in your configuration, use `${ROKE_CONFIG_DIR}` or, for the
   project's directory, `${ROKE_PROJECT_CONFIG}`.
8. Document it in its `README.md`, following the structure of the existing
   ones. In the catalog, also add a row to the table above.

The [`reference`](../../examples/projects/reference/services/elasticsearch/)
example has a complete custom service.
