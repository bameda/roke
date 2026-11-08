# Penpot

For working on [Penpot](https://github.com/penpot/penpot) with a coding agent,
together with Penpot's own development environment, the **devenv**.

## How the pieces fit

Penpot's devenv already builds and runs Penpot: its main container has the
whole toolchain (JVM and Clojure, Node, Rust and Emscripten, ImageMagick...),
watches the code and rebuilds it, and its infrastructure runs PostgreSQL,
Valkey, RustFS, Mailpit and LDAP. What it does not do is isolate an agent:
its main container is privileged, and an agent on your machine connecting
to it has access to everything else.

So each one does its part:

- **the devenv runs Penpot**, as usual, without its OpenCode;
- **roke runs the agent**, on the same checkout: when the agent changes a
  file, the devenv rebuilds it, and you see the result at
  <https://localhost:3449>.

The agent cannot build or test Penpot itself, since its toolchain lives in
the devenv: it edits the code, and you check it in the devenv.

## Setting it up

1. Start the devenv in your clone of Penpot, with its MCP server if you want
   the agent to use it:

   ```fish
   cd ~/src/penpot
   ./manage.sh run-devenv --agentic
   ```

2. Copy this configuration, named after the clone's directory (`penpot`):

   ```fish
   cp -r ~/.local/share/roke/examples/projects/penpot ~/.config/roke/projects/penpot
   ```

3. Start the agent in the same clone:

   ```fish
   cd ~/src/penpot
   roke
   ```

## The Penpot MCP server

[`mcps/penpot-devenv/`](mcps/penpot-devenv/) is an MCP server of this project
only: the one the devenv runs on your machine, on port 4401. It allows
`host:4401`, that port of your machine and nothing else, so the agent can
read and change the designs of the Penpot running in the devenv once you
connect its plugin. Without `--agentic`, remove it from `ROKE_MCPS` in
`project.env`.

For Penpot's hosted server instead, use the catalog's
[`penpot`](../../../mcps/penpot/README.md) MCP.

## Notes

- The devenv publishes its ports on every network interface of your
  machine, not only on `127.0.0.1`: the MCP server needs it to be reachable
  from Docker, but it is reachable from your network too.
- Serena is roke's (`ROKE_SERENA=1`); the devenv's, started with
  `--agentic`, is not used.
- To run an LDAP or other service of your own in the box instead, the
  catalog has [`ldap`](../../../services/ldap/README.md), the same test
  directory the devenv uses.
