import uuid

import pytest
from alembic import command
from alembic.config import Config
from testcontainers.postgres import PostgresContainer

from app.core import database
from app.core.config import settings
from app.domain.enums import TaskStatus
from app.domain.models import OutboxMessage, Task


@pytest.mark.integration
def test_task_is_persisted_after_alembic_migration(monkeypatch):
    with PostgresContainer("postgres:16.4-alpine") as postgres:
        database_url = postgres.get_connection_url()
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        else:
            database_url = database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        monkeypatch.setattr(settings, "database_url", database_url)
        database.get_engine.cache_clear()
        database.get_session_factory.cache_clear()
        try:
            config = Config("alembic.ini")
            command.upgrade(config, "head")
            task_id = uuid.uuid4()
            with database.get_session_factory()() as session:
                session.add(
                    Task(
                        id=task_id,
                        status=TaskStatus.PENDING.value,
                        processing_type="CSV_ANALYSIS",
                        original_filename="people.csv",
                        content_type="text/csv",
                        size_bytes=20,
                        input_key=f"inputs/{task_id}.csv",
                    )
                )
                # Match the upload use case: parent INSERT is flushed before
                # the outbox child references the task UUID.
                session.flush()
                session.add(OutboxMessage(task_id=task_id))
                session.commit()
            with database.get_session_factory()() as session:
                persisted = session.get(Task, task_id)
                outbox = session.query(OutboxMessage).filter_by(task_id=task_id).one_or_none()
                assert persisted is not None
                assert persisted.status == TaskStatus.PENDING.value
                assert outbox is not None
                assert outbox.task_id == persisted.id
        finally:
            database.get_session_factory.cache_clear()
            database.get_engine.cache_clear()
