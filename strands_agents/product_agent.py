import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from a2a.types import Message as A2aMessage
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.executors import ConcurrentToolExecutor

from common.strands.abstract_agent import AbstractAgent
from common.strands.executor import StrandsAgentExecutor
from common.strands.tool import ToolServerClient


class ProductInfoAgent(AbstractAgent):
    """ Product Information Agent """

    def __init__(self):
        super().__init__()
        self.tool_service = ToolServerClient(
            url="http://localhost:9012/mcp"
        )

    def get_agent(self) -> Agent:
        model = OpenAIModel(
            model_id="gpt-4o-mini",
            params={
                "temperature": 0.1,
            }
        )
        return Agent(
            model=model,
            tools=self.tool_service.list_tools(),
            tool_executor=ConcurrentToolExecutor(),
            system_prompt="provide product information based on user's request"
        )

    async def invoke(self, a2a_message: A2aMessage) -> str:
        message = self._parsing_a2a_message(a2a_message)

        if self.agent is None:
            self.agent = self.get_agent()

        with self.tool_service.tool_server:
            result = self._logging_metrics(self.agent([message]))

        return result.message['content'][0]['text']


if __name__ == "__main__":
    public_agent_card = AgentCard(
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
                description="get product infotmation by id",
                tags=["Product"],
                examples=[
                    "tell me product name of id \'PDO1234\'",
                ],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=StrandsAgentExecutor(ProductInfoAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9102)
