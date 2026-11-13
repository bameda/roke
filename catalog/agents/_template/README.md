# Agent name (`myagent`)

One sentence on what the agent is; this first line is shown by `roke agent`.

## Install and update

Where `install.sh` installs it from, which versions `ROKE_AGENT_VERSIONS`
accepts (`myagent=...`) and the default.

## Log in

How to authenticate inside the box: an interactive login (where the
credentials are kept) or an API key in `secrets.env`.

## Your configuration

What goes in `~/.config/roke/agents/myagent/` and where `setup.sh` links
it.

## Web and editors

Whether `roke --ui` or `roke acp` work with it, and how: the adapter it uses
for editors, if it needs one.

## Instructions and Serena

Where the agent reads the box's instructions, and how Serena is registered:
add a row to [how roke configures each agent](../README.md#how-roke-configures-each-agent).

## Notes

Anything that works differently inside the box.
