import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCapabilities, AgentCard
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from common.executor import GenericAgentExecutor
from langchain_agents.common.abstract_agent import AbstractAgent


class TravelGuideAgent(AbstractAgent):

    def __init__(self):
        super().__init__()
        self.agent = None
        self.agent_name = 'travel_guide_agent'

    async def get_agent(self, user_info: dict = None) -> CompiledStateGraph:
        mcp_client = MultiServerMCPClient(
            {
                "travel_tools": {
                    "transport": "http",
                    "url": "http://localhost:5001/mcp",
                }
            }
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
                content="provide travel guide information based on user's request, including place recommendations and detailed information about landmarks"
            )
        )


if __name__ == "__main__":
    public_agent_card = AgentCard(
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
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=10001)
