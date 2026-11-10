# Example projects

Optional project configurations for common stacks. You can start with the
commands in [First steps](../../docs/first-steps.md) and consult these
examples when you need more customization.

To use one as a starting point, copy it into your configuration, named after
your **project ID**, which defaults to the project's directory name:

```fish
cp -r ~/.local/share/roke/examples/projects/python-api ~/.config/roke/projects/my-api
```

Then adapt it: every file is optional, so delete what you do not need. The
README in each example explains what to add to the project itself
(usually a `mise.toml`).

| Example | For | Services | Shows |
|---|---|---|---|
| [`ansible`](ansible/) | Ansible roles and playbooks | `ssh-target` | Running playbooks against disposable hosts, several targets |
| [`helm-charts`](helm-charts/) | Helm charts | `kwok`, `registry` | Validating and installing charts without a real cluster, pushing to an OCI registry |
| [`python-api`](python-api/) | Python web API (FastAPI, Flask...) | `postgres`, `redis` | Adapting `DATABASE_URL` for SQLAlchemy, a test database |
| [`node-app`](node-app/) | Node.js app: frontend and API | `postgres`, `mailpit` | Several ports, checking emails from tests |
| [`go-service`](go-service/) | Go service | `postgres`, `nats` | gopls for Serena, golangci-lint |
| [`rust-api`](rust-api/) | Rust web API with sqlx | `postgres` | Compile-time query checks, a build directory apart from the host's |
| [`rails-app`](rails-app/) | Ruby on Rails app | `postgres`, `redis`, `mailpit` | Keeping tests away from the development database |
| [`java-spring`](java-spring/) | Spring Boot service | `postgres`, `kafka` | Spring properties from the environment, what to do with Testcontainers |
| [`clojure-app`](clojure-app/) | Clojure app with a REPL | `postgres`, `valkey` | Connecting your editor to the REPL in the box, Serena |
| [`penpot`](penpot/) | Penpot, with its own devenv | — | Leaving the build to another environment, a project-only MCP server on a port of your machine |
| [`reference`](reference/) | — | `postgres`, `valkey`, `mailpit`, `elasticsearch` | Every piece: secrets, compose override, a project-only service |

See [per-project settings](../../docs/configuration.md#per-project-settings)
for what each file does.
