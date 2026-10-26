import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api import routes
from app.core.auth import get_current_user
from app.core.database import get_db
from app.domain.enums import TaskStatus
from app.domain.models import Task, User
from app.main import app


def test_create_task_returns_accepted_task_without_processing_upload(monkeypatch):
    now = datetime.now(timezone.utc)
    task = Task(
        id=uuid.uuid4(),
        status=TaskStatus.PENDING.value,
        processing_type="CSV_ANALYSIS",
        original_filename="people.csv",
        content_type="text/csv",
        size_bytes=14,
        input_key="inputs/example.csv",
        created_at=now,
        updated_at=now,
    )

    async def fake_create_task(db, upload, processing_type, owner_id):
        return task

    monkeypatch.setattr(routes, "create_task_from_upload", fake_create_task)
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_current_user] = lambda: User(id=uuid.uuid4(), email="operator@example.com", password_hash="hash")
    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/tasks",
            data={"processingType": "CSV_ANALYSIS"},
            files={"file": ("people.csv", b"name,age\nAda,31\n", "text/csv")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json()["status"] == "PENDING"
    assert response.json()["resultAvailable"] is False
