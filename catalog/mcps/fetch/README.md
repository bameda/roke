# Fetch (`fetch`)

Part of the [MCP catalog](../README.md).

**Enable**: `roke mcp add fetch`.

[Fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch),
one of the MCP project's reference servers, runs inside the box and lets
the agent download web pages as markdown.

**Network**: it adds no destination, so in restricted mode it can only fetch
pages from the allowed destinations. Allow the sites you want the agent to
read with `roke network add`, or use it in open mode.
