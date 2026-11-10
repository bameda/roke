# Troubleshooting

- [Common problems](#common-problems)
- [Known limitations](#known-limitations)
- [Maintenance](#maintenance)

## Common problems

Run `roke doctor` in a project to check its configuration, MCP requirements,
Docker, the box image and Compose. Each line names the check, then reports
`OK` or `FAIL` and tells you what to fix. Use `roke settings` to see the
settings in effect.
The diagnostic reports names of missing variables without printing their values.

To save a report for an issue, use:

```bash
roke doctor --yaml > roke-diagnostic.yaml
```

It contains check results and versions of roke (`roke`), Python, the Docker client
(`docker_client`), Docker Engine (`docker_engine`) and Docker Compose
(`docker_compose`, previously `compose`), without environment
values, project paths, tokens or raw error output from configuration tools.
The top-level `ok` is `true` when all checks pass and `false` otherwise.
Versions that cannot be read are omitted; if the daemon is unavailable,
the Docker client version can still be reported without an Engine version.
Errors that could quote configuration values are replaced with an action to
run locally. Normal `roke doctor` keeps its detailed local error messages.
The command still exits nonzero if a check fails; the report is written even
then. No project configuration or registry entries are changed.

To check just the installed roke version, run `roke version` or
`roke --version`. It does not need Docker or project configuration.
A `-dev` suffix identifies a version
under development rather than a published release.

### `unknown option for roke run: --down`

Actions are commands, written without dashes: `roke down`, not
`roke --down`. Only the options that change how the agent starts are
options (`-s`, `-p`, `--agent`...). `roke help` lists every command.

### `configuration directory not found`

Run `roke init`, or `./install.sh` from the repository, to create
`~/.config/roke`.

### `Docker state unavailable`

`roke settings` can still show the configuration when Docker's container
query fails, but marks the runtime state as unavailable. Run `roke doctor`
to check the daemon. Commands that start sessions or stop all projects report
failed Docker queries as errors rather than assuming nothing is running.

### My settings are ignored

The project's configuration directory is named after its registered ID,
which defaults to the directory name: for `~/src/my-app`, normally
`~/.config/roke/projects/my-app/`, with its settings in `project.env`.
`roke settings` shows the ID. The line `[roke] project: ...` printed on start
shows the services and options that were applied, and `roke settings`
shows every setting of the project and where it comes from.

### `project ID ... is registered at ...`

Use `roke project` to list registered IDs and locate missing paths.
Another path owns that ID. For a separate project, choose a new one with
`roke --id NAME`. If you moved the original project, stop its containers
before moving it, then use its existing ID from the new path once the old
path is gone. See [project IDs and moves](configuration.md#project-ids-and-moves).

### `could not load settings from ...`

The named `.env` file failed while Bash was reading it. Check its shell
syntax and any commands it runs. Settings files are sourced as shell files;
`roke settings edit` also checks their syntax when you close the editor.

### `the project is already running ...`

Another session of the same project is open, and starting this one would
recreate a container it uses, leaving it without network or services. To
run two agents at once, list them in `ROKE_PARALLEL_AGENTS` in the project's
`project.env` (see [several agents at once](../catalog/agents/README.md#several-agents-at-once));
otherwise use the same agent and options as the open session, or finish it
first (or run `roke down`).

### `mise ERROR ... GitHub artifact attestations verification failed`

mise verifies the signature of the tools it installs, and needs Sigstore's
trust root for it, from `tuf-repo-cdn.sigstore.dev`, which roke allows by
default. If you still see this, run `roke network blocked` to find what
else it tried to reach. Turning the verification off
(`MISE_GITHUB_ATTESTATIONS=false`) would install the tool without checking
where it comes from: allow what is missing instead.

### Something cannot connect (a download, an API, a database...)

The network is restricted by default. Run `roke network blocked` to see what the
project tried to reach and was denied, then allow it with
`roke network add DESTINATION` and start the project again. See
[Network](network.md).

For errors from a service, use `roke logs SERVICE` (for example,
`roke logs postgres`). `roke logs gateway` shows the network gateway's logs;
`roke logs -f` follows all project services. Compose options pass through, so
`roke logs --tail 100 --since 2h postgres` limits lines and filters by time.

### The app does not load in the browser

Publish its port (`-p 5173` or `ROKE_PORTS`) and make the dev server
listen on `0.0.0.0`, not `localhost`.

### `port is already allocated`

Another project, or something on your host, is using that port. For
service UIs, change their port in the project's settings (for example
`MAILPIT_UI_PORT=18025`); each service's README lists its variables.

### `choose a coding agent`

Several agents are installed in the image and none is selected. Choose the
default one with `roke agent use NAME --global` (or a project's own with
`roke agent use NAME`), or pass `--agent` for a single run. See
[Agents](../catalog/agents/README.md).

### `the agent '<name>' is not in ROKE_AGENTS` / `is not installed in the image`

The agent you chose is not in the image. Add it to `ROKE_AGENTS` in
`roke.env` and run `roke build`.

### `WARNING: <path> exists in the project's home volume and hides yours`

A file in the agent's configuration directory inside the box, left from an
older setup or created by the agent, takes precedence over the same file in
your configuration. Remove it: `roke shell`, then `rm <path>`.

### Permission errors on files in the box's home

Usually after changing UID or switching to rootless Docker. Reset the
project with `roke purge`: it deletes the box's home, so you will need to
log in again and tools are downloaded again, but also the project's
databases and other service data. To reset only the home, find its volume
with `docker volume ls | grep _home` and remove it with `docker volume rm`.

## Known limitations

- **Dragging images into the terminal** passes a host path that does not
  exist in the box. Copy the image into the project and refer to it from
  there.
- **No SSH keys in the box**: `git push` and `git pull` happen on the host.
- **Agent-specific limitations** are listed in each
  [agent's README](../catalog/agents/README.md), for example the lack of language
  servers in OpenCode 2.
- **No systemd** in the box or in `ssh-target`.

## Maintenance

```fish
roke build --no-cache          # update the image and the agents
docker volume ls | grep roke   # each project's home and data
cd ~/src/my-app && roke purge  # delete one project's services and data
```
