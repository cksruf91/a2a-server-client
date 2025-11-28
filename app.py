from pathlib import Path

import nest_asyncio
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from common.broker import AgentMessageBroker
from common.model import ChatResponse, ChattingRequest

nest_asyncio.apply()
chat_router = APIRouter(prefix='/chat', tags=['chat'])

agent_message_broker = AgentMessageBroker(agent_url='http://localhost:10000/')


@chat_router.post('/complete')
async def get_chatting_message(request: ChattingRequest) -> ChatResponse:
    global agent_message_broker
    output = await agent_message_broker.complete(request)
    return ChatResponse(roomId=request.roomId, message=output)


@chat_router.post('/stream')
async def get_chatting_stream_message(request: ChattingRequest) -> StreamingResponse:
    global agent_message_broker
    return StreamingResponse(
        agent_message_broker.stream(request),
        media_type="text/event-stream"
    )


def main():
    app = FastAPI(
        title="Chatting UI",
        description="serve chat ui",
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

    static_file_path = Path("common/resource/app")
    app.mount("/static", StaticFiles(directory=static_file_path, html=True), name="static")

    @app.get("/index")
    async def serve_frontend():
        return FileResponse(static_file_path.joinpath("index.html"))

    return app
