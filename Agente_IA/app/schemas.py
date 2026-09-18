from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", min_length=1, max_length=100)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: list[str] = Field(default_factory=list)
    provider: str


class ResetResponse(BaseModel):
    message: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    service: str
    provider: str
