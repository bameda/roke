# GitHub (`github`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add github`.

GitHub's official [remote MCP server](https://github.com/github/github-mcp-server):
repositories, issues, pull requests, Actions and more, acting as the user
whose token it carries.

**Needs** `GITHUB_PAT` in `~/.config/roke/secrets.env` (or the project's
`secrets.env`): a [fine-grained personal access token](https://github.com/settings/personal-access-tokens)
with access only to the repositories and permissions the agent needs. The
agent can do with the server whatever the token allows, so prefer
read-only permissions unless you want it to open issues or pull requests.

For read-only access whatever the token allows, use your own copy of this
MCP (see [Adding your own MCP](../README.md#adding-your-own-mcp)) with the
URL `https://api.githubcopilot.com/mcp/readonly`.

**Network**: allows `api.githubcopilot.com`.
