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


class UserInfoAgent(AbstractAgent):
    """ User Information Agent """

    def __init__(self):
        super().__init__()
        self.name = "User Info Agent"
        self.mcp_server_url = "http://localhost:9011/mcp"

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
            system_prompt="provide user information based on user's request"
        )

    async def stream(self, context: RequestContext) -> AsyncIterable[dict]:
        tool_client = ToolServerClient(url=self.mcp_server_url)
        agent = await self.get_agent(tool_client=tool_client)
        with tool_client.tool_server:
            async for event in self._run_agent(agent, context):
                yield event


if __name__ == "__main__":
    public_agent_card = AgentCard(
        name="User Information Agent",
        description="this agent can control and access user information like name, address, etc..",
        url='http://localhost:9101/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        supports_authenticated_extended_card=False,
        skills=[
            AgentSkill(
                id="user_name_skill",
                name="get_user_name_skill",
                description="get user name by id",
                tags=["User"],
                examples=[
                    "plz tell me name of user id \'K1234\'"
                ],
            ),
            AgentSkill(
                id="user_address_skill",
                name="get_user_address_skill",
                description="get user address by id",
                tags=["User"],
                examples=[
                    "plz tell me address of user id \'K1234\'"
                ],
            ),
            AgentSkill(
                id="user_booked_item_skill",
                name="get_user_booked_item_skill",
                description="get user booked item by user id",
                tags=["User"],
                examples=[
                    "plz tell me booked item of user id \'K1234\'",
                ],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=StrandsAgentExecutor(UserInfoAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9101)
