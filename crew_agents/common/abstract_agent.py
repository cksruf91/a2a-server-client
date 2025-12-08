from abc import ABCMeta, abstractmethod
from typing import AsyncIterable

from a2a.server.agent_execution import RequestContext
from crewai import Agent

from common.types import AgentResponse


class AbstractAgent(metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        self.agent = None
        self.agent_name = 'CrewaiAgent'

    @staticmethod
    @abstractmethod
    def get_agent() -> Agent:
        ...

    @staticmethod
    def prepare_inputs(inputs: RequestContext) -> dict:
        processed_inputs = {}
        if isinstance(inputs, RequestContext):
            question = inputs.get_user_input()
            processed_inputs.update({"question": question})
        elif isinstance(inputs, dict):
            processed_inputs.update(inputs)
        else:
            raise TypeError("inputs must be a RequestContext or dict, but got {}".format(type(inputs)))

        print(f"parsed input : {processed_inputs}")
        return processed_inputs

    async def stream(self, topic: dict | RequestContext) -> AsyncIterable[AgentResponse]:
        if self.agent is None:
            self.agent = self.get_agent()
        topic = self.prepare_inputs(topic)
        result = self.agent.kickoff(topic['question'])
        yield AgentResponse(
            status="stream",
            message="in progress",
            content=result.raw
        )
        yield AgentResponse(
            status="Done",
            message="Done",
            content=".",
        )
