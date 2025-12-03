import asyncio
from pathlib import Path
from typing import AsyncIterable

import httpx
import uvicorn
import yaml
from a2a.client import A2ACardResolver
from a2a.server.agent_execution import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands_tools.a2a_client import A2AClientToolProvider

from common.executor import GenericAgentExecutor
from common.strands.abstract_agent import AbstractAgent
from common.types import AgentResponse
from strands.handlers.callback_handler import PrintingCallbackHandler


class StrandsHostAgent(AbstractAgent):
    AGENT_URLS = {
        "http://localhost:9101/": "user_agent",
        "http://localhost:9102/": "product_agent",
        "http://localhost:9103/": "travel_guide_agent",
        "http://localhost:9104/": "travel_planner_agent",
    }
    _prompt = yaml.safe_load(
        Path('strands_agents').joinpath('resource').joinpath('prompt.yaml').open('r')
    )

    host_system_prompt: str = _prompt.get('a2a').get('host').get('system')

    def __init__(self):
        super().__init__()
        self.name = "Host Agent"

    async def get_agent(self, user_id: str) -> Agent:
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
            name=self.name,
            tools=provider.tools,
            conversation_manager=conversation_manager,
            callback_handler=PrintingCallbackHandler(),
            system_prompt=self.host_system_prompt.format(
                agent_card=cards,
                user_info={"userId": user_id}
            )
        )

    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:
        user_id = "null"
        if getattr(context.message, "metadata", None) is not None:
            user_id = context.message.metadata.get("userId", "")
        agent = await self.get_agent(user_id)
        async for event in self._run_agent(agent, context):
            yield event

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


async def get_a2a_application() -> A2AStarletteApplication:
    host_agent = StrandsHostAgent()
    agent_skills: list[AgentSkill] = []
    for cards in await host_agent.get_agent_cards():
        agent_skills.extend(cards.skills)

    public_agent_card = AgentCard(
        name="User & Product information provide agent",
        description="this agent provide User & product information",
        url='http://localhost:10000/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=agent_skills,
        supports_authenticated_extended_card=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=GenericAgentExecutor(StrandsHostAgent()),
        task_store=InMemoryTaskStore(),
    )

    return A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        # extended_agent_card=specific_extended_agent_card,
    )


if __name__ == '__main__':
    app = asyncio.run(get_a2a_application())
    uvicorn.run(app.build(), host='0.0.0.0', port=10000)
