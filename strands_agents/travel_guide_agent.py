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

from common.strands.abstract_agent import AbstractAgent
from common.strands.executor import StrandsAgentExecutor
from common.strands.tool import ToolServerClient


class TravelGuideAgent(AbstractAgent):
    """ Travel Guide Agent """

    def __init__(self):
        super().__init__()
        self.name = "Travel Guide Agent"
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
            system_prompt="provide travel guide information based on user's request, including place recommendations and detailed information about landmarks"
        )

    async def stream(self, context: RequestContext) -> AsyncIterable[dict]:
        tool_client = ToolServerClient(url=self.mcp_server_url)
        agent = self.get_agent(tool_client=tool_client)
        with tool_client.tool_server:
            async for event in self._run_agent(agent, context):
                yield event


if __name__ == "__main__":
    public_agent_card = AgentCard(
        name="Travel Guide Agent",
        description="this agent can provide travel guide information including place recommendations and detailed information about landmarks and tourist attractions",
        url='http://localhost:9103/',
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
        agent_executor=StrandsAgentExecutor(TravelGuideAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9103)
