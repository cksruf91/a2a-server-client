from typing import Literal

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    response_type: Literal["text", "data"] | None = Field(..., description="Response type.")
    is_task_complete: bool = Field(..., description="whether response is complete or not")
    content: str | dict = Field(..., description="Response content")

    # def model_post_init(self, context: Any, /) -> None:
    #     try:
    #         content = json.loads(self.content)
    #         self.content = content.get("response")
    #         self.require_user_input = content.get('require_user_input', False)
    #     except json.decoder.JSONDecodeError:
    #         print("json parsing fail")
    #         print(self.content)
    #         pass
    #     print(self)
