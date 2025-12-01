import json
from abc import abstractmethod, ABCMeta
from typing import AsyncIterable

from a2a import types as a2a_types
from a2a.server.agent_execution import RequestContext
from strands import Agent
from strands.agent.agent_result import AgentResult
from strands.types import content as strands_content

from common.types import AgentResponse


class AbstractAgent(metaclass=ABCMeta):

    def __init__(self):
        self.agent: Agent | None = None
        self.name: str = "Strands Agent"

    @abstractmethod
    async def get_agent(self, *args, **kwargs) -> Agent:
        ...

    @abstractmethod
    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:
        ...

    async def _run_agent(self, agent: Agent, context: RequestContext) -> AsyncIterable[AgentResponse]:
        # context.get_user_input()
        message = self._parsing_a2a_message(context.message)

        async for event in agent.stream_async(message):
            status_message = ""
            if 'current_tool_use' in event:
                tool_name = event['current_tool_use'].get('name')
                status_message += f"func call: {tool_name}"
                input_: str = event['current_tool_use'].get('input', '')
                try:
                    params = json.loads(input_)
                    status_message += f"({params})"
                except json.decoder.JSONDecodeError:
                    continue

                yield AgentResponse(
                    status="tool_calling",
                    message=status_message,
                    content=None
                )
            elif "data" in event:
                yield AgentResponse(
                    status="stream",
                    message="in progress",
                    content=event['data']
                )

        yield AgentResponse(
            status="Done",
            message="Done",
            content=""
        )

    @staticmethod
    def _logging_metrics(result: AgentResult) -> AgentResult:
        # Access metrics through the AgentResult
        print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
        print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
        print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
        return result

    @staticmethod
    def _parsing_a2a_message(a2a_message: a2a_types.Message) -> list[strands_content.Message]:
        if a2a_message is None:
            raise ValueError("input message is None")

        messages = []
        if getattr(a2a_message, "metadata", None) is not None:
            history = a2a_message.metadata.get("history", [])
            for role, message in history:
                messages.append(
                    strands_content.Message(
                        role=role, content=[strands_content.ContentBlock(text=message)]
                    )
                )

        message = strands_content.Message(role='user', content=[])
        for part in a2a_message.parts:
            if part.root.kind == "text":
                message['content'].append(
                    strands_content.ContentBlock(text=part.root.text)
                )
        messages.append(message)
        return messages
