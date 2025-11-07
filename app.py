import uuid
from pathlib import Path
from typing import Literal

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard, Message as A2aMessage
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands.types.content import Message, ContentBlock
from strands_tools.a2a_client import A2AClientToolProvider

from prompt_manager import PromptManager


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


class OrcastratorAgent:
    AGENT_URLS = [
        'http://localhost:9101',
        'http://localhost:9102',
    ]
    prompt = PromptManager()

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
        sys_prompt = self.prompt.host_system.format(agent_card=cards)
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
        sys_prompt = self.prompt.host_system.format(agent_card=cards)
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


chat_router = APIRouter(prefix='/chat', tags=['chat'])


@chat_router.post('/complete')
async def get_chatting_message(request: ChattingRequest) -> ChatResponse:
    output = await OrcastratorAgent().complete(request)
    return ChatResponse(roomId=request.roomId, message=output)


def main():
    app = FastAPI(
        title="Host Agent",
        description="Host Agent executor",
        version="1.0"
    )
    app.include_router(chat_router)

    # CORS 설정 - 프론트엔드 앱에서 API 호출 허용
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발 환경용, 프로덕션에서는 특정 도메인 지정
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_file_path = Path("resource/app")

    app.mount("/static", StaticFiles(directory=static_file_path, html=True), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(static_file_path.joinpath("index.html"))

    return app
