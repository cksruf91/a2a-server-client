import json
import re
from collections.abc import AsyncIterable
from typing import Any

import nest_asyncio
import uvicorn
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
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams, McpToolset
from google.genai import types
from google.genai.types import ThinkingConfig

from common.google.agent import AgentRunner
from common.google.executor import GenericAgentExecutor
from common.google.tool import ToolFilter

nest_asyncio.apply()


class TravelGuideAgent:
    """Travel Guide Agent."""

    def __init__(self):
        self.agent = None
        self.session_service = InMemorySessionService()
        self.runner = None
        self.agent_name = 'TravelGuideAgent'

    async def init_agent(self):
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
            name="TravelGuideAgent",
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
        print(f'Initializing {self.agent_name} metadata')
        self.runner = AgentRunner()

    async def stream(self, query, context_id, task_id) -> AsyncIterable[dict[str, Any]]:
        print(
            f'Running agent stream for session {context_id} {task_id} - {query}'
        )

        if not query:
            raise ValueError('Query cannot be empty')

        if not self.agent:
            await self.init_agent()
        async for chunk in self.runner.run_stream(
                self.agent, query, context_id
        ):
            print(f'Received chunk {chunk}')
            if isinstance(chunk, dict) and chunk.get('type') == 'final_result':
                response = chunk['response']
                yield self.get_agent_response(response)
            else:
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': f'{self.agent_name}: Processing Request...',
                }

    def format_response(self, chunk):
        patterns = [
            r'```\n(.*?)\n```',
            r'```json\s*(.*?)\s*```',
            r'```tool_outputs\s*(.*?)\s*```',
        ]

        for pattern in patterns:
            match = re.search(pattern, chunk, re.DOTALL)
            if match:
                content = match.group(1)
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
        return chunk

    def get_agent_response(self, chunk):
        print(f'Response Type {type(chunk)}')
        data = self.format_response(chunk)
        print(f'Formatted Response {data}')
        try:
            if isinstance(data, dict):
                if 'status' in data and data['status'] == 'input_required':
                    return {
                        'response_type': 'text',
                        'is_task_complete': False,
                        'require_user_input': True,
                        'content': data['question'],
                    }
                return {
                    'response_type': 'data',
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': data,
                }
            return_type = 'data'
            try:
                data = json.loads(data)
                return_type = 'data'
            except Exception as json_e:
                print(f'Json conversion error {json_e}')
                return_type = 'text'
            return {
                'response_type': return_type,
                'is_task_complete': True,
                'require_user_input': False,
                'content': data,
            }
        except Exception as e:
            print(f'Error in get_agent_response: {e}')
            return {
                'response_type': 'text',
                'is_task_complete': True,
                'require_user_input': False,
                'content': 'Could not complete booking / task. Please try again.',
            }


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
