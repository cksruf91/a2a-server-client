from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient, MCPAgentTool


class ToolServerClient:
    def __init__(self, url: str):
        self.tool_server = MCPClient(lambda: streamablehttp_client(url))

    def list_tools(self) -> list[MCPAgentTool]:
        tools: list[MCPAgentTool] = []
        with self.tool_server:
            tools += self.tool_server.list_tools_sync()
        return tools
