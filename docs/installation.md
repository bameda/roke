# Installation

- [Requirements](#requirements)
- [Install Docker](#install-docker)
- [Install roke](#install-roke)
- [Updating](#updating)
- [Rootless Docker](#rootless-docker)
- [Uninstalling](#uninstalling)

## Requirements

- Linux with **Docker Engine** and the **Docker Compose plugin ≥ 2.24**.
- **Python 3.10** or newer and **git**, which every current distribution
  ships (on Arch, `pacman -S python git`).
- Your user in the `docker` group, or [rootless Docker](#rootless-docker).

## Install Docker

### Arch Linux, CachyOS, Manjaro, EndeavourOS

```bash
sudo pacman -S --needed docker docker-compose docker-buildx git
sudo systemctl enable --now docker.service
```

### Debian and Ubuntu

Follow [Docker's installation guide](https://docs.docker.com/engine/install/)
for your distribution, including the Compose plugin. On derivatives, follow
its instructions for the base distribution.

### Other distributions

Follow [Docker's installation guide](https://docs.docker.com/engine/install/)
and make sure the Compose plugin is installed.

### After installing Docker

Let your user run Docker without `sudo`, then **log out and back in** for it
to take effect:

```bash
sudo usermod -aG docker $USER
```

Check that everything works:

```bash
docker compose version          # must be 2.24 or newer
docker run --rm hello-world
```

Being in the `docker` group is equivalent to having root access on the
host; [rootless Docker](#rootless-docker) avoids that.

## Install roke

```fish
curl -fsSL https://github.com/bameda/roke/releases/latest/download/install.sh | bash
```

The installer puts roke in `~/.local/share/roke`, links the command into
`~/.local/bin` and creates `~/.config/roke` without overwriting existing
settings. Add `~/.local/bin` to your `PATH` if needed.

To inspect the installer and verify its checksum before running it:

```fish
curl -fsSL https://github.com/bameda/roke/releases/latest/download/install.sh -o install.sh
curl -fsSL https://github.com/bameda/roke/releases/latest/download/SHA256SUMS -o SHA256SUMS
sha256sum -c SHA256SUMS
less install.sh
bash install.sh
```

Run it again at any time: if roke is already installed, it updates within
its saved channel. A checkout with local changes is left untouched.
Its settings are environment variables, placed before `bash`:

| Variable | Default | Description |
|---|---|---|
| `ROKE_CONFIG_REPO` | — | Your private configuration repository, cloned into `~/.config/roke` on the first install |
| `ROKE_DIR` | `~/.local/share/roke` | Where to install roke |
| `ROKE_VERSION` | `stable` for new installations | `stable`, `main`, or an explicit branch or tag to install |
| `ROKE_BIN_DIR` | `~/.local/bin` | Where to link the `roke` command |

To work on roke itself, clone the repository wherever you want and run
`./install.sh` from it: it uses that clone instead.

To follow development on `main`, install with:

```fish
curl -fsSL https://raw.githubusercontent.com/bameda/roke/main/install.sh \
  | ROKE_VERSION=main bash
```

Use `ROKE_VERSION=vX.Y.Z` to install a specific release. Subsequent updates
follow the stable channel rather than keeping that version pinned.
An explicit branch other than `main` is updated manually with Git.

Continue with [First steps](first-steps.md) to choose an agent, build the
images and start your project.

### On another machine, with your configuration repository

If you keep your configuration in a private repository (see
[Configuration](configuration.md#keeping-it-in-a-private-repository)), pass
its URL to the installer. It clones the repository into `~/.config/roke` and
adds any missing file from the examples:

```fish
curl -fsSL https://github.com/bameda/roke/releases/latest/download/install.sh \
  | ROKE_CONFIG_REPO=git@github.com:<you>/roke-config.git bash
```

Your secrets are not in that repository, so recreate
`~/.config/roke/secrets.env` by hand if you use it, or log in again from
the agent.

## Updating

```fish
roke update
roke build          # in each project, to rebuild its images
```

`roke update` follows the saved channel, `stable` by default. Switch with:

```fish
roke update --main       # follow development; remembered for later updates
roke update --stable     # return to the latest published stable release
```

Switching from `main` to `stable` can install an older version. An ordinary
`roke update` refuses to downgrade to an older release. Local changes and
unpushed commits are preserved: resolve them with Git before updating.
If you have checked out a different branch yourself, the updater stops
instead of switching it silently.

Running the installer again follows the same channel unless `ROKE_VERSION`
is set explicitly. Your configuration is not touched, and neither are the
versions of your projects' services, which each project keeps: `roke service`
shows which ones have a newer version, and `roke service upgrade` moves a
project on (see [Versions](../catalog/services/README.md#versions)). Read
[CHANGELOG.md](../CHANGELOG.md) or the GitHub Release notes before updating;
breaking changes and migration steps appear first.

`roke build` rebuilds the images only where something changed. Agents
installed from a channel (`latest`, `stable`) are not updated by it, since
Docker reuses the cached layer: run `roke build --no-cache` to fetch their newest
release, or pin versions with `ROKE_AGENT_VERSIONS` in `roke.env` and run
`roke build` after changing them. See [Agents](../catalog/agents/README.md).

## Rootless Docker

With [rootless Docker](https://docs.docker.com/engine/security/rootless/),
the Docker daemon runs as your user instead of root, so being able to use
Docker no longer means having root on the host.

The container's root maps to your host user, and every other UID to a
subordinate one. To keep the files the agent creates owned by you, add to
`~/.config/roke/roke.env`:

```dotenv
ROKE_HOST_UID=0
ROKE_HOST_GID=0
```

Then run `roke build --no-cache`. There is still no `sudo` in the box, and its
root is not root on your machine.

## Uninstalling

```fish
cd ~/src/my-project && roke purge       # for each project: services and data
docker image ls roke --format '{{.Repository}}:{{.Tag}}' | xargs -r docker image rm
docker image rm roke-gateway:latest
rm ~/.local/bin/roke
rm -rf ~/.local/share/roke
```

`~/.config/roke` is left in place, so remove it too if you no longer need
your configuration.
