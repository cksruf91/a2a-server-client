from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, DataPart
from a2a.utils import new_task
from a2a.utils.parts import Part

from common.types import AgentResponse


class GenericAgentExecutor(AgentExecutor):
    """Generic Agent Executor for both Strands and Google ADK agents.

    Expects agents to yield dict with format:
    {'status': 'tool_calling|stream|Done', 'data': {'message': '...', 'content': '...'}}
    """

    def __init__(self, agent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        agent_name = getattr(self.agent, 'name', None) or getattr(self.agent, 'agent_name', 'unknown')
        print(f'Executing agent, {agent_name}')
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
            context.current_task = task

        updater = TaskUpdater(event_queue, task_id=task.id, context_id=task.context_id)
        await updater.update_status(
            TaskState.working,
            updater.new_agent_message(
                parts=[Part(root=DataPart(
                    data={'message': 'Thinking...', 'content': None}
                ))]
            )
        )

        accumulate_message = ""
        async for item in self.agent.stream(context):
            item: AgentResponse
            if item.status == "stream":
                accumulate_message += item.content

            if item.status != "stream" and accumulate_message:
                await updater.add_artifact(
                    parts=[Part(root=DataPart(
                        data={"message": "return to user", "content": accumulate_message}
                    ))],
                    name='{} {}'.format(agent_name, str(item.status))
                )
                accumulate_message = ""

            if item.status == "tool_calling":
                await updater.update_status(
                    TaskState.working,
                    updater.new_agent_message(
                        parts=[Part(root=DataPart(data=item.data))]
                    )
                )

            if item.status == "Done":
                print(f"Task completed, {agent_name}, task id: {task.id}")
                await updater.complete()

    async def cancel(
            self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
