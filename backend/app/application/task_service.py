import logging
import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.upload_validation import read_validated_upload
from app.core.errors import NotFoundError, SubmissionError
from app.domain.enums import ProcessingType, TaskStatus
from app.domain.models import OutboxMessage, Task
from app.infrastructure.storage import get_object_storage

logger = logging.getLogger(__name__)


async def create_task_from_upload(
    db: Session, upload: UploadFile, processing_type: ProcessingType, owner_id: uuid.UUID
) -> Task:
    validated = await read_validated_upload(upload)
    task_id = uuid.uuid4()
    task = Task(
        id=task_id,
        owner_id=owner_id,
        processing_type=processing_type.value,
        original_filename=validated.original_filename,
        content_type="text/csv",
        size_bytes=validated.size_bytes,
        input_key=f"inputs/{task_id}.csv",
        status=TaskStatus.PENDING.value,
    )
    storage = get_object_storage()
    object_uploaded = False
    try:
        storage.put_stream(task.input_key, validated.stream, "text/csv")
        object_uploaded = True
        db.add(task)
        # The models intentionally do not define an ORM relationship. Flush the
        # UUID-assigned parent first so PostgreSQL can enforce the outbox FK.
        # This does not commit; the task and outbox remain one transaction.
        db.flush()
        db.add(OutboxMessage(task_id=task_id))
        db.commit()
    except Exception:
        db.rollback()
        if object_uploaded:
            try:
                storage.delete(task.input_key)
            except Exception:
                logger.warning("Could not remove unreferenced upload object", exc_info=True)
        logger.exception("Task upload could not be persisted")
        raise SubmissionError("The upload could not be stored. Please try again.")
    finally:
        validated.stream.close()

    return task


def get_task(db: Session, task_id: uuid.UUID, owner_id: uuid.UUID) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == owner_id))
    if task is None:
        raise NotFoundError()
    return task


def list_tasks(db: Session, limit: int, offset: int, owner_id: uuid.UUID) -> list[Task]:
    statement = select(Task).where(Task.owner_id == owner_id).order_by(Task.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement))
