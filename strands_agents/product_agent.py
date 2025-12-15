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
from common.types import AgentResponse
from strands_agents.common.abstract_agent import AbstractAgent
from strands_agents.common.tool import ToolServerClient


class ProductInfoAgent(AbstractAgent):
    """ Product Information Agent """

    def __init__(self):
        super().__init__()
        self.name = "Product Info Agent"
        self.mcp_server_url = "http://localhost:9012/mcp"

    async def get_agent(self, tool_client: ToolServerClient) -> Agent:
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
            system_prompt="provide product information based on user's request"
        )

    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:
        # print(id(self), self.tool_client.tool_server)
        tool_client = ToolServerClient(url=self.mcp_server_url)
        agent = await self.get_agent(tool_client)
        with tool_client.tool_server:
            async for event in self._run_agent(agent, context):
                yield event


if __name__ == "__main__":
    public_agent_card = AgentCard(
        name="Product Information Agent",
        description="this agent can control and access product information like name, price, description etc..",
        url='http://localhost:10004/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        supports_authenticated_extended_card=False,
        skills=[
            AgentSkill(
                id="product_info_skill",
                name="get_product_info_skill",
                description="get product infotmation by id",
                tags=["Product"],
                examples=[
                    "tell me product name of id \'PDO1234\'",
                ],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GenericAgentExecutor(ProductInfoAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=10004)
