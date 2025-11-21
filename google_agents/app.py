from typing import AsyncIterable

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .broker import AgentMessageBroker
from .model import ChattingRequest


class TravelAssistantClient:
    """Client for communicating with travel_assistant_agent via A2A protocol"""

    AGENT_URL = 'http://localhost:10000'

    def __init__(self):
        self.broker = AgentMessageBroker(agent_url=self.AGENT_URL)

    async def get_agent_card(self) -> dict:
        """Fetch the agent card from travel_assistant_agent"""
        agent_card = await self.broker.get_agent_card()
        return agent_card.model_dump()

    async def stream_chat(self, request: ChattingRequest) -> AsyncIterable[bytes]:
        """Stream chat responses from travel_assistant_agent"""
        async for bytes_ in self.broker.stream(request=request):
            yield bytes_

    async def close(self):
        """Close the HTTP client"""
        await self.broker.aclose()


# API Router
chat_router = APIRouter(prefix='/chat', tags=['chat'])


@chat_router.post('/stream')
async def chat_stream(request: ChattingRequest) -> StreamingResponse:
    """Stream chat responses from travel_assistant_agent"""
    travel_client = TravelAssistantClient()
    return StreamingResponse(
        travel_client.stream_chat(request),
        media_type="text/event-stream; charset=utf-8"
    )


@chat_router.get('/health')
async def health_check():
    """Health check endpoint"""
    travel_client = TravelAssistantClient()
    try:
        card = await travel_client.get_agent_card()
        return {
            "status": "healthy",
            "agent": card if card else "unknown",
            "agent_url": TravelAssistantClient.AGENT_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def main():
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Travel Assistant API",
        description="FastAPI app for communicating with travel_assistant_agent",
        version="1.0.0",
        # lifespan=lifespan
    )

    # Include chat router
    app.include_router(chat_router)

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(main(), host="0.0.0.0", port=8080)
