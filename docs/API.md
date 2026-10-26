# CloudTask API

The FastAPI server exposes interactive OpenAPI documentation at `/docs` and its schema at `/openapi.json`. All task identifiers are UUIDs.

## Error envelope

Every handled error uses this shape:

```json
{
  "timestamp": "2026-10-22T12:00:00+00:00",
  "status": 422,
  "error": "Request Error",
  "message": "The CSV file is empty",
  "path": "/api/v1/tasks",
  "correlationId": "a6cfd78f-2c6f-4992-a327-c3fd52a0b46e"
}
```

Clients can provide `X-Correlation-ID`; otherwise the API generates one and returns it in the response header.

## Authentication

`POST /api/v1/auth/login` accepts JSON `{ "email": "...", "password": "..." }` and returns a bearer `access_token`. Every task and report endpoint requires `Authorization: Bearer <access_token>`. Authentication failures return `401`; a task belonging to another operator returns `404`. There is no public registration endpoint: the initial account comes from the deployment bootstrap configuration.

## Create a task

`POST /api/v1/tasks`

Content type: `multipart/form-data`

| Field | Required | Value |
| --- | --- | --- |
| `file` | yes | `.csv` UTF-8 file with a header row |
| `processingType` | no | `CSV_ANALYSIS` (default) |

Response: `202 Accepted`

```json
{
  "id": "c508c8af-2aec-4358-8cd5-2bf81c9c0cf1",
  "status": "PENDING",
  "processingType": "CSV_ANALYSIS",
  "originalFilename": "customers.csv",
  "sizeBytes": 43,
  "attemptCount": 0,
  "createdAt": "2026-10-22T12:00:00+00:00",
  "updatedAt": "2026-10-22T12:00:00+00:00",
  "completedAt": null,
  "error": null,
  "resultAvailable": false,
  "resultUrl": null
}
```

The endpoint returns after MinIO storage and one transaction that persists the task and its durable outbox entry. It does not read every row or create the report. A worker reconciliation loop safely retries broker publication after transient failures.

## List tasks

`GET /api/v1/tasks?limit=20&offset=0`

`limit` is between 1 and 100; `offset` is zero or greater. Response:

```json
{
  "items": [{ "id": "c508c8af-2aec-4358-8cd5-2bf81c9c0cf1", "status": "COMPLETED" }],
  "limit": 20,
  "offset": 0
}
```

Each item has the complete task response fields from the create endpoint.

## Get one task

`GET /api/v1/tasks/{taskId}`

Response: `200 OK` with the complete task response. An unknown UUID returns `404`. A failed task has a concise, safe `error` message; it never exposes a Python exception or object-storage credentials.

## Download a report

`GET /api/v1/tasks/{taskId}/result`

Response: `200 OK`, `Content-Type: application/json`, with an attachment filename. A task that is still `PENDING` or `PROCESSING`, or one that has failed, returns `409 Conflict`. The report body has this form:

```json
{
  "taskId": "c508c8af-2aec-4358-8cd5-2bf81c9c0cf1",
  "generatedAt": "2026-10-22T12:01:00+00:00",
  "rowCount": 2,
  "columns": ["name", "age", "score"],
  "estimatedTypes": { "name": "string", "age": "integer", "score": "number" },
  "missingValues": { "name": 0, "age": 1, "score": 0 },
  "numericStatistics": { "age": { "count": 1, "min": 31.0, "max": 31.0, "mean": 31.0 } }
}
```

## Operational routes

| Route | Purpose |
| --- | --- |
| `GET /health` and `GET /health/live` | Lightweight liveness endpoints that confirm the API process is responding. |
| `GET /health/ready` | Readiness endpoint that verifies PostgreSQL, RabbitMQ, and S3 access to the application bucket. Returns `503` while a required dependency is unavailable. |
| `GET /metrics` | Prometheus metrics for API requests and task intake. |
| `GET /docs` | FastAPI Swagger UI. |
| `GET /openapi.json` | OpenAPI JSON schema. |

The worker exposes Prometheus metrics on port `8001`, not a public REST API.

The API returns `429` with `Retry-After` when its process-local request, upload, or login limit is exceeded. Limits are configured with `CLOUDTASK_RATE_LIMIT_*` and are not shared across API replicas.

For Docker Compose deployments, an existing `.env` that omits both complete dedicated PostgreSQL role pairs continues to use its established `CLOUDTASK_POSTGRES_USER` connection for this API and migration job. The new JWT secret and bootstrap-operator values are still required before services can start. This preserves existing database ownership and does not reset credentials.
