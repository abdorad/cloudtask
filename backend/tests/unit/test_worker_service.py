import uuid
from contextlib import AbstractContextManager

from app.domain.enums import TaskStatus
from app.domain.models import Task
from app.worker import service


class FakeSession(AbstractContextManager):
    def __init__(self, task):
        self.task = task
        self.commits = 0

    def get(self, model, task_id, with_for_update=False):
        return self.task if task_id == self.task.id else None

    def commit(self):
        self.commits += 1


class FakeStorage:
    def __init__(self):
        self.report = None

    def get_bytes(self, key):
        return b"name,age\nAda,31\n"

    def put_json(self, key, body):
        self.report = (key, body)


def test_worker_stores_deterministic_report_and_marks_task_complete(monkeypatch):
    task = Task(
        id=uuid.uuid4(),
        status=TaskStatus.PROCESSING.value,
        processing_type="CSV_ANALYSIS",
        original_filename="people.csv",
        content_type="text/csv",
        size_bytes=16,
        input_key="inputs/example.csv",
    )
    session = FakeSession(task)
    storage = FakeStorage()
    monkeypatch.setattr(service, "mark_processing", lambda task_id: True)
    monkeypatch.setattr(service, "get_session_factory", lambda: lambda: session)
    monkeypatch.setattr(service, "get_object_storage", lambda: storage)

    assert service.process_task(task.id) is True
    assert task.status == TaskStatus.COMPLETED.value
    assert task.result_key == f"reports/{task.id}.json"
    assert storage.report[0] == task.result_key
