# Codex CLI (`codex`)

[Codex CLI](https://developers.openai.com/codex/cli), OpenAI's coding agent, which works with a ChatGPT plan or an OpenAI API key.

## Install and update

Installed from the `@openai/codex` npm package. The version is
`ROKE_AGENT_VERSIONS="codex=..."`: an npm version or tag, `latest` by
default. With `latest`, run `roke build --no-cache` to fetch a newer one.

The box turns off Codex's update check on startup
(`check_for_update_on_startup`), since the image decides the version.

## Log in

The box has no browser, so use the device-code flow: run

```fish
roke exec codex login --device-auth
```

and follow it: it shows a URL and a code to enter in your browser, on your
host. The credentials are kept in `~/.codex/auth.json`, in the project's
home volume, so you log in once per project. Alternatively, put
`OPENAI_API_KEY` in `~/.config/roke/secrets.env` and log in with it from
`roke shell`: `printenv OPENAI_API_KEY | codex login --with-api-key`.

## Your configuration

`~/.config/roke/agents/codex/` is linked into `~/.codex`: `config.toml`
(model, approvals, MCP servers...), plus `prompts/` and `skills/` if you use
them. It is mounted read-only, so edit it on your host. An `AGENTS.md` there
holds instructions for Codex only, added to the combined instructions.

## Instructions, MCP servers and Serena

- **Instructions**: the combined instructions (see
  [agents](../README.md#instructions-for-the-agent)) become
  `~/.codex/AGENTS.md`, Codex's global instructions file. The project's own
  `AGENTS.md` is read as usual.
- **MCP servers**: those of the project (`roke mcp`) are registered next to
  Serena, in the same place; see [MCP servers](../../mcps/README.md).
- **Serena**: registered as an MCP server in Codex's system configuration
  (`/etc/codex/config.toml`, regenerated on every start), with Serena's
  `codex` context. MCP servers in your `config.toml` keep working alongside
  it.

## Notes

- **Sandboxing.** Codex runs the commands it executes in its own sandbox.
  Inside the box it may work or not, depending on what the container
  allows; either way roke does not rely on it, since the box is the
  boundary (see [Security](../../docs/security.md#the-agent-is-not-trusted)).
  If Codex reports that its sandbox cannot start, set
  `sandbox_mode = "danger-full-access"` in your `config.toml`: inside the box,
  that means full access to the project only.
- Resume the last session with `roke continue`, which runs
  `codex resume --last`.
