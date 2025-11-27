from abc import abstractmethod, ABCMeta

from a2a import types as a2a_types
from strands import Agent
from strands.agent.agent_result import AgentResult
from strands.types import content as strands_content


class AbstractAgent(metaclass=ABCMeta):

    def __init__(self):
        self.agent: Agent | None = None

    @abstractmethod
    async def get_agent(self) -> Agent:
        ...

    @abstractmethod
    async def invoke(self, message: a2a_types.Message) -> str:
        ...

    @staticmethod
    def _logging_metrics(result: AgentResult) -> AgentResult:
        # Access metrics through the AgentResult
        print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
        print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
        print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
        return result

    @staticmethod
    def _parsing_a2a_message(a2a_message: a2a_types.Message) -> strands_content.Message:
        if a2a_message is None:
            raise ValueError("input message is None")
        message = strands_content.Message(role='user', content=[])
        for part in a2a_message.parts:
            if part.root.kind == "text":
                message['content'].append(
                    strands_content.ContentBlock(text=part.root.text)
                )
        return message
