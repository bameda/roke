# OpenLDAP for tests (`ldap`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `roke service add ldap` (or `roke -s ldap` for one run).

An [OpenLDAP server for tests](https://github.com/rroemhild/docker-test-openldap),
loaded with the `planetexpress.com` example domain and its Futurama users,
for apps that log in with LDAP. It is the same one Penpot's development
environment uses.

**Inside the box**

| Variable | Value |
|---|---|
| `LDAP_URL` | `ldap://ldap:10389` (`ldap://ldap:10636` for LDAPS) |
| `LDAP_BASE_DN` | `dc=planetexpress,dc=com` |
| `LDAP_USERS_DN` | `ou=people,dc=planetexpress,dc=com` |
| `LDAP_BIND_DN` / `LDAP_BIND_PASSWORD` | `cn=admin,dc=planetexpress,dc=com` / `GoodNewsEveryone` |

Users (`uid`, whose password is the same as the `uid`): `professor`, `fry`,
`zoidberg`, `hermes`, `leela`, `bender` and `amy`. Their email is
`<uid>@planetexpress.com`.

**Explore it**: the image has no LDAP client; ask the agent to install one
with mise, or query it from the app.

**Data**: none: the directory is the image's fixture, and changes are lost
when the container is recreated.

**Settings**

| Variable | Default |
|---|---|
| `LDAP_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
