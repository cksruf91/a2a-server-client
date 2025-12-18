import asyncio
from typing import AsyncIterable

import httpx
import uvicorn
from a2a.client import A2ACardResolver
from a2a.server.agent_execution import RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.handlers.callback_handler import PrintingCallbackHandler
from strands.models.openai import OpenAIModel
from strands_tools.a2a_client import A2AClientToolProvider

from common.executor import GenericAgentExecutor
from common.types import AgentResponse
from strands_agents.common.abstract_agent import AbstractAgent


class StrandsHostAgent(AbstractAgent):
    AGENT_URLS = {
        "http://localhost:10003/": "user_agent",
        "http://localhost:10004/": "product_agent",
        "http://localhost:10001/": "travel_guide_agent",
        "http://localhost:10002/": "travel_planner_agent",
    }

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
        sys_prompt = """
        당신은 사용자 정보와 상품 정보를 찾는 것을 도와주는 에이전트 입니다. 다음의 agent 를 사용하여 사용자의 질문에 답변하세요
        <AgentCards>
        {agent_card}
        </AgentCards>
        
        다음은 사용자에 대한 정보입니다.
        <userInformation>
        {user_info}
        </userInformation>
        
        <instruction>
        markdown 포멧을 활용하여 답변하세요
        </instruction>
        """.format(
            agent_card=cards,
            user_info={"userId": user_id}
        )
        return Agent(
            model=OpenAIModel(
                model_id="gpt-4o-mini",
                params={
                    "temperature": 0.1,
                }
            ),
            name=self.name,
            tools=provider.tools,
            conversation_manager=conversation_manager,
            callback_handler=PrintingCallbackHandler(),
            system_prompt=sys_prompt
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
