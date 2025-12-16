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


class ProductInfoAgent(AbstractAgent):

    def __init__(self):
        super().__init__()
        self.agent = None
        self.agent_name = 'product_agent'

    async def get_agent(self, user_info: dict = None) -> CompiledStateGraph:
        mcp_client = MCPServerClient(
            {
                "product_tools": {
                    "transport": "http",
                    "url": "http://localhost:9012/mcp",
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
                content="provide product information based on user's request"
            )
        )


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
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=10004)
