from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import CloudTaskError
from app.domain.models import User

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    return jwt.encode({"sub": str(user.id), "exp": expires_at}, settings.required_jwt_secret(), algorithm="HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), db: Session = Depends(get_db)
) -> User:
    if credentials is None:
        raise CloudTaskError("Authentication is required", 401)
    try:
        claims = jwt.decode(credentials.credentials, settings.required_jwt_secret(), algorithms=["HS256"])
        user_id = claims.get("sub")
        user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    except (jwt.InvalidTokenError, ValueError):
        user = None
    if user is None:
        raise CloudTaskError("Authentication is required", 401)
    return user
