from pathlib import Path

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastmcp import Client

from common.broker import AgentMessageBroker
from common.model import ChattingRequest

chat_router = APIRouter(prefix='/chat', tags=['chat'])
tool_router = APIRouter(prefix='/tool', tags=['tool'])

agent_message_broker = AgentMessageBroker(agent_url='http://localhost:10000/')

# MCP 서버 목록
MCP_SERVERS = [
    {'name': 'User MCP Server', 'url': 'http://localhost:9011/mcp'},
    {'name': 'Product MCP Server', 'url': 'http://localhost:9012/mcp'},
    {'name': 'Travel MCP Server', 'url': 'http://localhost:5001/mcp'},
]


@chat_router.post('/complete')
async def get_chatting_message(request: ChattingRequest) -> StreamingResponse:
    global agent_message_broker
    return StreamingResponse(
        agent_message_broker.stream(request),
        media_type="text/event-stream"
    )


@chat_router.post('/stream')
async def get_chatting_stream_message(request: ChattingRequest) -> StreamingResponse:
    global agent_message_broker
    return StreamingResponse(
        agent_message_broker.stream(request),
        media_type="text/event-stream"
    )


@tool_router.get('/list')
async def get_tool_list():
    """ 모든 MCP 서버로부터 사용 가능한 도구 목록을 가져옵니다. """
    all_tools = []

    for server in MCP_SERVERS:
        try:
            client = Client(server['url'])
            async with client:
                tools = await client.list_tools()
                for tool in tools:
                    tool_dict = {
                        'name': tool.name,
                        'description': tool.description,
                        'server': server['name']
                    }
                    if hasattr(tool, 'inputSchema'):
                        tool_dict['inputSchema'] = tool.inputSchema
                    all_tools.append(tool_dict)
        except Exception as e:
            print(f"Failed to fetch tools from {server['name']}: {e}")
            continue

    return {"tools": all_tools}


def main():
    app = FastAPI(
        title="Chatting UI",
        description="serve chat ui",
        version="1.0"
    )
    app.include_router(chat_router)
    app.include_router(tool_router)

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

    return app
