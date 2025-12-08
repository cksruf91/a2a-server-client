import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from crewai import Agent
from crewai.mcp import MCPServerHTTP

from common.executor import GenericAgentExecutor
from crew_agents.common.abstract_agent import AbstractAgent


class TravelPlannerAgent(AbstractAgent):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.agent_name = 'TravelPlannerCrewAgent'

    @staticmethod
    def get_agent() -> Agent:
        return Agent(
            role="travel planner",
            goal="help users create and modify their travel plans with personalized itineraries",
            backstory="""You are a travel planner agent who helps users create and modify their travel plans.
            You assist with destination selection, itinerary planning, and provide recommendations for transportation and accommodations.
            Your goal is to create personalized travel plans that consider the user's preferences and constraints while optimizing their travel experience.
            Always respond in the same language that the user asked the question in.
            If the user doesn't provide sufficient information to use the tool, ask for the necessary information.""",
            llm="openai/gpt-4o-mini",
            verbose=True,
            reasoning=False,
            mcps=[
                MCPServerHTTP(
                    url="http://127.0.0.1:5001/mcp",
                    streamable=True,
                    cache_tools_list=True,
                )
            ]
        )


if __name__ == "__main__":  # noqa
    agent_card = AgentCard(
        name="Travel Planner Agent",
        description="travel planner agent, Creates travel plan base on user request",
        url='http://localhost:10002/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        supports_authenticated_extended_card=False,
        skills=[
            AgentSkill(
                id="create_tour_plan_skill",
                name="create_tour_plan_skill",
                description="Creates a travel itinerary based on user's specified city or country and desired number of days.",
                tags=["Travel", "Planner"],
                examples=[
                    "샌프란시스코에서 하루를 계획해줘",
                    "다낭에서 3일 일정을 호텔을 포함하여 만들어줘"
                ],
            ),
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GenericAgentExecutor(TravelPlannerAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=10002)