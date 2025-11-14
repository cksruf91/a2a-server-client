from typing import Literal
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    response_type: Literal["text", "data"] | None = Field(..., description="Response type.")
    is_task_complete: bool = Field(..., description="whether response is complete or not")
    require_user_input: bool = Field(..., description="whether need your feedback or not")
    content: str | dict = Field(..., description="Response content")
