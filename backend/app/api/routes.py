import uuid
from collections.abc import Iterator

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.schemas import TaskListResponse, TaskResponse
from app.application.task_service import create_task_from_upload, get_task, list_tasks
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.errors import CloudTaskError
from app.core.metrics import TASKS_CREATED
from app.domain.enums import ProcessingType, TaskStatus
from app.domain.models import User
from app.infrastructure.storage import get_object_storage

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=202, summary="Upload a CSV and create an asynchronous task")
async def create_task(
    file: UploadFile = File(..., description="UTF-8 CSV file with a header row"),
    processing_type: ProcessingType = Form(ProcessingType.CSV_ANALYSIS, alias="processingType"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = await create_task_from_upload(db, file, processing_type, current_user.id)
    TASKS_CREATED.inc()
    return TaskResponse.from_task(task)


@router.get("", response_model=TaskListResponse, summary="List uploaded tasks")
def get_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    tasks = list_tasks(db, limit, offset, current_user.id)
    return TaskListResponse(items=[TaskResponse.from_task(task) for task in tasks], limit=limit, offset=offset)


@router.get("/{task_id}", response_model=TaskResponse, summary="Get one task's current status")
def get_task_by_id(
    task_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> TaskResponse:
    return TaskResponse.from_task(get_task(db, task_id, current_user.id))


def _stream_and_close(body) -> Iterator[bytes]:
    try:
        for chunk in body.iter_chunks(chunk_size=64 * 1024):
            if chunk:
                yield chunk
    finally:
        body.close()


@router.get("/{task_id}/result", summary="Download a completed JSON CSV-analysis report")
def download_result(
    task_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    task = get_task(db, task_id, current_user.id)
    if task.status != TaskStatus.COMPLETED.value or task.result_key is None:
        raise CloudTaskError("A result is not available for this task", 409)
    try:
        object_response = get_object_storage().get_json_response(task.result_key)
    except Exception as error:
        raise CloudTaskError("The result file is temporarily unavailable", 503) from error
    headers = {"Content-Disposition": f'attachment; filename="cloudtask-report-{task.id}.json"'}
    return StreamingResponse(
        _stream_and_close(object_response["Body"]),
        media_type="application/json",
        headers=headers,
    )
