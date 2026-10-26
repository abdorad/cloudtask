import asyncio
import logging
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

import aio_pika
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.api.auth_routes import router as auth_router
from app.api.routes import router as task_router
from app.core.config import settings
from app.core.database import get_session_factory
from app.core.errors import CloudTaskError
from app.core.metrics import API_DURATION, API_REQUESTS
from app.infrastructure.storage import get_object_storage

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudTask API",
    version="0.1.0",
    description="Asynchronous CSV analysis API. OpenAPI documentation is available at /docs.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)
app.include_router(task_router)
app.include_router(auth_router)


class InMemoryRateLimiter:
    """A bounded, per-process sliding window limiter for a single API replica."""

    def __init__(self) -> None:
        self._requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def allowed(self, bucket: str, client: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.monotonic()
        key = (bucket, client)
        requests = self._requests[key]
        while requests and requests[0] <= now - window:
            requests.popleft()
        if len(requests) >= limit:
            return False, max(1, int(window - (now - requests[0])))
        requests.append(now)
        return True, 0


rate_limiter = InMemoryRateLimiter()


@app.middleware("http")
async def request_observability(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    started = time.perf_counter()
    client = request.client.host if request.client else "unknown"
    checks = [("request", settings.rate_limit_requests)]
    if request.method == "POST" and request.url.path == "/api/v1/tasks":
        checks.append(("upload", settings.rate_limit_uploads))
    if request.method == "POST" and request.url.path == "/api/v1/auth/login":
        checks.append(("login", settings.rate_limit_login_attempts))
    for bucket, limit in checks:
        allowed, retry_after = rate_limiter.allowed(bucket, client, limit, settings.rate_limit_window_seconds)
        if not allowed:
            response = _error_response(request, 429, "Too Many Requests", "Please wait before trying again")
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled API request")
        response = _error_response(request, 500, "Internal Server Error", "The request could not be completed")
    response.headers["X-Correlation-ID"] = correlation_id
    route = request.scope.get("route")
    route_path = getattr(route, "path", "/unmatched")
    API_REQUESTS.labels(request.method, route_path, response.status_code).inc()
    API_DURATION.labels(request.method, route_path).observe(time.perf_counter() - started)
    return response


def _error_response(request: Request, status_code: int, error: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status_code,
            "error": error,
            "message": message,
            "path": request.url.path,
            "correlationId": getattr(request.state, "correlation_id", "unknown"),
        },
    )


@app.exception_handler(CloudTaskError)
async def cloudtask_error_handler(request: Request, error: CloudTaskError) -> JSONResponse:
    return _error_response(request, error.status_code, "Request Error", error.message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    return _error_response(request, 422, "Validation Error", "The request is not valid")


@app.get("/health", tags=["operations"], include_in_schema=False)
@app.get("/health/live", tags=["operations"], include_in_schema=False)
def liveness() -> dict[str, str]:
    return {"status": "ok"}


def _check_database_and_storage() -> None:
    with get_session_factory()() as session:
        session.execute(text("SELECT 1"))
    # This verifies the configured endpoint and credentials, and creates the
    # application bucket if it has not been created by a previous upload.
    get_object_storage().ensure_bucket()


@app.get("/health/ready", tags=["operations"], include_in_schema=False)
async def readiness(request: Request) -> JSONResponse:
    try:
        await asyncio.to_thread(_check_database_and_storage)
        connection = await aio_pika.connect_robust(
            settings.required("rabbitmq_url"), timeout=settings.s3_connect_timeout_seconds
        )
        await connection.close()
    except Exception:
        logger.warning("Readiness check could not reach a required dependency", exc_info=True)
        return _error_response(
            request,
            503,
            "Service Unavailable",
            "A required dependency is temporarily unavailable",
        )
    return JSONResponse(status_code=200, content={"status": "ready"})


@app.get("/metrics", include_in_schema=False)
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
