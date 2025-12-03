import re

import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from common.http_context import httpx_context


class RemoteAgentResolver(RemoteA2aAgent):
    # agent_card_url: str = Field(default=None)

    def __init__(self, name: str, description: str, agent_card: str, *args, **kwargs):
        super().__init__(name=name, description=description, agent_card=agent_card, *args, **kwargs)
        self._agent_card_url = agent_card

    @httpx_context
    async def get_agent_card(self, httpx_client: httpx.AsyncClient) -> AgentCard:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=self.extract_base_url(self._agent_card_url)
        )
        card = await resolver.get_agent_card()
        return card

    @staticmethod
    def extract_base_url(url: str) -> str:
        """
        URL에서 base_url(프로토콜 + 호스트 + 포트)을 추출합니다.

        예시:
        - "http://localhost:10001/.well-known/agent-card.json" -> "http://localhost:10001"
        - "https://example.com/path/to/resource" -> "https://example.com"
        - "http://192.168.1.1:8080/api/v1/data" -> "http://192.168.1.1:8080"
        """
        # 정규 표현식: scheme://host:port 부분만 추출
        pattern = r'^(https?://[^/]+)'
        match = re.match(pattern, url)

        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid URL format: {url}")
