import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.core.errors import CsvAnalysisError, RetryableProcessingError
from app.domain.enums import TaskStatus
from app.domain.models import OutboxMessage, Task
from app.infrastructure.storage import get_object_storage
from app.worker.csv_analysis import analyze_csv


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_task(session: Session, task_id: uuid.UUID) -> Task | None:
    return session.get(Task, task_id, with_for_update=True)


def mark_processing(task_id: uuid.UUID) -> bool:
    with get_session_factory()() as session:
        task = _load_task(session, task_id)
        if task is None or task.status != TaskStatus.PENDING.value:
            return False
        task.status = TaskStatus.PROCESSING.value
        task.error_message = None
        task.attempt_count += 1
        task.started_at = _now()
        session.commit()
        return True


def process_task(task_id: uuid.UUID) -> bool:
    """Process one idempotent task. Completed tasks are safely ignored."""
    if not mark_processing(task_id):
        return False
    try:
        with get_session_factory()() as session:
            task = _load_task(session, task_id)
            if task is None:
                return False
            input_bytes = get_object_storage().get_bytes(task.input_key)
            report = analyze_csv(input_bytes, str(task.id))
            result_key = f"reports/{task.id}.json"
            get_object_storage().put_json(result_key, json.dumps(report, indent=2).encode("utf-8"))
            task.result_key = result_key
            task.status = TaskStatus.COMPLETED.value
            task.error_message = None
            task.completed_at = _now()
            session.commit()
            return True
    except CsvAnalysisError:
        raise
    except Exception as error:
        raise RetryableProcessingError("Processing infrastructure is temporarily unavailable") from error


def mark_pending_for_retry(task_id: uuid.UUID) -> None:
    with get_session_factory()() as session:
        task = _load_task(session, task_id)
        if task is not None and task.status != TaskStatus.COMPLETED.value:
            task.status = TaskStatus.PENDING.value
            task.error_message = "Processing will be retried automatically."
            session.commit()


def mark_failed(task_id: uuid.UUID, message: str) -> None:
    with get_session_factory()() as session:
        task = _load_task(session, task_id)
        if task is not None and task.status != TaskStatus.COMPLETED.value:
            task.status = TaskStatus.FAILED.value
            task.error_message = message[:500]
            task.completed_at = _now()
            session.commit()


def recover_expired_processing_tasks(lease_seconds: int) -> int:
    """Return abandoned processing tasks to the durable outbox after a worker crash."""
    cutoff = _now().timestamp() - lease_seconds
    recovered = 0
    with get_session_factory()() as session:
        tasks = session.scalars(
            select(Task).where(
                Task.status == TaskStatus.PROCESSING.value,
                Task.started_at.is_not(None),
                Task.started_at < datetime.fromtimestamp(cutoff, timezone.utc),
            ).with_for_update(skip_locked=True)
        )
        for task in tasks:
            task.status = TaskStatus.PENDING.value
            task.error_message = "Processing was recovered after a worker interruption."
            outbox = session.scalar(select(OutboxMessage).where(OutboxMessage.task_id == task.id))
            if outbox is None:
                session.add(OutboxMessage(task_id=task.id))
            else:
                outbox.published_at = None
            recovered += 1
        session.commit()
    return recovered


def unpublished_outbox_task_ids(limit: int = 50) -> list[uuid.UUID]:
    with get_session_factory()() as session:
        return list(
            session.scalars(
                select(OutboxMessage.task_id)
                .where(OutboxMessage.published_at.is_(None))
                .order_by(OutboxMessage.created_at)
                .limit(limit)
            )
        )


def mark_outbox_published(task_id: uuid.UUID) -> None:
    with get_session_factory()() as session:
        outbox = session.scalar(select(OutboxMessage).where(OutboxMessage.task_id == task_id).with_for_update())
        if outbox is not None:
            outbox.published_at = _now()
            outbox.attempt_count += 1
            outbox.last_error = None
            session.commit()


def mark_outbox_failed(task_id: uuid.UUID) -> None:
    with get_session_factory()() as session:
        outbox = session.scalar(select(OutboxMessage).where(OutboxMessage.task_id == task_id).with_for_update())
        if outbox is not None:
            outbox.attempt_count += 1
            outbox.last_error = "Message publication will be retried."
            session.commit()
