import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from a2a.types import Message as A2aMessage
from a2a.utils import new_agent_text_message
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.executors import ConcurrentToolExecutor
from strands.tools.mcp.mcp_client import MCPClient, MCPAgentTool
from strands.types.content import Message, ContentBlock


class ToolService:
    def __init__(self):
        self.tool_server = MCPClient(lambda: streamablehttp_client("http://localhost:9012/mcp"))

    def list_tools(self) -> list[MCPAgentTool]:
        tools: list[MCPAgentTool] = []
        with self.tool_server:
            tools += self.tool_server.list_tools_sync()
        return tools


class ProductInfoAgent:
    """Hello World Agent."""

    def __init__(self):
        self.tool_service = ToolService()

        model = OpenAIModel(
            model_id="gpt-4o-mini",
            params={
                "temperature": 0.1,
            }
        )
        self.llm = Agent(
            model=model,
            tools=self.tool_service.list_tools(),
            tool_executor=ConcurrentToolExecutor(),
            system_prompt="You are a helpful assistant."
        )

    async def invoke(self, a2a_message: A2aMessage) -> str:

        message = Message(role='user', content=[])
        for part in a2a_message.parts:
            if part.root.kind == "text":
                message['content'].append(
                    ContentBlock(text=part.root.text)
                )

        with self.tool_service.tool_server:
            result = self.llm([message])

        # Access metrics through the AgentResult
        print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
        print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
        print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
        return result.message['content'][0]['text']


class ProductInfoAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = ProductInfoAgent()

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ) -> None:
        result = await self.agent.invoke(context.message)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
            self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')


if __name__ == "__main__":
    get_product_info_skill = AgentSkill(
        id="product_info_skill",
        name="get_product_info_skill",
        description="get product infotmation by id",
        tags=["Product"],
        examples=[
            "tell me product name of id \'PDO1234\'",
        ],
    )

    public_agent_card = AgentCard(
        name="Product Information Agent",
        description="this agent can control and access product information like name, price, description etc..",
        url='http://localhost:9102/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[get_product_info_skill],
        supports_authenticated_extended_card=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ProductInfoAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9102)
