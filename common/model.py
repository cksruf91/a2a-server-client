import uuid
from typing import Literal

from pydantic import BaseModel, Field
from strands.types import content as strands_content


class ChattingRequest(BaseModel):
    question: str = Field(default="안녕?")
    userId: str | None = Field(default=None, description="User ID")
    roomId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    taskId: str | None = Field(default=None)
    history: list[tuple[Literal['user', 'assistant'], str]] = Field(
        default_factory=lambda: [],
        description="chat history, format: [(\"user\",\"hello\"), (\"assistant\": \"hi! how are you doing?\nhow can i help you?\")]"
    )

    def to_model_input(self) -> list[strands_content.Message]:
        messages = []
        for role, content in self.history:
            messages.append(
                strands_content.Message(role=role, content=[
                    strands_content.ContentBlock(text=content)
                ])
            )
        messages.append({"role": "user", "content": [{"text": self.question}]})
        return messages


class ChatResponse(BaseModel):
    message: str = Field()
    roomId: str = Field()
