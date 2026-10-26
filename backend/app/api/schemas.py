import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import Task


class TaskResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    status: str
    processing_type: str = Field(serialization_alias="processingType")
    original_filename: str = Field(serialization_alias="originalFilename")
    size_bytes: int = Field(serialization_alias="sizeBytes")
    attempt_count: int = Field(serialization_alias="attemptCount")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    completed_at: datetime | None = Field(serialization_alias="completedAt")
    error: str | None
    result_available: bool = Field(serialization_alias="resultAvailable")
    result_url: str | None = Field(serialization_alias="resultUrl")

    @classmethod
    def from_task(cls, task: Task) -> "TaskResponse":
        result_url = f"/api/v1/tasks/{task.id}/result" if task.result_available else None
        return cls(
            id=task.id,
            status=task.status,
            processing_type=task.processing_type,
            original_filename=task.original_filename,
            size_bytes=task.size_bytes,
            attempt_count=task.attempt_count,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            error=task.error_message,
            result_available=task.result_available,
            result_url=result_url,
        )


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    timestamp: datetime
    status: int
    error: str
    message: str
    path: str
    correlation_id: str = Field(serialization_alias="correlationId")
