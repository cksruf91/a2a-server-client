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
    """Retrieves place recommendations for a specified city or country with optional theme filtering.

    The tool uses the provided name of a city or country to generate a list of
    recommended places nearby by leveraging grounding with Google Maps. You can optionally
    specify a theme to get recommendations for specific types of places.

    Args:
        city_or_country_name (str): The name of the city or country for which places
            are to be recommended.
        theme (str, optional): The type of places to recommend. Common themes include:
            - "맛집" or "restaurant": Recommend restaurants and dining spots
            - "관광" or "tourist": Recommend tourist attractions and sightseeing spots
            - "카페" or "cafe": Recommend cafes and coffee shops
            - "쇼핑" or "shopping": Recommend shopping areas and markets
            - "자연" or "nature": Recommend parks and natural attractions
            If not provided, general tourist attractions will be recommended.
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        the generated place recommendation text based on the specified theme.
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
        query: str,
        ctx: Context = None
) -> ToolResult:
    """Retrieves detailed information about a given landmark or place name.

    This function utilizes a map grounding agent to gather information based on the
    provided landmark or place name. The resulting content is parsed and returned
    as a ToolResult containing text-based information.

    Args:
        landmark_or_place_name (str): Name of the landmark or place for which
            detailed information is requested.
        query (str): The user's specific question or request about what information they want to know about the location,
            such as opening hours, admission fees, historical significance, or any other location-specific details.
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        detailed information related to the specified landmark or place name in textual format.
    """
    await ctx.info(
        'get_place_information tool invoked, params({}, {})'.format(
            landmark_or_place_name, query
        ))
    instruction = f"""Please provide information about the location based on the following request
    request: {query}
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
        query: str = None,
        ctx: Context = None
) -> ToolResult:
    """generates a travel itinerary for a specified location and duration.
    create a detailed plan and optionally includes accommodations in the itinerary.

    Args:
        city_or_country_name (str): Name of the city or country for which to create the travel itinerary.
        days (int): The number of days for the travel itinerary.
        is_include_hotel (bool): flag indicating whether accommodations should be included in the itinerary.
        query (str): Additional requirements or preferences for the travel plan
            (e.g., focus on cultural sites, family-friendly activities, specific interests).
            If not provided, a general itinerary will be created with popular tourist attractions.
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        generated travel itinerary text.
    """
    await ctx.info(
        'get_tour_plan tool invoked, params({}, {}, {})'.format(city_or_country_name, days, is_include_hotel))
    gemini = MapGroundingAgent()

    prompt = f"Please create a {days}-day travel itinerary for {city_or_country_name}"
    if is_include_hotel is not None:
        prompt += "\nPlease include accommodation in the itinerary"
    else:
        prompt += "\nPlease exclude accommodation from the itinerary"
    if query is not None:
        prompt += "\nconsidering the following user's request"
        prompt += f"\n{query}"

    response = gemini.map_grounding(instruction=prompt)
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
        query: str,
        ctx: Context = None
) -> ToolResult:
    """Modifies an existing travel itinerary based on user's specific requirements.

    This function takes an original travel plan and modifies it according to the user's
    request while maintaining the core structure and duration of the trip.

    Args:
        city_or_country_name (str): Name of the city or country for the travel itinerary.
        days (int): The number of days for the travel itinerary.
        is_include_hotel (bool): flag indicating whether accommodations should be included in the itinerary.
        org_plan (str): The original travel plan that needs to be modified.
        query (str): User's specific request for modifying the plan
            (e.g., "replace day 2 with museum visits", "add more local food experiences",
            "make it more budget-friendly", "include outdoor activities").
        ctx (Context, optional): internal use only, ignore this parameter

    Returns:
        modified travel itinerary text based on user's requirements.
    """
    await ctx.info(
        'change_tour_plan tool invoked, params(city_or_country_name={}, days={}, is_include_hotel={}, query={})'.format(
            city_or_country_name, days, is_include_hotel, query
        )
    )
    gemini = MapGroundingAgent()

    prompt = f"""Please modify the following {days}-day travel itinerary for {city_or_country_name} based on the user's request.

Original Plan:
{org_plan}

User's Request for Modification:
{query}

"""
    if is_include_hotel:
        prompt += "\nPlease include accommodation in the modified itinerary"
    else:
        prompt += "\nPlease exclude accommodation from the modified itinerary"

    prompt += "\n\nPlease provide the complete modified itinerary while keeping the same duration and overall structure."

    response = gemini.map_grounding(instruction=prompt)
    return ToolResult(
        content=TextContent(
            type="text",
            text=parsing_map_grounding_text_response(response)
        )
    )


if __name__ == "__main__":
    mcp.run()
