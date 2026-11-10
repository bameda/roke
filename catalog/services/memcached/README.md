# Memcached (`memcached`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add memcached`.

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
| `MEMCACHED_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
| `MEMCACHED_MEMORY_MB` | `128` |
