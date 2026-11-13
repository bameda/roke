#!/usr/bin/env python3
"""A fake Agent Client Protocol adapter, for the tests of roke acp.

It answers initialize and session/new, and asks the editor for what a real one
could: the editor's files and terminal (fs/*, terminal/*). It logs every line
it receives to $FAKE_AGENT_LOG, and whether it was asked for a clean standard
input. Exits when the editor closes its side.
"""

import json
import os
import sys


def send(message):
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def serve(log):
    for line in sys.stdin:
        log.write(line if line.endswith("\n") else line + "\n")
        log.flush()
        try:
            message = json.loads(line)
        except ValueError:
            continue
        method = message.get("method")
        if method == "initialize":
            send({"jsonrpc": "2.0", "id": message["id"], "result": {"protocolVersion": 1}})
            # What an adapter could ask of the editor, and a legitimate update.
            read = {"path": "/etc/passwd"}
            send({"jsonrpc": "2.0", "id": 100, "method": "fs/read_text_file", "params": read})
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 101,
                    "method": "terminal/create",
                    "params": {"command": "id"},
                }
            )
            send({"jsonrpc": "2.0", "method": "terminal/output", "params": {"terminalId": "t"}})
            send({"jsonrpc": "2.0", "method": "session/update", "params": {"update": "hello"}})
        elif method == "session/new":
            send({"jsonrpc": "2.0", "id": message["id"], "result": {"sessionId": "s1"}})


with open(os.environ["FAKE_AGENT_LOG"], "a") as log:
    serve(log)
sys.exit(int(os.environ.get("FAKE_AGENT_EXIT", "0")))
