#!/usr/bin/env bash
# Installs an Agent Client Protocol (ACP) adapter, the program an editor
# starts to talk to an agent (roke acp). Runs as root at build time, called by
# the install.sh of the agents that need an adapter.
#   $1  the npm package, for example @agentclientprotocol/claude-agent-acp
#   $2  its version
#   $3  the command to create for it, for example claude-agent-acp
#
# Adapters need Node.js 22, and the box's own Node.js, from Debian, is older, so
# they get a private one under /opt/acp, shared by all of them. Nothing else
# uses it. The adapters are installed without their optional packages: those
# are copies of the agent's own binary, which the image already has, and
# roke points the adapter to it (see the agent's setup.sh).
set -euo pipefail

package="$1" version="$2" command="$3"
prefix=/opt/acp
node_dir="$prefix/node"

if [[ ! -x "$node_dir/bin/node" ]]; then
  case "$(uname -m)" in
    x86_64) arch=x64 ;;
    aarch64) arch=arm64 ;;
    *) echo "no Node.js build for $(uname -m)" >&2; exit 1 ;;
  esac
  base="${ACP_NODE_BASE:-https://nodejs.org/dist/latest-v22.x}"  # overridden only by the tests
  work="$(mktemp -d)"
  curl -fsSL "$base/SHASUMS256.txt" -o "$work/SHASUMS256.txt"
  file="$(grep -oE "node-v22\.[0-9]+\.[0-9]+-linux-${arch}\.tar\.xz" "$work/SHASUMS256.txt" | head -n1)"
  [[ -n "$file" ]] || { echo "no Node.js 22 build for $arch at $base" >&2; exit 1; }
  curl -fsSL "$base/$file" -o "$work/$file"
  # The download must match the checksum that nodejs.org publishes for it.
  (cd "$work" && grep " ${file}\$" SHASUMS256.txt | sha256sum -c -)
  install -d "$node_dir"
  tar -xJf "$work/$file" -C "$node_dir" --strip-components=1
  rm -rf "$work"
fi

lib="$prefix/lib/$command"
install -d "$lib"
PATH="$node_dir/bin:$PATH" npm install --prefix "$lib" --omit=optional --ignore-scripts \
  --no-audit --no-fund "$package@$version"
PATH="$node_dir/bin:$PATH" npm cache clean --force

# The file the package's bin points to.
entry="$("$node_dir/bin/node" -p \
  "const d = require('$lib/node_modules/$package/package.json'); \
   typeof d.bin === 'string' ? d.bin : d.bin['$command']")"
[[ -f "$lib/node_modules/$package/$entry" ]] \
  || { echo "$package has no bin $command" >&2; exit 1; }

cat > "/usr/local/bin/$command" <<LAUNCHER
#!/bin/sh
exec $node_dir/bin/node $lib/node_modules/$package/$entry "\$@"
LAUNCHER
chmod 0755 "/usr/local/bin/$command"
"$command" --version >/dev/null 2>&1 || true
