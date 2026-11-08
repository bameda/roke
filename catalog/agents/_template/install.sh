#!/usr/bin/env bash
# Installs the agent in the image. Runs as root at build time, after the
# box's user ("dev") exists.
#   $1  version from ROKE_AGENT_VERSIONS, or "default"
set -euo pipefail

version="${1:-default}"
[[ "$version" == default ]] && version=latest

# Install it system-wide (not in the user's home, which is a volume):
# npm install -g "myagent@${version}"
# myagent --version

# Prepare any directory setup.sh writes to at start, owned by the user:
# install -d -o dev -g "$(id -g dev)" /etc/myagent
