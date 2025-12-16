from abc import abstractmethod, ABCMeta
from typing import AsyncIterable

from a2a.server.agent_execution import RequestContext
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, BaseMessage
from langgraph.graph.state import CompiledStateGraph

from common.types import AgentResponse


class AbstractAgent(metaclass=ABCMeta):

    def __init__(self):
        self.agent_name = "default agent name"

    @abstractmethod
    async def get_agent(self, user_info: dict = None) -> CompiledStateGraph:
        ...

    @staticmethod
    def _parse_message(context: RequestContext) -> list[BaseMessage]:
        messages = []
        if getattr(context.message, "metadata", None) is not None:
            history = context.message.metadata.get("history", [])
            for role, message in history:
                messages.append(
                    HumanMessage(content=message) if role == "user" else AIMessage(content=message)
                )
        messages.append(HumanMessage(context.get_user_input()))
        return messages

    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:

        user_id = None
        if context.message.metadata is not None:
            user_id = context.message.metadata.get('userId', 'unknown')
        agent = await self.get_agent({"user_id": user_id})

        messages = self._parse_message(context)
        result = agent.astream(
            input={  # type: ignore
                "messages": messages
            },
            stream_mode="updates",
            subgraphs=True,
        )

        async for _, event in result:
            if "tools" in event:
                content: ToolMessage = event['tools']['messages'][0]
                message: str = "{}({})".format(content.name, content.content)
                yield AgentResponse(
                    status="tool_calling",
                    message=message,
                    content=None
                )
            elif "model" in event:
                content: AIMessage = event['model']['messages'][0]
                finish_reason = content.response_metadata.get('finish_reason')
                if (finish_reason == 'tool_calls') and content.tool_calls:
                    message = f"[{content.name}({finish_reason})] "
                    for tool_call in content.tool_calls:
                        message += "{}({}) |".format(tool_call["name"], tool_call["args"])
                    yield AgentResponse(
                        status="tool_calling",
                        message=message,
                        content=None
                    )
                elif finish_reason == 'stop':
                    yield AgentResponse(
                        status="stream",
                        message="",
                        content=content.content
                    )
                else:
                    raise RuntimeError(
                        "unexpected event data format: {}".format(event)
                    )
            else:
                raise RuntimeError("unexpected event: {}".format(event))

        yield AgentResponse(
            status="Done",
            message="Done",
            content="."
        )
