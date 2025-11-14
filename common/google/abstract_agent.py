from abc import abstractmethod, ABCMeta
from typing import AsyncIterable

from common.google.types import AgentResponse


class AbstractAgent(metaclass=ABCMeta):
    def __init__(self, *args, **kwargs) -> None:
        self.agent_name = "default_agent_name"

    @abstractmethod
    def stream(self, *args, **kwargs) -> AsyncIterable[AgentResponse]:
        ...
