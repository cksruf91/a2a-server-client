from abc import ABCMeta, abstractmethod
from typing import AsyncIterable

from a2a.server.agent_execution import RequestContext
from crewai import Agent, Crew
from crewai.types.streaming import StreamChunkType

from common.types import AgentResponse


class AbstractAgent(metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        self.agent = None
        self.agent_name = 'CrewaiAgent'

    @staticmethod
    @abstractmethod
    def get_agent() -> Agent | Crew:
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

    async def stream(self, topic: dict | RequestContext) -> AsyncIterable[AgentResponse | str]:
        if self.agent is None:
            self.agent = self.get_agent()
        topic = self.prepare_inputs(topic)
        if isinstance(self.agent, Agent):
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
        elif isinstance(self.agent, Crew):
            streaming = await self.agent.kickoff_async(inputs={"question": topic['question']})
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
