from typing import Type, Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from common.utils import call_remote_agent


class AgentToolInput(BaseModel):
    """Input schema for AgentTool."""
    message: str = Field(..., description="description of the task that agent needs to do")


class AgentToolResponse(BaseModel):
    """Output schema for AgentTool."""
    answer: str = Field(..., description="answer to the task")


class AgentTool(BaseTool):
    name: str = "Name of my tool"
    description: str = "What this tool does. It's vital for effective utilization."
    args_schema: Type[BaseModel] = AgentToolInput
    max_usage_count: int = 1
    url: str = Field(..., description="url of the agent")

    def model_post_init(self, __context: Any) -> None:
        self.description += (
            "\narg: {\"message\": \"some message...\"}"
            "\nexample: tool_name(message=\"some message...\")"
        )

    async def _run(self, message: str) -> AgentToolResponse:
        return AgentToolResponse(
            answer=await call_remote_agent(self.url, message)
        )
