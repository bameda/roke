# Ansible test host (`ssh-target`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add ssh-target` (or `roke -s ssh-target` for one run).

A disposable Debian machine for **testing Ansible playbooks** (or any SSH
automation) without touching real infrastructure.

What it provides:

- A Debian container reachable as `ssh-target`, with SSH, Python and a user
  `ansible` with passwordless sudo, so `become: true` works.
- A test key pair generated per project and mounted read-only in the box. The
  key only opens these targets; your real SSH keys never enter the box.
- `ANSIBLE_*` defaults preset inside the box, so a minimal inventory is
  enough.

**Inside the box**

| Variable | Value |
|---|---|
| `SSH_TARGET_HOST` / `SSH_TARGET_USER` | `ssh-target` / `ansible` |
| `SSH_TARGET_KEY` | `/run/ssh-target/id_ed25519` |
| `ANSIBLE_PRIVATE_KEY_FILE`, `ANSIBLE_REMOTE_USER` | the same key and user |
| `ANSIBLE_HOST_KEY_CHECKING` | `False` |

Values set in your inventory take precedence over these defaults.

## Setup

The [`ansible` example project](../../examples/projects/ansible/) has all
of this ready to copy.

In `projects/<name>/project.env`:

```dotenv
ROKE_SERVICES=ssh-target
```

In the project's `mise.toml`, so ansible is installed in the box:

```toml
[tools]
python = "3.13"
"pipx:ansible" = "latest"
"pipx:ansible-lint" = "latest"
```

And a test inventory in the project, for example `inventories/test/hosts.ini`:

```ini
[web]
ssh-target
```

The first `roke` builds the target's image; after that it starts in a
couple of seconds.

## Usage

Ask the agent to test the playbook against the test inventory, or do it
yourself from `roke shell`:

```bash
ansible -i inventories/test all -m ping
ansible-playbook -i inventories/test site.yml
ansible-playbook -i inventories/test site.yml  # 2nd run: changed=0
ssh -i "$SSH_TARGET_KEY" ansible@ssh-target    # look around by hand
```

The second run is the idempotence check: a well-written playbook must report
no changes. To start again from a clean machine, run `roke down`: the
target's filesystem is not persisted.

Once it works, apply it to your real infrastructure **from the host**, first
with `--check --diff`. The vault password and the real SSH keys stay outside
the box.

## Several targets or another distribution

To test against Ubuntu or another Debian release, set the base image in
`projects/<name>/project.env` (it must use apt) and rebuild with `roke build`:

```dotenv
SSH_TARGET_BASE_IMAGE=ubuntu:24.04
```

For several hosts (for example, a web and a db group), add more targets in
`projects/<name>/compose.yaml`; they share the same test key:

```yaml
services:
  box:
    depends_on:
      ssh-target-2:
        condition: service_healthy
  ssh-target-2:
    build:
      context: ./services/ssh-target
      args:
        BASE_IMAGE: ${SSH_TARGET_BASE_IMAGE:-debian:trixie-slim}
    environment:
      KEY_OWNER_UID: ${HOST_UID:-1000}
    volumes:
      - ssh-target-keys:/keys
```

## Limitations

- There is no systemd in the targets, so tasks such as
  `systemd: name=nginx state=started enabled=true` fail there. Validate those
  parts with `--check` against a real or virtual machine.
- Only Debian/Ubuntu bases are supported, since the image is built with apt.
- Molecule's Docker driver is not usable: it needs the Docker socket, which
  the box never gets.

**Settings**

| Variable | Default |
|---|---|
| `SSH_TARGET_BASE_IMAGE` | `debian:trixie-slim` |
