#!/usr/bin/env bash
# Prepares the test key pair (shared with the box through a
# volume) and starts sshd in the foreground.
set -euo pipefail

keys=/keys
owner="${KEY_OWNER_UID:-1000}"

mkdir -p "$keys"

# Several targets may start at once and share the same volume: generate the
# key pair only once, under a lock.
exec 9>"$keys/.lock"
flock 9
if [[ ! -f "$keys/id_ed25519" ]]; then
  ssh-keygen -q -t ed25519 -N '' -C roke-ssh-target -f "$keys/id_ed25519"
fi
# The private key must belong to the box user, or ssh refuses it.
chown "$owner" "$keys/id_ed25519" "$keys/id_ed25519.pub"
chmod 600 "$keys/id_ed25519"
chmod 644 "$keys/id_ed25519.pub"
install -d -m 700 -o ansible -g ansible /home/ansible/.ssh
install -m 600 -o ansible -g ansible "$keys/id_ed25519.pub" /home/ansible/.ssh/authorized_keys
flock -u 9

ssh-keygen -A >/dev/null   # host keys
exec /usr/sbin/sshd -D -e
