# Mailpit (`mailpit`)

Part of the [service catalog](../README.md). See
[How services work](../README.md#how-services-work) for what is common
to every service: enabling, data, `roke down`/`roke purge` and host access.

**Enable**: `ROKE_SERVICES=mailpit` in `~/.config/roke/projects/<name>/project.env`, or `roke -s mailpit`.

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

To send a test email:

```bash
python3 -c "
import smtplib; from email.message import EmailMessage
m = EmailMessage(); m['From'] = 'app@example.com'; m['To'] = 'user@example.com'
m['Subject'] = 'Test'; m.set_content('Hello from the box')
smtplib.SMTP('mailpit', 1025).send_message(m)"
```

**Data**: not persisted; the inbox is emptied on `roke down`.

**Settings**

| Variable | Default |
|---|---|
| `MAILPIT_UI_PORT` | `8025` (change it if another project uses mailpit at the same time) |
| `MAILPIT_VERSION` | `v1.33.0` |
