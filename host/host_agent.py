import asyncio
import uuid
from pathlib import Path
from typing import Literal

import httpx
import uvicorn
import yaml
from a2a.client import A2ACardResolver
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from a2a.types import Message as A2aMessage
from a2a.utils import new_agent_text_message
from pydantic import BaseModel, Field
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands.types.content import Message, ContentBlock
from strands_tools.a2a_client import A2AClientToolProvider


class ChattingRequest(BaseModel):
    question: str = Field(
        default="안녕?"
    )
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    history: list[tuple[Literal['user', 'assistant'], str]] = Field(
        default_factory=lambda: [],
        description="chat history, format: [(\"user\",\"hello\"), (\"assistant\": \"hi! how are you doing?\nhow can i help you?\")]"
    )


class ChatResponse(BaseModel):
    message: str = Field()
    roomId: str = Field()


class StrandsHostAgent:
    AGENT_URLS = [
        'http://localhost:9101',
        'http://localhost:9102',
    ]
    _prompt = yaml.safe_load(
        Path('.').joinpath('resource').joinpath('prompt.yaml').open('r')
    )

    host_system_prompt: str = _prompt.get('a2a').get('host').get('system')

    def __init__(self):
        self.provider = A2AClientToolProvider(known_agent_urls=self.AGENT_URLS)
        self.conversation_manager = SlidingWindowConversationManager(
            window_size=10,
        )
        self.model = OpenAIModel(
            model_id="gpt-4o-mini",
            params={
                "temperature": 0.1,
            }
        )

    async def invoke(self, a2a_message: A2aMessage) -> str:
        cards = [
            c.model_dump_json() for c in await self.get_agent_cards()
        ]
        sys_prompt = self.host_system_prompt.format(agent_card=cards)
        agent = Agent(
            model=self.model,
            tools=self.provider.tools,
            system_prompt=sys_prompt
        )

        message = Message(role='user', content=[])
        for part in a2a_message.parts:
            if part.root.kind == "text":
                message['content'].append(
                    ContentBlock(text=part.root.text)
                )
        result = agent([message])
        # Access metrics through the AgentResult
        print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
        print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
        print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
        return result.message['content'][0]['text']

    async def complete(self, request: ChattingRequest) -> str:
        cards = [
            c.model_dump_json() for c in await self.get_agent_cards()
        ]
        sys_prompt = self.host_system_prompt.format(agent_card=cards)
        agent = Agent(
            model=self.model,
            tools=self.provider.tools,
            system_prompt=sys_prompt
        )

        messages = []
        for conversation in request.history:
            messages.append(
                {"role": conversation[0], "content": [{"text": conversation[1]}]}
            )
        messages.append({"role": "user", "content": [{"text": request.question}]})

        result = agent(
            messages,
            conversation_manager=self.conversation_manager,
        )

        # Access metrics through the AgentResult
        print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
        print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
        print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
        return result.message['content'][0]['text']

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


class HostAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = StrandsHostAgent()

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


async def a2a_application_emitter() -> A2AStarletteApplication:
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
        agent_executor=HostAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    return A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )


if __name__ == '__main__':
    app = asyncio.run(a2a_application_emitter())
    uvicorn.run(app.build(), host='0.0.0.0', port=9202)
