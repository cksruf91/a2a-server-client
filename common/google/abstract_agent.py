import uuid
from abc import abstractmethod, ABCMeta
from typing import AsyncIterable

from a2a.server.agent_execution import RequestContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.sessions import Session
from google.genai import types

from common.google.types import AgentResponse


class AbstractAgent(metaclass=ABCMeta):
    def __init__(self, *args, **kwargs) -> None:
        self.agent = None
        self.runner: Runner | None = None
        self.agent_name = "default_agent_name"
        self.session_service = InMemorySessionService()

    @abstractmethod
    async def init_agent_runner(self):
        ...

    async def stream(self, context: RequestContext, session: Session) -> AsyncIterable[AgentResponse]:
        query = context.get_user_input()
        # print("hist : ", context.current_task.history)
        print('Running agent stream for session {context_id} {task_id} - {query}'.format(
            context_id=context.current_task.context_id,
            task_id=context.current_task.id,
            query=query,
        ))
        if not query:
            raise ValueError('Query cannot be empty')

        if not self.runner:
            await self.init_agent_runner()

        user_id = context.metadata.get('userId', uuid.uuid4().hex)

        content = types.Content(role='user', parts=[types.Part(text=query)])
        async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=content,
        ):
            self.middle_event_logging(event)

            if not event.is_final_response():
                yield AgentResponse(
                    response_type=None,
                    is_task_complete=False,
                    content=f"{event.content}: Processing response...",
                )
            else:
                response = ""
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response += part.text + "\n"
                        elif part.function_response:
                            response += part.function_response.model_dump_json() + "\n"
                else:
                    response += f"Error for running agent {self.agent_name}"
                yield AgentResponse(
                    response_type="text",
                    is_task_complete=True,
                    content=response,
                )

    @staticmethod
    def middle_event_logging(event: Event) -> None:
        print("------[Event Log]------")
        for part in event.content.parts:
            if part.function_call:
                print("{name}({args})".format(
                    name=part.function_call.name, args=part.function_call.args))
            elif part.function_response:
                print("{name} response : {resp})".format(
                    name=part.function_response.name, resp=part.function_response.response))
            elif part.text:
                print("{text}".format(text=part.text))
            else:
                print(event.model_dump_json())
