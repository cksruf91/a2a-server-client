import json
from typing import Literal, Any

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    response_type: Literal["text", "data"] | None = Field(..., description="Response type.")
    is_task_complete: bool = Field(..., description="whether response is complete or not")
    content: str | dict = Field(..., description="Response content")

    def model_post_init(self, context: Any, /) -> None:
        if isinstance(self.content, dict):
            self.content = json.dumps(self.content, ensure_ascii=False)
