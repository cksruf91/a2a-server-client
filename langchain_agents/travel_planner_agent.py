import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCapabilities, AgentCard
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from common.executor import GenericAgentExecutor
from langchain_agents.common.abstract_agent import AbstractAgent
from langchain_agents.common.tool import MCPServerClient


class TravelPlannerAgent(AbstractAgent):

    def __init__(self):
        super().__init__()
        self.agent = None
        self.agent_name = 'travel_planner_agent'

    async def get_agent(self, user_info: dict = None) -> CompiledStateGraph:
        mcp_client = MCPServerClient(
            {
                "travel_tools": {
                    "transport": "http",
                    "url": "http://localhost:5001/mcp",
                }
            },
            tags=['planner']
        )

        return create_agent(
            name=self.agent_name,
            model=ChatOpenAI(
                model='gpt-4o-mini',
                temperature=0.,
                timeout=60,
                max_retries=1
            ),
            tools=await mcp_client.get_tools(),
            system_prompt=SystemMessage(
                content="create and modify travel itineraries based on user's requirements, including day-by-day plans with time schedules and optional accommodation recommendations"
            )
        )


if __name__ == "__main__":
    public_agent_card = AgentCard(
        name="Travel Planner Agent",
        description="this agent can create and modify travel itineraries with day-by-day plans, time schedules, and accommodation recommendations",
        url='http://localhost:10002/',
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

    uvicorn.run(server.build(), host='0.0.0.0', port=10002)
