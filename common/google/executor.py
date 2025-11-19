import asyncio
import datetime
import uuid

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from google.adk.sessions import Session

from common.google.abstract_agent import AbstractAgent
from common.google.types import AgentResponse


class GenericAgentExecutor(AgentExecutor):
    """AgentExecutor used by the travel agents."""

    def __init__(self, agent: AbstractAgent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        print(f'Executing agent, {self.agent.agent_name}')
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
            context.current_task = task

        user_id = context.metadata.get('userId', uuid.uuid4().hex)
        session = await self._manage_session(user_id=user_id, session_id=context.current_task.id)

        updater = TaskUpdater(event_queue, task_id=task.id, context_id=task.context_id)

        async for item in self.agent.stream(context, session):
            item: AgentResponse
            if item.is_task_complete:
                if item.response_type == 'data':
                    part = DataPart(data=item.content)
                else:
                    part = TextPart(text=item.content)

                await updater.add_artifact(
                    [part],
                    name=f'{self.agent.agent_name}-result',
                )
                await updater.complete()
                break
            # if item.require_user_input:
            #     print('require user input : True')
            #     await updater.update_status(
            #         TaskState.input_required,
            #         new_agent_text_message(
            #             item.content,
            #             task.context_id,
            #             task.id,
            #         ),
            #         final=True,
            #     )
            #     break
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    item.content,
                    task.context_id,
                    task.id,
                ),
            )

    async def _get_or_create_session(self, user_id: str, session_id: str) -> Session:
        session = None
        if not session_id:
            session_id = uuid.uuid4().hex
        else:
            session = await self.agent.session_service.get_session(
                app_name=self.agent.agent_name,
                user_id=user_id,
                session_id=session_id,
            )
        if not session:
            session = await self.agent.session_service.create_session(
                app_name=self.agent.agent_name,
                user_id=user_id,
                session_id=session_id,
            )
            print(f"[Session Management] session created : {session.id}")
        else:
            print(f"[Session Management] session retrieved : {session.id}")
        return session

    async def _delete_expired_session(self) -> None:
        session_list = await self.agent.session_service.list_sessions(app_name=self.agent.agent_name)
        print("[Session Management] current session count : {}".format(len(session_list.sessions)))

        delta_time = datetime.timedelta(seconds=2).total_seconds()
        for _session in session_list.sessions:
            if (_session.last_update_time + delta_time) < datetime.datetime.now().timestamp():
                print("[Session Management] session expired, id(last_update_time): {}({})".format(
                    _session.id, _session.last_update_time))
                self.agent.session_service.delete_session(
                    app_name=_session.app_name,
                    user_id=_session.user_id,
                    session_id=_session.id,
                )

    async def _manage_session(self, user_id: str, session_id: str | None) -> Session:
        session = await self._get_or_create_session(user_id, session_id)
        asyncio.create_task(self._delete_expired_session())
        print("[Session Management] finished")
        return session

    async def cancel(
            self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
