import inspect
import json
import uuid
from functools import wraps
from typing import Callable, AsyncIterable

import httpx
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig, Client
from a2a.types import TransportProtocol, Message, Role, Part, TextPart, Task, TaskStatusUpdateEvent, \
    TaskArtifactUpdateEvent, TaskQueryParams, AgentCard
from sse_starlette.sse import ServerSentEvent


def httpx_context(func: Callable):
    """
    비동기 함수 또는 비동기 제너레이터 함수를 래핑하는 데코레이터로, `httpx.AsyncClient` 인스턴스를 제공합니다.
    데코레이트된 함수는 미리 정의된 타임아웃과 헤더 설정이 포함된 HTTP 클라이언트에 접근할 수 있습니다.
    `httpx.AsyncClient` 인스턴스는 데코레이트된 함수의 **kwargs를 통해 `httpx_client` 인자로 전달됩니다.

    비동기 제너레이터 함수의 경우, 래퍼는 값을 yield하는 동안 `httpx.AsyncClient`가 적절하게 관리되도록 보장합니다.

    Args:
        func: 래핑할 비동기 함수 또는 비동기 제너레이터 함수

    Returns:
        `httpx.AsyncClient` 인스턴스가 함수의 **kwargs로 주입된 입력 함수 또는 제너레이터 함수의 래핑된 버전
    """
    if inspect.isasyncgenfunction(func):
        # Async generator function (yields values)
        @wraps(func)
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
    else:
        # Regular async function (returns a value)
        @wraps(func)
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

    @httpx_context
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
            print(f"task({task.id}) - {task.status.state}")
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
