from typing import AsyncIterable

import uvicorn
from a2a.server.agent_execution import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.executors import ConcurrentToolExecutor

from common.executor import GenericAgentExecutor
from common.strands.abstract_agent import AbstractAgent
from common.strands.tool import ToolServerClient
from common.types import AgentResponse


class TravelPlannerAgent(AbstractAgent):
    """ Travel Planner Agent """

    def __init__(self):
        super().__init__()
        self.name = "Travel Planner Agent"
        self.mcp_server_url = "http://localhost:5001/mcp"

    def get_agent(self, tool_client: ToolServerClient) -> Agent:
        model = OpenAIModel(
            model_id="gpt-4o-mini",
            params={
                "temperature": 0.1,
            }
        )
        return Agent(
            model=model,
            name=self.name,
            tools=tool_client.list_tools(),
            tool_executor=ConcurrentToolExecutor(),
            system_prompt="create and modify travel itineraries based on user's requirements, including day-by-day plans with time schedules and optional accommodation recommendations"
        )

    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:
        tool_client = ToolServerClient(url=self.mcp_server_url, tags=['planner'])
        agent = self.get_agent(tool_client=tool_client)
        with tool_client.tool_server:
            async for event in self._run_agent(agent, context):
                yield event


if __name__ == "__main__":
    public_agent_card = AgentCard(
        name="Travel Planner Agent",
        description="this agent can create and modify travel itineraries with day-by-day plans, time schedules, and accommodation recommendations",
        url='http://localhost:9104/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        supports_authenticated_extended_card=False,
        skills=[
            AgentSkill(
                id="tour_plan_skill",
                name="get_tour_plan_skill",
                description="create a new travel itinerary for a specified location and duration with optional hotel recommendations",
                tags=["Travel", "Planner"],
                examples=[
                    "create a 3-day travel plan for Paris",
                    "plan a 5-day trip to Seoul with hotel recommendations",
                    "make a 7-day itinerary for Tokyo focusing on cultural sites"
                ],
            ),
            AgentSkill(
                id="change_tour_plan_skill",
                name="change_tour_plan_skill",
                description="modify an existing travel itinerary based on specific requirements",
                tags=["Travel", "Planner"],
                examples=[
                    "add more museum visits to day 2 of the plan",
                    "make the itinerary more budget-friendly",
                    "include more local food experiences throughout the trip"
                ],
            ),
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GenericAgentExecutor(TravelPlannerAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9104)
