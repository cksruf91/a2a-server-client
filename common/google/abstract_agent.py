import asyncio
import datetime
import json
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

    async def stream(self, context: RequestContext) -> AsyncIterable[AgentResponse]:
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
        session = await self._manage_session(user_id=user_id, session_id=context.current_task.id)

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
                    require_user_input=False,
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

                try:
                    response = json.loads(response)
                except json.decoder.JSONDecodeError:
                    print(f"Invalid response format : {response}")

                require_user_input = response.get('require_user_input', False)
                yield AgentResponse(
                    response_type="text",
                    is_task_complete=False if require_user_input else True,
                    require_user_input=require_user_input,
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

    async def _get_or_create_session(self, user_id: str, session_id: str) -> Session:
        print(f"session id: {session_id}")
        session = None
        if not session_id:
            session_id = uuid.uuid4().hex
        else:
            session = await self.session_service.get_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id,
            )
        if not session:
            session = await self.session_service.create_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id,
            )
            print(f"[{self.agent_name} Session Management] session created : {session.id}")
        else:
            print(f"[{self.agent_name} Session Management] session retrieved : {session.id}")
        return session

    async def _delete_expired_session(self) -> None:
        session_list = await self.session_service.list_sessions(app_name=self.agent_name)
        print(f"[{self.agent_name} Session Management] current session count : {len(session_list.sessions)}")

        delta_time = datetime.timedelta(seconds=60).total_seconds()
        for _session in session_list.sessions:
            if (_session.last_update_time + delta_time) < datetime.datetime.now().timestamp():
                print(f"[{self.agent_name} Session Management] session expired, "
                      f"id(last_update_time): {_session.id}({_session.last_update_time})")
                await self.session_service.delete_session(
                    app_name=_session.app_name,
                    user_id=_session.user_id,
                    session_id=_session.id,
                )

    async def _manage_session(self, user_id: str, session_id: str | None) -> Session:
        session = await self._get_or_create_session(user_id, session_id)
        asyncio.create_task(self._delete_expired_session())
        print(f"[{self.agent_name} Session Management] finished, session_id: {session.id}")
        return session
