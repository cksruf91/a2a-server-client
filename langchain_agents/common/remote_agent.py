from typing import Callable

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard

from common.http_context import httpx_context
from common.utils import call_remote_agent


class RemoteAgentResolver:

    def __init__(self, agent_url: str, tool_name: str, tool_desc: str):
        self._agent_url = agent_url
        self._tool_name = tool_name
        self._tool_desc = tool_desc

    @httpx_context
    async def get_agent_card(self, httpx_client: httpx.AsyncClient) -> AgentCard:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=self._agent_url
        )
        card = await resolver.get_agent_card()
        return card

    def as_tool(self) -> Callable:
        async def func(message: str):
            return await call_remote_agent(
                url=self._agent_url,
                message=message,
            )

        func.__name__ = self._tool_name
        func.__doc__ = self._tool_desc
        return func
