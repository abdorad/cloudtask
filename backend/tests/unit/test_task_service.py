from io import BytesIO
import uuid

import pytest

from app.application import task_service
from app.application.upload_validation import ValidatedUpload
from app.domain.enums import ProcessingType
from app.domain.models import OutboxMessage, Task


class FakeStorage:
    def __init__(self):
        self.deleted_key = None

    def put_stream(self, key, stream, content_type):
        assert key.startswith("inputs/")
        assert content_type == "text/csv"

    def delete(self, key):
        self.deleted_key = key


class OrderingSession:
    def __init__(self):
        self.added = []
        self.flushed_task_id = None
        self.committed = False

    def add(self, value):
        if isinstance(value, OutboxMessage):
            assert self.flushed_task_id == value.task_id
        self.added.append(value)

    def flush(self):
        task = next(value for value in self.added if isinstance(value, Task))
        self.flushed_task_id = task.id

    def commit(self):
        self.committed = True

    def rollback(self):
        raise AssertionError("rollback is not expected for a successful persistence transaction")


@pytest.mark.asyncio
async def test_task_is_flushed_before_its_outbox_message_is_added(monkeypatch):
    stream = BytesIO(b"name\nage\n")

    async def fake_read_validated_upload(upload):
        return ValidatedUpload("people.csv", len(stream.getvalue()), stream)

    storage = FakeStorage()
    session = OrderingSession()
    monkeypatch.setattr(task_service, "read_validated_upload", fake_read_validated_upload)
    monkeypatch.setattr(task_service, "get_object_storage", lambda: storage)

    task = await task_service.create_task_from_upload(
        session, object(), ProcessingType.CSV_ANALYSIS, uuid.uuid4()
    )

    outbox = next(value for value in session.added if isinstance(value, OutboxMessage))
    assert session.flushed_task_id == task.id
    assert outbox.task_id == task.id
    assert session.committed is True
    assert storage.deleted_key is None
