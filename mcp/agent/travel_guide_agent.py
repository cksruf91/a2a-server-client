import uuid
from collections.abc import AsyncIterable

import nest_asyncio
import uvicorn
from a2a.server.agent_execution import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentSkill,
    AgentCard,
    AgentCapabilities,
)
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.planners import BuiltInPlanner
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams, McpToolset
from google.genai import types
from google.genai.types import ThinkingConfig

from common.google.abstract_agent import AbstractAgent
from common.google.executor import GenericAgentExecutor
from common.google.tool import ToolFilter
from common.google.types import AgentResponse

nest_asyncio.apply()


class TravelGuideAgent(AbstractAgent):
    """Travel Guide Agent."""

    def __init__(self):
        super().__init__()
        self.agent = None
        self.runner: Runner | None = None
        self.agent_name = 'TravelGuideAgent'
        self.session_service = InMemorySessionService()

    async def init_agent_runner(self):
        tools = await McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="http://localhost:9013/mcp", timeout=2.0
            ),
            tool_filter=ToolFilter(tags=['guide'])
        ).get_tools()

        for tool in tools:
            print(f'Loaded tools {tool.name}')

        self.agent = Agent(
            model=LiteLlm(model="openai/gpt-4o-mini"),
            name=self.agent_name,
            instruction="as a travel guide assistant, you provide information about specific locations or recommendations.",
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True,
            generate_content_config=types.GenerateContentConfig(
                temperature=0.0
            ),
            tools=tools,
            planner=BuiltInPlanner(
                thinking_config=ThinkingConfig(
                    include_thoughts=True,  # Ask the model to include its thoughts in the response
                    thinking_budget=256  # Limit the 'thinking' to 256 tokens (adjust as needed)
                )
            ),
        )
        print(f'Initializing {self.agent_name}')
        self.runner = Runner(
            agent=self.agent,
            app_name=self.agent_name,
            session_service=self.session_service,
        )

    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:
        query = context.get_user_input()

        print('Running agent stream for session {context_id} {task_id} - {query}'.format(
            context_id=context.current_task.context_id,
            task_id=context.current_task.id,
            query=query,
        ))
        if not query:
            raise ValueError('Query cannot be empty')

        if not self.runner:
            await self.init_agent_runner()

        user_id = context.metadata.get('user_id', uuid.uuid4().hex)
        session_id = await self.manage_session(user_id=user_id, session_id=context.current_task.context_id)

        content = types.Content(role='user', parts=[types.Part(text=query)])
        async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
        ):

            if not event.is_final_response():
                yield AgentResponse(
                    response_type=None,
                    is_task_complete=False,
                    require_user_input=False,
                    content=f"{event.content}: Processing response...",
                )
            else:
                response = ""
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response += part.text + "\n"
                        elif part.function_response:
                            response += part.function_response.model_dump_json() + "\n"
                else:
                    response += f"Error for running agent {self.agent_name}"
                # TODO : user input required case
                yield AgentResponse(
                    response_type="text",
                    is_task_complete=True,
                    require_user_input=False,
                    content=response,
                )

    async def manage_session(self, user_id: str, session_id: str | None) -> str:
        session = None
        if session_id:
            session_id = uuid.uuid4().hex
        else:
            session = await self.session_service.get_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id,
            )
        if not session:
            _ = await self.session_service.create_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id,
            )
        return session_id


if __name__ == "__main__":
    public_agent_card = AgentCard(
        name="travel guide agent",
        description="travel guide agent",
        url='http://localhost:9103/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="place_recommendation_skill",
                name="get_place_recommendation_skill",
                description="Retrieves place recommendations for a specified city or country.",
                tags=["travel", 'guide'],
                examples=[
                    "다낭 관광지 추천해줘",
                    "이탈리아 로마에 유명한 관광지 추천해줘",
                    "오사카 맛집 찾아줘",
                ],
            ),
            AgentSkill(
                id="place_information_skill",
                name="get_place_information_skill",
                description="Retrieves detailed information about a given landmark or place name.",
                tags=["travel", 'guide'],
                examples=[
                    "콜로세움에 대해 설명해줘"
                    "도톤보리는 어떤곳이야?"
                ],
            ),

        ],
        supports_authenticated_extended_card=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GenericAgentExecutor(TravelGuideAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host='0.0.0.0', port=9103)
