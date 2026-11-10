# Mailpit (`mailpit`)

See [common service settings](../README.md#how-services-work).

**Enable**: `roke service add mailpit`.

Mailpit catches every email your app sends, so nothing reaches real
recipients, and shows it in a web inbox.

**Inside the box**

| Variable | Value |
|---|---|
| `SMTP_HOST` / `SMTP_PORT` | `mailpit` / `1025` |
| `MAILPIT_API` | `http://mailpit:8025/api` |

Configure your app's SMTP with that host and port, **without
authentication or TLS**.

**From your host**: open the inbox at <http://127.0.0.1:8025>.

**From the box.** The API lets the agent (or your tests) check what was sent:

```bash
curl -s "$MAILPIT_API/v1/messages" | jq '.messages[] | {Subject, To: [.To[].Address]}'
curl -s -X DELETE "$MAILPIT_API/v1/messages"     # empty the inbox
```

**Data**: not persisted; the inbox is emptied on `roke down`.

**Settings**

| Variable | Default |
|---|---|
| `MAILPIT_UI_PORT` | `8025` (change it if another project uses mailpit at the same time) |
| `MAILPIT_VERSION` | see [`compose.yaml`](compose.yaml); pinned per project |
