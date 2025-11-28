from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient, MCPAgentTool


class ToolServerClient:
    def __init__(self, url: str, tags: list[str] = None) -> None:
        self.tool_server = MCPClient(lambda: streamablehttp_client(url))
        self.tags = tags

    def list_tools(self) -> list[MCPAgentTool]:
        tools: list[MCPAgentTool] = []
        with self.tool_server:
            for tool in self.tool_server.list_tools_sync():
                tool = self._filter_mcp_tools(tool)
                if tool is not None:
                    tools.append(tool)
        return tools

    def _filter_mcp_tools(self, tool: MCPAgentTool) -> MCPAgentTool | None:
        meta = tool.mcp_tool.meta.get('_fastmcp')
        if (self.tags is None) or (not self.tags):
            return tool
        is_available = any([tag in meta['tags'] for tag in self.tags])
        return tool if is_available else None
