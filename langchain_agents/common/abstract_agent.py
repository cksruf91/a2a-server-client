from abc import abstractmethod, ABCMeta
from typing import AsyncIterable

from a2a.server.agent_execution import RequestContext
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph

from common.types import AgentResponse


class AbstractAgent(metaclass=ABCMeta):

    def __init__(self):
        self.agent = None
        self.agent_name = "default agent name"

    @abstractmethod
    async def get_agent(self) -> CompiledStateGraph:
        ...

    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:
        query = context.get_user_input()
        if self.agent is None:
            self.agent = await self.get_agent()

        result = self.agent.astream(
            input={  # type: ignore
                "messages": [HumanMessage(query)]
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
