from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.execution import ExecutionStatus


class ExecutionCreate(BaseModel):
    language: str = Field(min_length=1, max_length=20)
    source_code: str = Field(min_length=1, max_length=100_000)
    stdin: str = Field(default="", max_length=100_000)
    project_id: UUID | None = None
    room_id: UUID | None = None


class ExecutionResponse(BaseModel):
    id: UUID
    user_id: UUID
    project_id: UUID | None
    room_id: UUID | None
    language: str
    status: ExecutionStatus
    created_at: datetime
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class ExecutionResultResponse(ExecutionResponse):
    stdout: str
    stderr: str
    exit_code: int | None
    execution_time_ms: int | None
    memory_kb: int | None
