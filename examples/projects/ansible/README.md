# Example: Ansible

For a repository of Ansible roles and playbooks. The agent writes and
refactors them, validates them with `ansible-lint`, and **runs them for
real** against disposable `ssh-target` hosts. Your real infrastructure stays
out of reach: you apply the result from your host.

## What it sets up

- **`project.env`**: the `ssh-target` service.
- **`compose.yaml`**: a second target host, so playbooks can be tested
  against a `web` and a `db` group.
- **`AGENTS.md`**: the rules for the agent: test inventory only,
  idempotence checks, no secrets.

## In the project

Add a `mise.toml`, so ansible is installed in the box:

```toml
[tools]
python = "3.13"
"pipx:ansible" = "latest"
"pipx:ansible-lint" = "latest"
```

And a test inventory with the box's hosts, `inventories/test/hosts.ini`:

```ini
[web]
ssh-target

[db]
ssh-target-db
```

## Check it

From `roke shell`:

```bash
ansible -i inventories/test all -m ping
ansible-playbook -i inventories/test site.yml
```

Once a playbook works, run it from your host against the real inventory,
first with `--check --diff`. See [ssh-target](../../../catalog/services/ssh-target/README.md)
for its limitations (no systemd).
