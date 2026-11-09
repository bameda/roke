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

roke and its scripts are started through their shebang, so they work the
same from fish, zsh or any other shell.

## Install Docker

### Arch Linux, CachyOS, Manjaro, EndeavourOS

```bash
sudo pacman -S --needed docker docker-compose docker-buildx git
sudo systemctl enable --now docker.service
```

### Debian and Ubuntu

The Docker packages in the distribution repositories (`docker.io`,
`docker-compose`...) can be too old, so use Docker's official repository.
This block works on both, since it reads the distribution and release from
`/etc/os-release`. Run it in **bash** (from fish, type `bash` first):

```bash
# Remove unofficial packages that conflict with Docker's own
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc 2>/dev/null | cut -f1)

# Add Docker's repository
sudo apt update
sudo apt install -y ca-certificates curl git
. /etc/os-release
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/$ID
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

# Install Docker Engine and the Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

On derivatives such as Linux Mint or Pop!_OS, `$ID` is not `ubuntu`:
replace `$ID` with `ubuntu` in the two URLs, and
`${UBUNTU_CODENAME:-$VERSION_CODENAME}` with the Ubuntu release it is based
on (for example `noble`).

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
curl -fsSL https://raw.githubusercontent.com/bameda/roke/main/install.sh | bash
```

The installer:

- clones roke into `~/.local/share/roke`;
- links the `roke` command into `~/.local/bin`, and tells you how to add it
  to your `PATH` if it is not there;
- creates your configuration directory, `~/.config/roke`, from the examples
  (see [Configuration](configuration.md)), never overwriting existing files;
- checks that Docker and its Compose plugin are installed.

The whole script runs from its last line, so a download cut halfway runs
nothing. To read it before running it:

```fish
curl -fsSL https://raw.githubusercontent.com/bameda/roke/main/install.sh -o install.sh
less install.sh
bash install.sh
```

Run it again at any time: if roke is already installed, it updates it.
Its settings are environment variables, placed before `bash`:

| Variable | Default | Description |
|---|---|---|
| `ROKE_CONFIG_REPO` | — | Your private configuration repository, cloned into `~/.config/roke` on the first install |
| `ROKE_DIR` | `~/.local/share/roke` | Where to install roke |
| `ROKE_VERSION` | `main` | Branch or tag to install |
| `ROKE_BIN_DIR` | `~/.local/bin` | Where to link the `roke` command |

To work on roke itself, clone the repository wherever you want and run
`./install.sh` from it: it uses that clone instead.

Then choose your default agent:

```fish
roke agent use claude --global      # or codex, or opencode; see catalog/agents/README.md
```

The image installs every agent by default. To make it smaller, keep only
the ones you use in `ROKE_AGENTS` (see [Agents](../catalog/agents/README.md)).

Then build the image and start the agent in a project:

```fish
cd ~/src/my-project
roke build
roke
```

`roke build` prepares the images; `roke` starts the agent. If the agent needs
authentication with its provider, follow its README
([Claude Code](../catalog/agents/claude/README.md#log-in),
[Codex](../catalog/agents/codex/README.md#log-in),
[OpenCode](../catalog/agents/opencode/README.md#log-in)). roke itself has no
account. The agent's login is stored in the
project's own home volume, not in your real `$HOME`, so you log in once
per project. An API key in `~/.config/roke/secrets.env` works for every
project instead.

### On another machine, with your configuration repository

If you keep your configuration in a private repository (see
[Configuration](configuration.md#keeping-it-in-a-private-repository)), pass
its URL to the installer. It clones the repository into `~/.config/roke` and
adds any missing file from the examples:

```fish
curl -fsSL https://raw.githubusercontent.com/bameda/roke/main/install.sh \
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

`roke update` pulls the latest version of roke; running the installer
again does the same. Your configuration is not touched, and neither are the
versions of your projects' services, which each project keeps: `roke service`
shows which ones have a newer version, and `roke service upgrade` moves a
project on (see [Versions](../catalog/services/README.md#versions)). Releases with
incompatible changes are marked with `!` in the commit history (for example
`feat(postgres)!: ...`): read their description, which explains what to
change.

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
