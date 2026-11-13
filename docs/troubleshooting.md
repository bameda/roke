# Troubleshooting

- [Common problems](#common-problems)
- [Known limitations](#known-limitations)

## Common problems

Run `roke doctor` to diagnose configuration, Docker and image problems; it
runs every check it can, so a missing configuration or a directory roke
refuses still shows whether Docker works. `roke settings` shows effective
settings and their sources.

For a bug report, attach or paste this output:

```bash
roke doctor --yaml > roke-diagnostic.yaml
```

The report includes check results and installed versions, without secret
values or project paths. Failed checks still produce a report and a nonzero
exit status. Use plain `roke doctor` for detailed local error messages.

### `configuration directory not found`

Run `roke init`, or `./install.sh` from the repository, to create
`~/.config/roke`.

### `Docker state unavailable`

`roke settings` can still show the configuration when Docker's container
query fails, but marks the runtime state as unavailable. Run `roke doctor`
to check the daemon.

### My settings are ignored

Run `roke settings` to check the project ID and where each value comes from.
Use `roke settings edit` to edit the right file; see
[configuration precedence](configuration.md#per-project-settings).

### `project ID ... is registered at ...`

Use `roke project` to locate the path that owns the ID. For a separate
project, choose a new ID with `roke --id ID`. For a moved project, follow
[project IDs and moves](configuration.md#project-ids-and-moves).

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

Run `roke urls` to inspect published ports. Another project, or something
on your host, is using that port. For
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
