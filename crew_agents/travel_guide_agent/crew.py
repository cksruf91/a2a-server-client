import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from crewai import Agent
from crewai_tools import MCPServerAdapter

from common.executor import GenericAgentExecutor
from crew_agents.common.abstract_agent import AbstractAgent


class TravelGuideAgent(AbstractAgent):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.agent_name = 'TravelGuideCrewAgent'
        self.mcp_server_params: dict = {
            "url": "http://127.0.0.1:5001/mcp",
            "transport": "streamable-http"
        }

    @staticmethod
    def get_agent(mcp_tools: MCPServerAdapter) -> Agent:
        return Agent(
            role="travel guide information provider",
            goal="provide travel guide information based on user's request, including place recommendations and detailed information about landmarks",
            backstory=(
                "expert travel guide who helps travelers discover amazing places and provides detailed information about tourist attractions, "
                "Input question: {question}"
            ),
            llm="openai/gpt-4o-mini",
            verbose=False,
            reasoning=False,
            tools=mcp_tools
        )


if __name__ == "__main__":  # noqa
    agent_card = AgentCard(
        name="Travel Guide Agent",
        description="this agent can provide travel guide information including place recommendations and detailed information about landmarks and tourist attractions",
        url='http://localhost:10001/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        supports_authenticated_extended_card=False,
        skills=[
            AgentSkill(
                id="place_recommendation_skill",
                name="get_place_recommendation_skill",
                description="get place recommendations for a city or country, optionally filtered by theme (restaurant, tourist, cafe, shopping, nature)",
                tags=["Travel", "Guide"],
                examples=[
                    "recommend tourist attractions in Paris",
                    "show me popular restaurants in Seoul",
                    "what are the best cafes in Tokyo"
                ],
            ),
            AgentSkill(
                id="place_information_skill",
                name="get_place_information_skill",
                description="get detailed information about a specific landmark or place",
                tags=["Travel", "Guide"],
                examples=[
                    "tell me about the Eiffel Tower",
                    "what are the opening hours of the Louvre Museum",
                    "give me information about Gyeongbokgung Palace"
                ],
            ),
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GenericAgentExecutor(TravelGuideAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=10001)
