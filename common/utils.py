import uuid

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Part, TextPart, Role, TransportProtocol

from common.http_context import get_httpx_context


async def call_remote_agent(url: str, message: str) -> str:
    async with get_httpx_context() as httpx_context:
        m = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            context_id=str(uuid.uuid4()),
            task_id=None,
            parts=[
                Part(root=TextPart(
                    text=message,
                ))
            ]
        )
        resolver = A2ACardResolver(
            httpx_client=httpx_context,
            base_url=url,
        )
        factory = ClientFactory(
            ClientConfig(
                supported_transports=[TransportProtocol.jsonrpc],
                use_client_preference=True,
                httpx_client=httpx_context,
            )
        )
        client = factory.create(card=await resolver.get_agent_card())
        accumulate_message = ""
        async for task, event in client.send_message(m):
            if hasattr(task, "artifacts") and task.artifacts:
                artifact: Artifact = task.artifacts[-1]  # noqa
                _data = artifact.parts[0].root.data
                accumulate_message += _data['content']

    print(f"[Agent Tool result] | {accumulate_message}")

    return accumulate_message
