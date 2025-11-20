import json
import uuid
from typing import Callable, AsyncIterable

import httpx
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig, Client
from a2a.types import TransportProtocol, Message, Role, Part, TextPart, Task, TaskStatusUpdateEvent, \
    TaskArtifactUpdateEvent, TaskQueryParams, AgentCard
from sse_starlette.sse import ServerSentEvent


def httpx_context(func: Callable):
    async def wrapper(*args, **kwargs):
        async with httpx.AsyncClient(
                timeout=60,
                headers={
                    "Content-Type": "application/json",
                }
        ) as httpx_client:
            kwargs['httpx_client'] = httpx_client
            return await func(*args, **kwargs)

    return wrapper


def stream_httpx_context(func: Callable):
    async def wrapper(*args, **kwargs):
        async with httpx.AsyncClient(
                timeout=60,
                headers={
                    "Content-Type": "application/json",
                }
        ) as httpx_client:
            kwargs['httpx_client'] = httpx_client
            async for event in func(*args, **kwargs):
                yield event

    return wrapper


class AgentMessageBroker:

    def __init__(self, agent_url: str) -> None:
        self.agent_url = agent_url
        self.client: Client | None = None
        self.httpx_client = None

    async def _get_client(self, httpx_client: httpx.AsyncClient) -> Client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=self.agent_url,
        )
        factory = ClientFactory(
            ClientConfig(
                supported_transports=[TransportProtocol.jsonrpc],
                use_client_preference=True,
                httpx_client=httpx_client,
            )
        )
        return factory.create(card=await resolver.get_agent_card())

    @httpx_context
    async def get_agent_card(self, httpx_client: httpx.AsyncClient) -> AgentCard:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=self.agent_url,
        )
        return await resolver.get_agent_card()

    @httpx_context
    async def complete(self, message: str, httpx_client: httpx.AsyncClient = None) -> str:
        # self.httpx_client = httpx_client
        # self.client = await self._get_client(httpx_client)
        raise NotImplementedError('complete is not implemented yet')

    @stream_httpx_context
    async def stream(self, message: str, httpx_client: httpx.AsyncClient = None) -> AsyncIterable[bytes]:
        self.httpx_client = httpx_client
        self.client = await self._get_client(httpx_client)

        m = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            parts=[
                Part(root=TextPart(
                    text=message,
                ))
            ]
        )

        output = None
        task: Task | None = None
        event: TaskStatusUpdateEvent | TaskArtifactUpdateEvent | None = None
        async for task, event in self.client.send_message(m):
            print("-" * 50 + "[Event]" + "-" * 50)
            if task:
                yield ServerSentEvent(
                    event='working',
                    data=json.dumps(
                        {'message': 'response', 'contents': f"task({task.id}) - {task.status.state}"}
                    )
                ).encode()

        if not task:
            raise RuntimeError(f"failed to get task, event: {event.model_dump_json(ensure_ascii=False)}")

        response = await self.client.get_task(TaskQueryParams(id=task.id, history_length=1))
        if hasattr(response, 'artifacts') and response.artifacts:
            for artifact in response.artifacts:
                output = artifact.parts[0].root.text

        if not output:
            raise RuntimeError(f"failed to parse response, task: {task.model_dump_json(ensure_ascii=False)}")

        yield ServerSentEvent(
            event='Done',
            data=json.dumps(
                {'message': 'response', 'contents': output}
            )
        ).encode()

    async def aclose(self) -> None:
        if self.httpx_client:
            await self.httpx_client.aclose()
