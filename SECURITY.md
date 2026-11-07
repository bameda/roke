# Security

roke's purpose is to keep a coding agent away from everything on your
machine but the project it works on, so security reports are especially
welcome.

## Reporting a vulnerability

**Do not open a public issue.** Report it privately through GitHub: on the
repository, go to **Security → Report a vulnerability**. If you cannot use
it, email [bameda+roke@gmail.com](mailto:bameda+roke@gmail.com) instead.
Please include:

- what the agent (or anything running in the box) can reach or do that it
  should not;
- how to reproduce it: roke's commit, your distribution and Docker version,
  and the relevant output of `roke settings`;
- if you know it, where the problem is and how it could be fixed.

This is a small project maintained in spare time: you will get an answer as
soon as possible, and the fix will be credited to you unless you prefer
otherwise.

## Scope

In scope, for example:

- escaping the box: reaching host files outside the project, the Docker
  socket, or getting capabilities or privileges;
- getting around the network restrictions: reaching destinations that are
  not allowed, from the box or from a service;
- getting around the guards that refuse to mount `$HOME`, `/`, the
  configuration directory or roke's repository;
- the agent changing its own configuration, the box's instructions or the
  gateway's rules.

Out of scope: what [Security](docs/security.md) lists as not protected, such
as the agent sending your project's code to a destination you allowed, or
code it writes that you later run on your host; and the coding agents' own
sandboxes, which roke does not rely on.

## Supported versions

Only the latest version on the `main` branch is supported.
