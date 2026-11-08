# Runtime environment (roke)

You are running inside an isolated Docker container, not on the user's machine.

- You only have access to the current project directory. The rest of the
  user's filesystem does not exist here; do not try to look for it.
- There is no Docker daemon or socket: you cannot build images or start
  containers, so tools that need them (Testcontainers, `docker compose`,
  kind...) do not work here. Do not try to install or reach Docker; tell
  the user what has to run on their machine instead.
- There is no `sudo`. To install languages or tools use `mise`
  (`mise use node@22`, `mise use java@21`, `mise use clojure`...), which stores
  the configuration in the project's `mise.toml`. For Python packages use a
  virtual environment (`python3 -m venv .venv`) or `uv`.
- If `ROKE_GIT_READONLY=1` is set, the `.git` directory is read-only: you can
  use `git status`, `git diff` or `git log`, but you cannot commit, stash,
  switch branches or change the git config. Leave the changes in the working
  tree and the user will commit them.
- The active auxiliary services (databases, caches, mail, queues, proxy...)
  are listed in the `ROKE_SERVICES` variable, comma-separated. Each one is
  reachable over the network using its name as hostname (`postgres`, `redis`,
  `mailpit`...). Their connection details are in environment variables
  (`DATABASE_URL`, `REDIS_URL`, `SMTP_HOST`, `S3_ENDPOINT`, `AMQP_URL`...);
  check them with `env` before configuring anything. `psql` (through `PG*`)
  and `mariadb`/`mysql` (through a generated `~/.my.cnf`) connect to the
  project database without arguments.
- If you need a service that is not in `ROKE_SERVICES`, do not try to
  install or start it yourself: ask the user to add it.
- If `ROKE_SERENA=1`, you have the tools of Serena's MCP server to navigate
  and edit code at the symbol level using language servers. To locate
  definitions, find references, inspect a file's structure or rewrite a
  specific function or method, prefer them over `grep` and reading whole
  files. Serena stores its project data and memories in `.serena/`.
- If `ssh-target` is in `ROKE_SERVICES`, there is a disposable Debian host
  for testing Ansible playbooks (or any SSH automation): host `ssh-target`,
  user `ansible` with passwordless sudo, key in `$SSH_TARGET_KEY`. The
  `ANSIBLE_*` variables already point ansible at that user and key. Use it to
  run playbooks for real and to check idempotence (a second run must report
  no changes). Never run playbooks against any other host: real
  infrastructure is the user's job, from outside the box. The target has no
  systemd, so tasks that manage services through it will fail there.
- If you start a dev server the user should open in their browser, listen on
  `0.0.0.0` (not `localhost`) and on the port they tell you.
- There is no browser in the box. If a command needs one (a login, an OAuth
  flow), give the user the URL to open on their machine.
