from langchain.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPServerClient(MultiServerMCPClient):
    def __init__(self, *args, tags: list[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tags = tags

    def _is_available_tool(self, tool: BaseTool) -> bool:
        if self.tags is None:
            return True
        tags = tool.metadata.get("_meta", {}).get("_fastmcp", {}).get("tags")
        return any(t in self.tags for t in tags)

    async def get_tools(self, *args, **kwargs) -> list[BaseTool]:
        filtered_tools = []
        tools = await super().get_tools(*args, **kwargs)
        for tool in tools:
            if self._is_available_tool(tool):
                filtered_tools.append(tool)
        return filtered_tools
