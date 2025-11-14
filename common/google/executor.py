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

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        async for item in self.agent.stream(context):
            item: AgentResponse
            # if hasattr(item, 'root') and isinstance(
            #         item.root, SendStreamingMessageSuccessResponse
            # ):
            #     event = item.root.result
            #     if isinstance(
            #             event,
            #             (TaskStatusUpdateEvent | TaskArtifactUpdateEvent),
            #     ):
            #         await event_queue.enqueue_event(event)
            #     continue

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
            if item.require_user_input:
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        item.content,
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
                break
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    item.content,
                    task.context_id,
                    task.id,
                ),
            )

    async def cancel(
            self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
