import asyncio
import json
import uuid
from pathlib import Path
from typing import AsyncIterable, Literal

import httpx
import uvicorn
import yaml
from a2a.client import A2ACardResolver
from a2a.server.agent_execution import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities, Message as A2aMessage
from a2a.utils import new_agent_text_message
from pydantic import BaseModel, Field
from sse_starlette.sse import ServerSentEvent
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands.types import content as strands_content
from strands_tools.a2a_client import A2AClientToolProvider

from common.strands.abstract_agent import AbstractAgent
from common.strands.executor import StrandsAgentExecutor


class ChattingRequest(BaseModel):
    question: str = Field(
        default="안녕?"
    )
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: list[tuple[Literal['user', 'assistant'], str]] = Field(
        default_factory=lambda: [],
        description="chat history, format: [(\"user\",\"hello\"), (\"assistant\": \"hi! how are you doing?\nhow can i help you?\")]"
    )

    def to_model_input(self) -> list[strands_content.Message]:
        messages = []
        for role, content in self.history:
            messages.append(
                strands_content.Message(role=role, content=[
                    strands_content.ContentBlock(text=content)
                ])
            )
        messages.append({"role": "user", "content": [{"text": self.question}]})
        return messages


class ChatResponse(BaseModel):
    message: str = Field()
    roomId: str = Field()


class StrandsHostAgent(AbstractAgent):
    AGENT_URLS = {
        "http://localhost:9101/": "user_agent",
        "http://localhost:9102/": "product_agent",
        "http://localhost:9103/": "travel_guide_agent",
    }
    _prompt = yaml.safe_load(
        Path('strands_agents').joinpath('resource').joinpath('prompt.yaml').open('r')
    )

    host_system_prompt: str = _prompt.get('a2a').get('host').get('system')

    def __init__(self):
        super().__init__()

    async def get_agent(self) -> Agent:
        urls = [url for url, name in self.AGENT_URLS.items()]
        provider = A2AClientToolProvider(known_agent_urls=urls)
        conversation_manager = SlidingWindowConversationManager(
            window_size=10,
        )
        cards = [card.model_dump_json() for card in await self.get_agent_cards()]
        model = OpenAIModel(
            model_id="gpt-4o-mini",
            params={
                "temperature": 0.1,
            }
        )
        return Agent(
            model=model,
            tools=provider.tools,
            conversation_manager=conversation_manager,
            system_prompt=self.host_system_prompt.format(agent_card=cards)
        )

    async def invoke(self, a2a_message: A2aMessage | None) -> str:
        message = self._parsing_a2a_message(a2a_message)
        if self.agent is None:
            self.agent = await self.get_agent()
        result = self._logging_metrics(self.agent([message]))

        return result.message['content'][0]['text']

    async def complete(self, request: ChattingRequest) -> str:

        if self.agent is None:
            self.agent = await self.get_agent()

        result = self._logging_metrics(self.agent(request.to_model_input()))
        return result.message['content'][0]['text']

    async def stream(self, request: ChattingRequest) -> AsyncIterable[bytes]:
        if self.agent is None:
            self.agent = await self.get_agent()

        async for event in self.agent.stream_async(request.to_model_input()):
            if 'current_tool_use' in event:
                input_: str = event['current_tool_use'].get('input', '')
                try:
                    target_agent_url = json.loads(input_).get('target_agent_url')
                    status_message = "ask {} ..".format(self.AGENT_URLS.get(target_agent_url, 'agent'))
                except json.decoder.JSONDecodeError:
                    status_message = "ask agent .."
                yield ServerSentEvent(
                    event='executing',
                    data=json.dumps({
                        'message': status_message, 'contents': None
                    })
                ).encode()
            elif "data" in event:
                yield ServerSentEvent(
                    event='stream',
                    data=json.dumps({
                        'message': 'in progress', 'contents': event["data"]
                    })
                ).encode()

        yield ServerSentEvent(
            event='Done',
            data=json.dumps({
                'message': 'Done', 'contents': ""
            })
        ).encode()

    async def get_agent_cards(self) -> list[AgentCard]:
        cards: list[AgentCard] = []
        async with httpx.AsyncClient() as httpx_client:
            for base_url in self.AGENT_URLS:
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=base_url,
                )
                cards.append(await resolver.get_agent_card())
        return cards


class HostAgentExecutor(StrandsAgentExecutor):

    def __init__(self, agent):
        super().__init__(agent)

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ) -> None:
        result = await self.agent.invoke(context.message)
        await event_queue.enqueue_event(
            new_agent_text_message(
                result,
                context_id=context.context_id,
                task_id=context.task_id,
            )
        )


async def get_a2a_application() -> A2AStarletteApplication:
    host_agent = StrandsHostAgent()
    agent_skills: list[AgentSkill] = []
    for cards in await host_agent.get_agent_cards():
        agent_skills.extend(cards.skills)

    public_agent_card = AgentCard(
        name="User & Product information provide agent",
        description="this agent provide User & product information",
        url='http://localhost:9202/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=agent_skills,
        supports_authenticated_extended_card=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=HostAgentExecutor(StrandsHostAgent()),
        task_store=InMemoryTaskStore(),
    )

    return A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )


if __name__ == '__main__':
    app = asyncio.run(get_a2a_application())
    uvicorn.run(app.build(), host='0.0.0.0', port=9202)
