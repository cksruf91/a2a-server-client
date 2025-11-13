from typing import Optional

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_toolset import ToolPredicate
from mcp.types import Tool


class ToolFilter(ToolPredicate):

    def __init__(self, tags: list[str] = None, *args, **kwargs):  # real signature unknown
        super().__init__(*args, **kwargs)
        if tags is None:
            tags = []
        self.tags = tags

    def __call__(self, tool: Tool, readonly_context: Optional[ReadonlyContext] = None) -> bool:
        meta = tool.raw_mcp_tool.meta.get('_fastmcp')
        return any([tag in meta['tags'] for tag in self.tags])
