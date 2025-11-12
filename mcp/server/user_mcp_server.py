import logging

from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult, TextContent

mcp = FastMCP(
    name="MCP server Alpha 🚀",
    instructions="""
        This server provides user information services.
    """,
)


class ContextMocker(Context):
    def __init__(self):
        super().__init__(mcp)
        self.logger = logging.getLogger('ContextMocker')


@mcp.tool(
    tags={'user'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def get_user_name(user_id: str, ctx: Context = None) -> ToolResult:
    """
    Retrieves a user's name based on their user ID.

    This function takes a user ID string and returns the corresponding user name
    from a predefined mapping. If the user ID is not found, returns None.

    Args:
        user_id (str): The ID of the user to look up
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        ToolResult: Result object containing:
            - Text content with the user's name
            - Structured content with the name result
    """
    if ctx is None:
        ctx: ContextMocker = ContextMocker()
    await ctx.info('get_user_name tool invoked')
    nams_space = {
        'M4386': 'D.B.Cooper'
    }
    user_name = nams_space.get(user_id)
    await ctx.info(f'get_user_name return value [{user_name}]')
    return ToolResult(
        content=TextContent(type="text", text=user_name),
        structured_content={"result": user_name}
    )


@mcp.tool(
    tags={'user'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def get_user_address(user_id: str, ctx: Context = None) -> ToolResult:
    """
    Retrieves a user's address based on their user ID.

    This function takes a user ID string and returns the corresponding address
    from a predefined mapping. If the user ID is not found, returns None.

    Args:
        user_id (str): The ID of the user to look up
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        ToolResult: Result object containing:
            - Text content with the user's address
            - Structured content with the address result
    """
    if ctx is None:
        ctx: ContextMocker = ContextMocker()
    await ctx.info('get_user_address tool invoked')
    nams_space = {
        'M4386': 'Seattle Tacoma International Airport'
    }
    user_address = nams_space.get(user_id)
    await ctx.info(f'get_user_address return value [{user_address}]')
    return ToolResult(
        content=TextContent(type="text", text=user_address),
        structured_content={"result": user_address}
    )


@mcp.tool(
    tags={'user'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def get_user_booked_item(user_id: str, ctx: Context = None) -> ToolResult:
    """
    Retrieves a list of items booked by a user based on their user ID.

    This function takes a user ID string and returns the corresponding list of booked items
    from a predefined mapping. If the user ID is not found, returns None.

    Args:
        user_id (str): The ID of the user to look up
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        ToolResult: Result object containing:
            - Text content with the list of items booked by the user
            - Structured content with the booked items result
    """
    if ctx is None:
        ctx: ContextMocker = ContextMocker()
    await ctx.info('get_user_booked_item tool invoked')
    nams_space = {
        'M4386': ["BALI004", "TOKYO002"]
    }
    booked_item = nams_space.get(user_id)
    await ctx.info(f'get_user_booked_item return value [{booked_item}]')
    return ToolResult(
        content=TextContent(type="text", text=f"{booked_item}"),
        structured_content={"result": booked_item}
    )


if __name__ == "__main__":
    mcp.run()
