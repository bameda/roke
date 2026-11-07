# Memcached (`memcached`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=memcached` in `~/.config/roke/projects/<name>/project.env`, or `roke -s memcached`.

Memcached, a simple key-value cache.

**Inside the box**

| Variable | Value |
|---|---|
| `MEMCACHED_SERVERS` | `memcached:11211` |

**Explore it.** There is no dedicated client in the image; Python is enough
for a quick check:

```bash
python3 -c "import socket; s=socket.create_connection(('memcached',11211)); s.sendall(b'stats\r\n'); print(s.recv(4096).decode())"
```

Send `flush_all` instead of `stats` to empty it.

**Data**: not persisted.

**Settings**

| Variable | Default |
|---|---|
| `MEMCACHED_VERSION` | pinned per project; new projects get the default in [`compose.yaml`](compose.yaml) |
| `MEMCACHED_MEMORY_MB` | `128` |
