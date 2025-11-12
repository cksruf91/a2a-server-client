import logging
from typing import List

from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult, TextContent

mcp = FastMCP(
    name="Product Manager MCP server🚀",
    instructions="""
        This server provides travel package information services including package details like name, price and description.
    """,
)

PROD_INFO = {
    "JEJU001": {
        "name": "제주도 3일 패키지 여행",
        "price": 599000,
        "description": "제주도의 주요 관광지를 모두 둘러보는 알찬 3일 일정. 한라산 등반, 성산일출봉 관광, 올레길 트래킹 포함. 호텔 숙박과 조식 제공."
    },
    "TOKYO002": {
        "name": "도쿄 자유여행 4일",
        "price": 899000,
        "description": "도쿄 시내 4성급 호텔 3박, 나리타 공항 왕복 항공권 포함. 디즈니랜드 입장권 옵션 선택 가능. 현지 교통패스 제공."
    },
    "EURO003": {
        "name": "유럽 핵심도시 투어 7일",
        "price": 2890000,
        "description": "파리, 로마, 바르셀로나를 둘러보는 황금코스. 에펠탑, 콜로세움, 사그라다 파밀리아 등 핵심 관광지 티켓 포함. 전 일정 가이드 동행."
    },
    "BALI004": {
        "name": "발리 휴양 패키지 5일",
        "price": 1290000,
        "description": "우붓과 꾸따를 모두 경험하는 완벽한 발리 여행. 프라이빗 풀빌라 숙박, 스파 트리트먼트 1회, 우붓 문화투어 포함."
    },
    "VIET005": {
        "name": "다낭 호이안 4일",
        "price": 699000,
        "description": "베트남의 인기 관광지를 한번에! 바나힐 입장권, 호이안 고대도시 투어, 마사지 1회 포함. 비치front 호텔 숙박과 조식 제공."
    }
}


class ContextMocker(Context):
    def __init__(self):
        super().__init__(mcp)
        self.logger = logging.getLogger('ContextMocker')


@mcp.tool(
    tags={'prod'},
    meta={'author': 'anonymous'},
    enabled=True
)
async def get_product_info(product_code: List[str], ctx: Context = None) -> ToolResult:
    """
    Gets travel package information for given product codes.

    Args:
        product_code (list[str]): List of product codes to retrieve information for
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        ToolResult: Product information including name, price and description for requested product codes
    """
    if ctx is None:
        ctx: ContextMocker = ContextMocker()
    await ctx.info('get_product_info tool invoked')
    result = {}
    for code in product_code:
        result.update({code: PROD_INFO[code]})
    return ToolResult(
        content=TextContent(type="text", text=f"{result}"),
        structured_content={"result": result}
    )


if __name__ == "__main__":
    mcp.run()
