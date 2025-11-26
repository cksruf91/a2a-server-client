import logging
from functools import wraps

from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult, TextContent
from google import genai
from google.genai import types

mcp = FastMCP(
    name="Travel MCP server 🚀",
    instructions="""
        This server provides Travel information services.
    """,
)


class MapGroundingAgent:
    client = genai.Client()

    def __init__(self, model: str = 'gemini-2.5-flash-lite', config: types.GenerateContentConfig = None):
        self.model = model
        self.config = config or types.GenerateContentConfig(
            tools=[types.Tool(google_maps=types.GoogleMaps())],  # Turn on grounding with Google Maps
        )

    def map_grounding(self, instruction: str) -> types.GenerateContentResponse:
        return self.client.models.generate_content(
            model=self.model,
            contents=instruction,
            config=self.config
        )


def parsing_map_grounding_text_response(response: types.GenerateContentResponse) -> str:
    candidate = response.candidates[0]
    for part in candidate.content.parts:
        if part.text is not None:
            return part.text
    raise RuntimeError("parsing response failed, Response : {}".format(response))


class ContextMocker(Context):
    def __init__(self):
        super().__init__(mcp)
        self.logger = logging.getLogger('ContextMocker')


def ensure_context(func):
    """Decorator to ensure ctx parameter is not None by providing ContextMocker as default."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if 'ctx' not in kwargs or kwargs['ctx'] is None:
            kwargs['ctx'] = ContextMocker()
        return await func(*args, **kwargs)

    return wrapper


@mcp.tool(
    tags={'travel', 'guide'},
    meta={'author': 'anonymous'},
    enabled=True
)
@ensure_context
async def get_place_recommendation(
        city_or_country_name: str,
        theme: str = None,
        ctx: Context = None
) -> ToolResult:
    """Gets place recommendations for a specified city or country.

    Use this tool to find recommended places to visit in a city or country.
    You can optionally filter by theme to get specific types of recommendations.

    Args:
        city_or_country_name (str): Name of the city or country to get recommendations for.
        theme (str, optional): Type of places to recommend. Supported values:
            - "restaurant" or "맛집": Restaurants and dining spots
            - "tourist" or "관광": Tourist attractions and sightseeing spots
            - "cafe" or "카페": Cafes and coffee shops
            - "shopping" or "쇼핑": Shopping areas and markets
            - "nature" or "자연": Parks and natural attractions
            If not specified, returns general tourist attractions.
        ctx (Context, optional): Internal use only, ignore this parameter.

    Returns:
        A list of recommended places with descriptions for the specified location and theme.
    """
    await ctx.info(
        'get_place_recommendation tool invoked, '
        'params(city_or_country_name={}, theme={})'.format(city_or_country_name, theme)
    )
    gemini = MapGroundingAgent()

    # Build instruction based on theme
    if theme:
        # Map common Korean themes to English descriptions
        theme_mapping = {
            "맛집": "popular restaurants and dining spots",
            "restaurant": "popular restaurants and dining spots",
            "관광": "key tourist attractions and sightseeing spots",
            "tourist": "key tourist attractions and sightseeing spots",
            "카페": "popular cafes and coffee shops",
            "cafe": "popular cafes and coffee shops",
            "쇼핑": "shopping areas and markets",
            "shopping": "shopping areas and markets",
            "자연": "parks and natural attractions",
            "nature": "parks and natural attractions",
        }

        place_type = theme_mapping.get(theme.lower(), f"{theme} places")
        instruction = f"Please recommend {place_type} near {city_or_country_name}"
    else:
        instruction = f"Please recommend key tourist attractions near {city_or_country_name}"

    instruction += """
    # Key Guidelines
    1. return recommend place in markdown table style
      example)
      | Place Name | Description | Link | Review |
      |------------|-------------|------|--------|
      | Everest Curry World | 인도 및 네팔 요리를 제공하는 인기 레스토랑입니다. 가격대는 중간 정도이며, 늦은 시간까지 운영합니다. 식사, 포장, 배달이 가능합니다. | https://example.com | ⭐⭐⭐⭐ |
      | 라 그릴리아 광화문 | 점심과 저녁에 운영되며 라이브 음악을 즐길 수 있습니다. |https://example.com | ⭐⭐⭐⭐⭐ |
      * Place Name : place name
      * Description : place description
      * Link : link (if passable or blank)
      * Review : place review score
    """

    response = gemini.map_grounding(instruction=instruction)
    return ToolResult(
        content=TextContent(
            type="text",
            text=parsing_map_grounding_text_response(response)
        )
    )


@mcp.tool(
    tags={'travel', 'guide'},
    meta={'author': 'anonymous'},
    enabled=True
)
@ensure_context
async def get_place_information(
        landmark_or_place_name: str,
        message: str,
        ctx: Context = None
) -> ToolResult:
    """Gets detailed information about a specific landmark or place.

    Use this tool when you need specific information about a particular location,
    such as opening hours, admission fees, historical background, or other details.

    Args:
        landmark_or_place_name (str): Name of the landmark or place to get information about.
        message (str): Detailed description of what information you need about this location.
            Examples: "What are the opening hours and admission fees?",
            "Tell me about the historical significance", "What facilities are available?".
        ctx (Context, optional): Internal use only, ignore this parameter.

    Returns:
        Detailed information about the specified location based on your request.
    """
    await ctx.info(
        'get_place_information tool invoked, params({}, {})'.format(
            landmark_or_place_name, message
        ))
    instruction = f"""Please provide information about the location based on the following request
    request: {message}
    location: {landmark_or_place_name}
    """
    gemini = MapGroundingAgent()
    response = gemini.map_grounding(
        instruction=instruction
    )
    return ToolResult(
        content=TextContent(
            type="text",
            text=parsing_map_grounding_text_response(response)
        )
    )


@mcp.tool(
    tags={'travel', 'planner'},
    meta={'author': 'anonymous'},
    enabled=True
)
@ensure_context
async def get_tour_plan(
        city_or_country_name: str,
        days: int,
        is_include_hotel: bool,
        message: str = None,
        ctx: Context = None
) -> ToolResult:
    """Creates a new travel itinerary for a specified location and duration.

    Use this tool to generate a complete day-by-day travel plan with recommended places,
    time schedules, and optional accommodation suggestions.

    Args:
        city_or_country_name (str): Name of the city or country to create the itinerary for.
        days (int): Number of days for the trip (must be a positive integer).
        is_include_hotel (bool): Whether to include hotel/accommodation recommendations in the itinerary.
            Set to True to include hotels, False to exclude them.
        message (str, optional): Additional requirements or preferences for the travel plan.
            Examples: "Focus on cultural and historical sites", "Family-friendly activities with kids",
            "Budget-friendly options", "Include vegetarian restaurants", "Avoid crowded tourist spots".
            If not provided, generates a general itinerary with popular tourist attractions.
        ctx (Context, optional): Internal use only, ignore this parameter.

    Returns:
        A detailed travel itinerary in markdown table format with time schedules, place names,
        links, and review ratings for each day of the trip.
    """
    await ctx.info(
        'get_tour_plan tool invoked, params({}, {}, {})'.format(city_or_country_name, days, is_include_hotel))
    gemini = MapGroundingAgent()

    instruction = f"Please create a {days}-day travel itinerary for {city_or_country_name}"
    if is_include_hotel is not None:
        instruction += "\nPlease include accommodation in the itinerary"
    else:
        instruction += "\nPlease exclude accommodation from the itinerary"
    if message is not None:
        instruction += "\nconsidering the following user's request"
        instruction += f"\n{message}"

    instruction += """
    # Key Guidelines
    1. return plan in markdown table style
      example)
      | Time | Place Name | Link | Review |
      |------|-----------|------|--------|
      | 10:00~11:00 | 바티칸 시티 | https://example.com | ⭐⭐⭐⭐ |
      | 11:30~12:30 | 콜로세움 | https://example.com | ⭐⭐⭐⭐⭐ |
      * Time : time table
      * Place Name : place name
      * Link : link (if passable or blank)
      * Review : average review star count
    """

    response = gemini.map_grounding(instruction=instruction)
    return ToolResult(
        content=TextContent(
            type="text",
            text=parsing_map_grounding_text_response(response)
        )
    )


@mcp.tool(
    tags={'travel', 'planner'},
    meta={'author': 'anonymous'},
    enabled=True
)
@ensure_context
async def change_tour_plan(
        city_or_country_name: str,
        days: int,
        is_include_hotel: bool,
        org_plan: str,
        message: str,
        ctx: Context = None
) -> ToolResult:
    """Modifies an existing travel itinerary based on specific requirements.

    Use this tool when you need to update or adjust an existing travel plan while
    keeping the same destination and duration. The modified plan will maintain the
    overall structure but incorporate your requested changes.

    Args:
        city_or_country_name (str): Name of the city or country for the itinerary.
        days (int): Number of days for the trip (must match the original plan).
        is_include_hotel (bool): Whether to include hotel/accommodation recommendations in the modified itinerary.
            Set to True to include hotels, False to exclude them.
        org_plan (str): The complete original travel itinerary text that needs to be modified.
            This should be the full itinerary content from a previous get_tour_plan or change_tour_plan call.
        message (str): Detailed description of what changes you want to make to the plan.
            Examples: "Replace day 2 activities with museum visits", "Add more local food experiences throughout",
            "Make the itinerary more budget-friendly", "Include more outdoor and nature activities",
            "Reduce walking time between locations".
        ctx (Context, optional): Internal use only, ignore this parameter.

    Returns:
        A modified travel itinerary in markdown table format with your requested changes applied,
        maintaining the same destination and duration as the original plan.
    """
    await ctx.info(
        'change_tour_plan tool invoked, params(city_or_country_name={}, days={}, is_include_hotel={}, message={})'.format(
            city_or_country_name, days, is_include_hotel, message
        )
    )
    gemini = MapGroundingAgent()

    instruction = f"""Please modify the following {days}-day travel itinerary for {city_or_country_name} based on the user's request.

Original Plan:
{org_plan}

User's Request for Modification:
{message}

"""
    if is_include_hotel:
        instruction += "\nPlease include accommodation in the modified itinerary"
    else:
        instruction += "\nPlease exclude accommodation from the modified itinerary"

    instruction += "\n\nPlease provide the complete modified itinerary while keeping the same duration and overall structure."

    response = gemini.map_grounding(instruction=instruction)
    return ToolResult(
        content=TextContent(
            type="text",
            text=parsing_map_grounding_text_response(response)
        )
    )


if __name__ == "__main__":
    mcp.run()
