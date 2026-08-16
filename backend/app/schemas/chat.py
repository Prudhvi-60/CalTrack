from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("role")
    @classmethod
    def valid_role(cls, role: str) -> str:
        normalized = role.lower().strip()
        if normalized not in {"user", "assistant"}:
            raise ValueError("role must be user or assistant")
        return normalized


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("message must not be empty")
        return text


class ToolTrace(BaseModel):
    name: str
    ok: bool
    summary: str


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[ToolTrace] = Field(default_factory=list)
