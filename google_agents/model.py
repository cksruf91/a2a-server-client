import uuid

from pydantic import BaseModel, Field


class ChattingRequest(BaseModel):
    question: str = Field(default="안녕?")
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    taskId: str | None = Field(default=None)
    userId: str | None = Field(default=None)
