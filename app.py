import asyncio
from pathlib import Path

import nest_asyncio
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from host.host_agent import StrandsHostAgent, ChatResponse, ChattingRequest, a2a_application_emitter

nest_asyncio.apply()
chat_router = APIRouter(prefix='/chat', tags=['chat'])


@chat_router.post('/complete')
async def get_chatting_message(request: ChattingRequest) -> ChatResponse:
    output = await StrandsHostAgent().complete(request)
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

    @app.get("/index")
    async def serve_frontend():
        return FileResponse(static_file_path.joinpath("index.html"))

    a2a_app = asyncio.run(a2a_application_emitter())
    app.mount('/', a2a_app.build())

    return app
