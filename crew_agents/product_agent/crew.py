import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from crewai import Agent
from crewai.mcp import MCPServerHTTP

from common.executor import GenericAgentExecutor
from crew_agents.common.abstract_agent import AbstractAgent


class ProductInfoAgent(AbstractAgent):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.agent_name = 'ProductInfoCrewAgent'

    @staticmethod
    def get_agent() -> Agent:
        return Agent(
            role="product information manager",
            goal="provide product information based on user's request",
            backstory="retrieve and provide product information using available tools",
            llm="openai/gpt-4o-mini",
            verbose=True,
            reasoning=False,
            mcps=[
                MCPServerHTTP(
                    url="http://127.0.0.1:9012/mcp",
                    streamable=True,
                    cache_tools_list=True,
                )
            ]
        )


if __name__ == "__main__":  # noqa
    agent_card = AgentCard(
        name="Product Information Agent",
        description="this agent can control and access product information like name, price, description etc..",
        url='http://localhost:9102/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        supports_authenticated_extended_card=False,
        skills=[
            AgentSkill(
                id="product_info_skill",
                name="get_product_info_skill",
                description="get product information by id",
                tags=["Product"],
                examples=[
                    "tell me product name of id 'PDO1234'",
                ],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GenericAgentExecutor(ProductInfoAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9102)