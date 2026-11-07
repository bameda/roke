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
#   ROKE_VERSION      branch or tag to install (default main)
#   ROKE_REPO         repository to install from (default bameda/roke on GitHub)
#   ROKE_BIN_DIR      where to link the roke command (default ~/.local/bin)
#
# Everything runs from the last line, so a download cut halfway runs nothing.

roke_install() {
  set -euo pipefail

  local repo="${ROKE_REPO:-https://github.com/bameda/roke.git}"
  local version="${ROKE_VERSION:-main}"
  local bin_dir="${ROKE_BIN_DIR:-$HOME/.local/bin}"
  local dir here

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
      say "updating $dir"
      git -C "$dir" fetch --quiet origin "$version"
      git -C "$dir" checkout --quiet "$version"
      git -C "$dir" merge --quiet --ff-only FETCH_HEAD \
        || die "$dir has local changes or diverged; update it by hand (git -C $dir status)"
    elif [[ -e "$dir" ]]; then
      die "$dir exists and is not a roke clone; move it away or set ROKE_DIR"
    else
      say "installing into $dir"
      mkdir -p "$(dirname "$dir")"
      git clone --quiet --branch "$version" "$repo" "$dir"
    fi
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
