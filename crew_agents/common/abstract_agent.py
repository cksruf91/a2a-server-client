from abc import ABCMeta, abstractmethod
from functools import wraps
from typing import AsyncIterable

from a2a.server.agent_execution import RequestContext
from crewai import Agent, Crew
from crewai.types.streaming import StreamChunkType
from crewai.utilities.types import LLMMessage
from crewai_tools import MCPServerAdapter

from common.types import AgentResponse


def with_mcp_context(func):
    """
    Decorator that conditionally wraps the stream method with MCPServerAdapter context.

    If self.mcp_server_params is not None, creates MCPServerAdapter context and passes
    mcp_tools to the decorated method. Otherwise, passes None as mcp_tools.
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.mcp_server_params is not None:
            with MCPServerAdapter(self.mcp_server_params, connect_timeout=60) as mcp_tools:
                kwargs['mcp_tools'] = mcp_tools
                async for item in func(self, *args, **kwargs):
                    yield item
        else:
            async for item in func(self, *args, **kwargs):
                yield item

    return wrapper


class AbstractAgent(metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        self.agent_name = 'CrewaiAgent'
        self.mcp_server_params: dict | None = None

    @staticmethod
    @abstractmethod
    def get_agent(mcp_tools: MCPServerAdapter) -> Agent | Crew:
        ...

    @staticmethod
    def prepare_inputs(inputs: RequestContext) -> list[LLMMessage]:
        processed_inputs: list[LLMMessage] = []

        a2a_message = inputs.message
        if getattr(a2a_message, "metadata", None) is not None:
            history = a2a_message.metadata.get("history", [])
            for role, message in history:
                processed_inputs.append(
                    LLMMessage(role=role, content=message)
                )

        if isinstance(inputs, RequestContext):
            question = inputs.get_user_input()
            processed_inputs.append(LLMMessage(role="user", content=question))
        elif isinstance(inputs, dict):
            processed_inputs.append(
                LLMMessage(
                    role=inputs.get("role", "user"),  # noqa
                    content=inputs.get("content"),
                )
            )
        else:
            raise TypeError("inputs must be a RequestContext or dict, but got {}".format(type(inputs)))

        print(f"parsed input : {processed_inputs}")
        return processed_inputs

    @with_mcp_context
    async def stream(self, topic: dict | RequestContext, mcp_tools: MCPServerAdapter = None) -> AsyncIterable[
        AgentResponse | str]:

        topic = self.prepare_inputs(topic)
        agent = self.get_agent(mcp_tools)
        if isinstance(agent, Agent):
            result = await agent.kickoff_async(messages=topic)
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
        elif isinstance(agent, Crew):
            streaming = await agent.kickoff_async(inputs={
                "question": topic[0],
                "conversion_history": topic,
            })
            current_task = ""
            async for chunk in streaming:
                # Show task transitions
                if chunk.task_name != current_task:
                    current_task = chunk.task_name
                    print(f"\n[{chunk.agent_role}] Working on: {chunk.task_name}")
                    print("-" * 60)

                # Display text chunks
                if chunk.chunk_type == StreamChunkType.TEXT:
                    ...  # print("text: ", chunk.content, end="", flush=True)

                # Display tool calls
                elif chunk.chunk_type == StreamChunkType.TOOL_CALL and chunk.tool_call:
                    print(f"\n🔧 Using tool: {chunk.tool_call.tool_name}")

            # Show final result
            result = streaming.result
            print(f"\nToken Usage: {result.token_usage}")
            yield AgentResponse(
                status="stream",
                message="in progress",
                content=str(result)
            )

            yield AgentResponse(
                status="Done",
                message="Done",
                content=".",
            )
