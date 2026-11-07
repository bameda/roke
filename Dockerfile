# syntax=docker/dockerfile:1
#
# Working image for coding agents. It only sees what gets mounted into it
# (the project, its own $HOME in a volume and your agent configuration).
FROM debian:trixie-slim

# Host user's UID/GID, so files the agent creates in the project are owned
# by you. bin/roke passes them automatically.
ARG HOST_UID=1000
ARG HOST_GID=1000

# Coding agents to install (directories in agents/), space-separated, and
# optional versions as agent=version pairs ("opencode=2.2.5 claude=latest");
# agents without one get their install.sh's default.
ARG ROKE_AGENTS="claude codex opencode"
ARG ROKE_AGENT_VERSIONS=""

# PostgreSQL client tools (psql, pg_dump...) from the official PGDG repo.
# Keep it >= the server's major: pg_dump refuses to dump newer servers.
ARG POSTGRES_CLIENT_VERSION=18

# Serena (semantic code navigation/editing MCP). INSTALL_SERENA=0 skips it.
ARG INSTALL_SERENA=1
# renovate: datasource=pypi depName=serena-agent
ARG SERENA_VERSION=2.1.0
ARG SERENA_PYTHON=3.13

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Base tools. Specific languages (node, python, java, clojure, rust, go...)
# are installed per project with mise. The -dev libraries let mise compile
# Ruby and let native extensions build (pg, mysql2, psych...).
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl wget gnupg \
      git less nano vim-tiny tree file procps openssh-client \
      ripgrep fd-find jq \
      unzip zip xz-utils bzip2 zstd \
      build-essential pkg-config libssl-dev \
      python3 python3-venv python3-pip \
      nodejs npm \
      mariadb-client mariadb-client-compat redis-tools sqlite3 kcat \
      libyaml-dev zlib1g-dev libffi-dev libgmp-dev libreadline-dev \
      libmariadb-dev \
      ncurses-term \
    && ln -s /usr/bin/fdfind /usr/local/bin/fd \
    && rm -rf /var/lib/apt/lists/*

# PostgreSQL client from apt.postgresql.org (Debian's is older).
RUN install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
         https://www.postgresql.org/media/keys/ACCC4CF8.asc \
    && . /etc/os-release \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" \
         > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
         "postgresql-client-${POSTGRES_CLIENT_VERSION}" libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && psql --version

# mise: per-project version manager for languages and tools.
RUN curl -fsSL https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh \
    && mise --version

# uv: required by Serena and handy for Python projects.
RUN curl -LsSf https://astral.sh/uv/install.sh \
      | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh \
    && uv --version

# Serena, installed under /opt (outside the box's $HOME) with its own Python.
# A base config is generated with the dashboard disabled and no browser
# launch; the entrypoint copies it to ~/.serena on first use.
RUN if [ "${INSTALL_SERENA}" = "1" ]; then \
      set -eux; \
      export UV_TOOL_DIR=/opt/uv/tools UV_TOOL_BIN_DIR=/usr/local/bin \
             UV_PYTHON_INSTALL_DIR=/opt/uv/python UV_CACHE_DIR=/tmp/uv-cache; \
      uv tool install -p "${SERENA_PYTHON}" "serena-agent==${SERENA_VERSION}"; \
      tmpl="$(find /opt/uv/tools/serena-agent -name serena_config.template.yml | head -n1)"; \
      install -d /opt/serena; \
      sed -E \
        -e 's/^web_dashboard:.*/web_dashboard: False/' \
        -e 's/^web_dashboard_open_on_launch:.*/web_dashboard_open_on_launch: False/' \
        -e 's/^gui_log_window:.*/gui_log_window: False/' \
        "$tmpl" > /opt/serena/serena_config.base.yml; \
      rm -rf /tmp/uv-cache; \
      serena --help >/dev/null; \
    fi

# Unprivileged user with the same UID/GID as on the host. No sudo.
RUN set -eux; \
    if ! getent group "${HOST_GID}" >/dev/null; then groupadd -g "${HOST_GID}" dev; fi; \
    if getent passwd "${HOST_UID}" >/dev/null; then \
      userdel -r "$(getent passwd "${HOST_UID}" | cut -d: -f1)" || true; \
    fi; \
    useradd -m -u "${HOST_UID}" -g "${HOST_GID}" -s /bin/bash -d /home/dev dev; \
    install -d -o "${HOST_UID}" -g "${HOST_GID}" \
      /home/dev/.config \
      /home/dev/.local/bin /home/dev/.local/share /home/dev/.local/state \
      /home/dev/.cache /home/dev/.serena

# Coding agents: each agents/<agent>/install.sh runs as root, after the user
# exists so it can prepare directories the agent's setup.sh writes at start.
COPY agents/ /tmp/roke-agents/
RUN set -eu; \
    install -d /etc/roke; \
    : > /etc/roke/installed-agents; \
    for agent in ${ROKE_AGENTS}; do \
      [ -x "/tmp/roke-agents/${agent}/install.sh" ] \
        || { echo "unknown agent: ${agent}" >&2; exit 1; }; \
      version="$(printf '%s\n' ${ROKE_AGENT_VERSIONS} | sed -n "s/^${agent}=//p" | tail -n1)"; \
      echo "Installing ${agent} (${version:-default})"; \
      "/tmp/roke-agents/${agent}/install.sh" "${version:-default}"; \
      echo "${agent}" >> /etc/roke/installed-agents; \
    done; \
    rm -rf /tmp/roke-agents

COPY --chmod=0755 docker/entrypoint.sh /usr/local/bin/roke-entrypoint

ENV HOME=/home/dev \
    SHELL=/bin/bash \
    MISE_YES=1 \
    SERENA_HOME=/home/dev/.serena \
    npm_config_cache=/home/dev/.cache/npm \
    PATH=/home/dev/.local/share/mise/shims:/home/dev/.local/bin:/home/dev/.cargo/bin:${PATH}

USER dev
WORKDIR /home/dev

# Without a command, the entrypoint runs the agent selected with ROKE_AGENT.
ENTRYPOINT ["/usr/local/bin/roke-entrypoint"]
