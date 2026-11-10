#!/usr/bin/env bash
# Installs roke, or updates it if it is already installed.
#
# From the internet (clones roke into ~/.local/share/roke):
#   curl -fsSL https://raw.githubusercontent.com/bameda/roke/main/install.sh | bash
#
# From a clone of the repository (uses that clone):
#   ./install.sh
#
# Settings, as environment variables (put them before "bash" when piping:
# curl ... | ROKE_CONFIG_REPO=git@github.com:you/roke-config.git bash):
#   ROKE_CONFIG_REPO  your private configuration repository, cloned into
#                     ~/.config/roke on the first install
#   ROKE_DIR          where to install roke (default ~/.local/share/roke)
#   ROKE_VERSION      stable (default), main, or a branch or tag to install
#   ROKE_REPO         repository to install from (default bameda/roke on GitHub)
#   ROKE_BIN_DIR      where to link the roke command (default ~/.local/bin)
#
# Everything runs from the last line, so a download cut halfway runs nothing.

roke_install() {
  set -euo pipefail

  local repo="${ROKE_REPO:-https://github.com/bameda/roke.git}"
  local version="${ROKE_VERSION:-stable}"
  local bin_dir="${ROKE_BIN_DIR:-$HOME/.local/bin}"
  local dir here channel branch ref local_main status previous

  say()  { printf '\033[1m[roke]\033[0m %s\n' "$*"; }
  warn() { printf '\033[1;33m[roke]\033[0m %s\n' "$*" >&2; }
  die()  { printf '\033[1;31m[roke]\033[0m %s\n' "$*" >&2; exit 1; }

  command -v git >/dev/null || die "git is required: install it and try again"
  python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null \
    || die "roke needs Python 3.10 or newer (python3): install it and try again"

  # Run from a clone (./install.sh)? Then use it as it is. Piped from curl,
  # there is no script file, so it never picks up the current directory.
  here=""
  if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  fi
  if [[ -n "$here" && -x "$here/bin/roke" && -z "${ROKE_DIR:-}" ]]; then
    dir="$here"
    say "using this clone: $dir"
  else
    dir="${ROKE_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/roke}"
    if [[ -d "$dir/.git" ]]; then
      status="$(git -C "$dir" status --porcelain --untracked-files=all)"
      [[ -z "$status" ]] \
        || die "$dir has local changes; commit or move them before reinstalling"
      repo="$(git -C "$dir" config --get remote.origin.url)"
      branch="$(git -C "$dir" symbolic-ref --quiet --short HEAD || true)"
      if [[ -z "${ROKE_VERSION:-}" ]]; then
        version="$(git -C "$dir" config --local --get roke.channel || true)"
        [[ -n "$version" ]] || version="${branch:-stable}"
        [[ "$version" == stable || "$version" == main ]] \
          || die "this is a development clone; update it with Git or set ROKE_VERSION explicitly"
        [[ "$branch" == main && "$version" == main || -z "$branch" && "$version" == stable ]] \
          || die "the checkout differs from its update channel; update it with Git or set ROKE_VERSION"
      fi
    elif [[ -e "$dir" ]]; then
      die "$dir exists and is not a roke clone; move it away or set ROKE_DIR"
    fi

    channel=development
    [[ "$version" != main ]] || channel=main
    if [[ "$version" == stable ]]; then
      # Keep this bootstrap independent of an existing roke installation.
      version="$(python3 -I - "$repo" <<'PY'
import json
import re
import sys
import urllib.error
import urllib.request

match = re.fullmatch(
    r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+/[\w.-]+?)(?:\.git)?/?",
    sys.argv[1],
)
if not match:
    sys.exit("[roke] stable requires a GitHub repository; set ROKE_VERSION to a branch or tag")
request = urllib.request.Request(
    f"https://api.github.com/repos/{match[1]}/releases/latest",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "roke"},
)
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
except urllib.error.HTTPError as error:
    if error.code == 404:
        sys.exit("[roke] no stable release is available; set ROKE_VERSION=main to follow main")
    sys.exit(f"[roke] could not check the latest release (GitHub HTTP {error.code})")
except (OSError, ValueError):
    sys.exit("[roke] could not check the latest release; check connectivity to api.github.com")
if (
    not isinstance(release, dict)
    or release.get("draft") is not False
    or release.get("prerelease") is not False
    or not isinstance(release.get("tag_name"), str)
    or not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", release["tag_name"])
):
    sys.exit("[roke] GitHub did not return a stable vMAJOR.MINOR.PATCH release")
print(release["tag_name"])
PY
)"
    fi
    if [[ "$version" =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
      channel=stable
    fi

    if [[ -d "$dir/.git" ]]; then
      if [[ -z "${ROKE_VERSION:-}" && "$channel" == stable ]]; then
        previous="$(git -C "$dir" describe --tags --exact-match HEAD 2>/dev/null || true)"
        python3 -I -c '
import re, sys
previous, target = sys.argv[1:]
if re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", previous):
    if tuple(map(int, previous[1:].split("."))) > tuple(map(int, target[1:].split("."))):
        sys.exit("[roke] refusing to downgrade; set ROKE_VERSION explicitly to choose this version")
' "$previous" "$version"
      fi
      say "updating $dir"
      if [[ "$channel" == stable ]] || ! git -C "$dir" ls-remote --exit-code --heads origin "refs/heads/$version" >/dev/null; then
        ref="refs/tags/$version"
        git -C "$dir" fetch --quiet --no-tags origin "$ref:$ref"
      else
        ref="refs/remotes/origin/$version"
        git -C "$dir" fetch --quiet --no-tags origin "refs/heads/$version:$ref"
        local_main="$(git -C "$dir" rev-parse --verify "refs/heads/$version" 2>/dev/null || true)"
        if [[ -n "$local_main" ]]; then
          git -C "$dir" merge-base --is-ancestor "$local_main" "$ref" \
            || die "local $version has commits absent from origin; update it with Git"
        fi
      fi
      [[ -z "$(git -C "$dir" rev-list --max-count=1 HEAD --not --remotes --tags)" ]] \
        || die "the checkout has local commits; update it with Git"
      if [[ "$ref" == refs/tags/* ]]; then
        git -C "$dir" checkout --quiet --no-overwrite-ignore --detach "$ref"
      else
        git -C "$dir" checkout --quiet --no-overwrite-ignore "$version"
        git -C "$dir" merge --quiet --ff-only "$ref"
      fi
    else
      say "installing into $dir"
      mkdir -p "$(dirname "$dir")"
      git clone --quiet --branch "$version" "$repo" "$dir"
    fi
    git -C "$dir" config --local roke.channel "$channel"
    say "installed $version (update channel: $channel)"
  fi

  # The command.
  mkdir -p "$bin_dir"
  if [[ -L "$bin_dir/roke" && "$(readlink "$bin_dir/roke")" != "$dir/bin/roke" ]]; then
    warn "replacing $bin_dir/roke, which pointed to $(readlink "$bin_dir/roke")"
  elif [[ -e "$bin_dir/roke" && ! -L "$bin_dir/roke" ]]; then
    die "$bin_dir/roke exists and is not a link; move it away and try again"
  fi
  ln -sfn "$dir/bin/roke" "$bin_dir/roke"
  say "command: $bin_dir/roke"

  # The configuration: cloned from your repository on the first install, then
  # completed with any missing file (existing ones are never touched).
  local config="${ROKE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/roke}"
  if [[ -n "${ROKE_CONFIG_REPO:-}" && ! -e "$config" ]]; then
    "$dir/bin/roke" init "$ROKE_CONFIG_REPO"
  else
    [[ -n "${ROKE_CONFIG_REPO:-}" ]] && say "$config already exists; not cloning $ROKE_CONFIG_REPO"
    "$dir/bin/roke" init
  fi

  # Checks that do not stop the install.
  if ! command -v docker >/dev/null; then
    warn "Docker is not installed: see https://github.com/bameda/roke/blob/main/docs/installation.md"
  elif ! docker compose version >/dev/null 2>&1; then
    warn "the Docker Compose plugin is missing: see https://github.com/bameda/roke/blob/main/docs/installation.md"
  fi
  case ":$PATH:" in
    *":$bin_dir:"*) ;;
    *) warn "$bin_dir is not in your PATH. Add it:"
       warn "  fish:  fish_add_path $bin_dir"
       warn "  bash:  echo 'export PATH=\"$bin_dir:\$PATH\"' >> ~/.bashrc"
       warn "  zsh:   echo 'export PATH=\"$bin_dir:\$PATH\"' >> ~/.zshrc" ;;
  esac

  say "done. Next: roke agent use claude|codex|opencode --global, then roke build in a project"
}

roke_install "$@"
