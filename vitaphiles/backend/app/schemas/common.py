from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[str] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class MessageResponse(BaseModel):
    message: str = Field(examples=["ok"])
