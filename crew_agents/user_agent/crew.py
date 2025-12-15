import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from crewai import Agent
from crewai_tools import MCPServerAdapter

from common.executor import GenericAgentExecutor
from crew_agents.common.abstract_agent import AbstractAgent


class UserInfoAgent(AbstractAgent):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.agent_name = 'UserInfoCrewAgent'
        self.mcp_server_params: dict = {
            "url": "http://127.0.0.1:9011/mcp",
            "transport": "streamable-http"
        }

    @staticmethod
    def get_agent(mcp_tools: MCPServerAdapter) -> Agent:
        return Agent(
            role="user information manager",
            goal="retrieve user information as user request",
            backstory="simply return data by using tools",
            llm="openai/gpt-4o-mini",
            verbose=False,
            reasoning=False,
            tools=mcp_tools,
        )


if __name__ == "__main__":  # noqa
    agent_card = AgentCard(
        name="User Information Agent",
        description="this agent can control and access user information like name, address, etc..",
        url='http://localhost:10003/',
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
        agent_executor=GenericAgentExecutor(UserInfoAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=10003)
