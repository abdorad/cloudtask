"""Create the configured operator once and safely claim pre-authentication tasks."""

from sqlalchemy import select

from app.core.auth import hash_password
from app.core.config import settings
from app.core.database import get_session_factory
from app.domain.models import Task, User


def main() -> None:
    email = settings.required("bootstrap_user_email").strip().lower()
    password = settings.required("bootstrap_user_password")
    if len(password) < 12:
        raise RuntimeError("CLOUDTASK_BOOTSTRAP_USER_PASSWORD must be at least 12 characters")
    with get_session_factory()() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, password_hash=hash_password(password))
            session.add(user)
            session.flush()
        # Legacy data remains available to its local installation's operator; no rows are deleted.
        for task in session.scalars(select(Task).where(Task.owner_id.is_(None))):
            task.owner_id = user.id
        session.commit()


if __name__ == "__main__":
    main()
