from typing import Literal

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    status: Literal["tool_calling", "stream", "Done"] = Field(..., description="Status of the response")
    message: str = Field(..., description="status message")
    content: str | None = Field(..., description="content of the response")

    @property
    def data(self) -> dict:
        return {
            "message": self.message,
            "content": self.content,
        }
