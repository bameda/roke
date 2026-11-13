# Codex CLI (`codex`)

[Codex CLI](https://developers.openai.com/codex/cli), OpenAI's coding agent, which works with a ChatGPT plan or an OpenAI API key.

## Install and update

Installed from the `@openai/codex` npm package. The version is
`ROKE_AGENT_VERSIONS="codex=..."`: an npm version or tag, `latest` by
default. The image also gets `codex-acp`, the adapter editors use (see below).

## Log in

The box has no browser, so use the device-code flow: run

```fish
roke exec -a codex codex login --device-auth
```

and follow it: it shows a URL and a code to enter in your browser, on your
host. The credentials are kept in `~/.codex/auth.json`, in the project's
home volume, so you log in once per project. Alternatively, put
`OPENAI_API_KEY` in `~/.config/roke/secrets.env` and log in with it from
`roke shell -a codex`: `printenv OPENAI_API_KEY | codex login --with-api-key`.

## Web and editors

Codex has no `--ui`. `roke acp -a codex` serves it to an editor through the
`codex-acp` adapter, which runs the image's `codex`, with the same
configuration as a terminal session. See [editors](../../../docs/editors.md).

## Your configuration

`~/.config/roke/agents/codex/` is linked into `~/.codex`: `config.toml`
(model, approvals, MCP servers...), plus `prompts/` and `skills/` if you use
them. It is mounted read-only, so edit it on your host. An `AGENTS.md` there
holds instructions for Codex only, added to the combined instructions.

How roke gives Codex the instructions, MCP servers and approvals is in
[how roke configures each agent](../README.md#how-roke-configures-each-agent).

## Notes

- roke sets `sandbox_mode = "danger-full-access"`; the
  [box provides isolation](../../../docs/security.md#the-agent-is-not-trusted).
  Your command approval policy is unchanged. An explicit `sandbox_mode` in
  your own `config.toml` overrides this setting.
- **The project is trusted**, so Codex does not ask "Trust this folder?":
  whatever the project's own Codex settings run, they run in the box too. To
  treat a project as untrusted, set its `trust_level` in your `config.toml`.
- The approvals `roke mcp allow` and `ask` generate also cover Serena; your
  personal settings and per-tool overrides keep their native precedence. See
  [tool approvals](../../mcps/README.md#tool-approvals).
