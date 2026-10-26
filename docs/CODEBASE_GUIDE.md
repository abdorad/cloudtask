# CloudTask Codebase Guide

This guide describes the repository as it exists on 2026-10-24. CloudTask is a
learning-oriented, full-stack application for durable, asynchronous CSV
profiling: an authenticated operator uploads a CSV, a background worker creates
a JSON profile, and the operator downloads the result.

## At A Glance

| Area | Technology | Responsibility |
| --- | --- | --- |
| API | Python 3.12, FastAPI | Authentication, upload validation, task API, readiness, metrics |
| Worker | Python 3.12, `aio-pika` | Queue consumption, CSV profiling, retries, task state transitions |
| Database | PostgreSQL 16, SQLAlchemy, Alembic | Users, tasks, lifecycle state, durable outbox |
| Messaging | RabbitMQ | Durable task delivery, retry delay, dead-letter queue |
| Object storage | MinIO via boto3/S3 API | Uploaded CSVs and generated JSON reports |
| Web UI | React 19, Vite, Nginx | Login, upload progress, task polling, report download |
| Observability | Prometheus, Grafana | HTTP, task outcome, and worker-duration metrics |
| Operations | Docker Compose, Kubernetes manifests | Local complete stack and stateless app deployment templates |

The root `AGENTS.md` is the repository's operational contract. In particular,
preserve the four-state lifecycle, use only `CLOUDTASK_*` configuration, keep
uploaded filenames out of storage paths, and add an Alembic migration whenever
the database schema changes.

## Repository Map

```text
cloudtask/
├── backend/
│   ├── app/
│   │   ├── api/               FastAPI routers and API response schemas
│   │   ├── application/       Upload validation and task use cases
│   │   ├── core/              Settings, database, auth, errors, metrics
│   │   ├── domain/            SQLAlchemy models and lifecycle enums
│   │   ├── infrastructure/    RabbitMQ and S3/MinIO adapters
│   │   └── worker/            Queue consumer and CSV profiler
│   ├── alembic/               Database migration environment and revisions
│   ├── scripts/               Config validation, migrations, bootstrap user
│   └── tests/                 Unit tests and PostgreSQL Testcontainers test
├── frontend/
│   └── src/                   React app, API client, components, styles/tests
├── infra/
│   ├── kubernetes/base/       Kustomize-ready app manifests and templates
│   ├── monitoring/            Prometheus and provisioned Grafana dashboard
│   └── postgres/init/         Fresh-volume role initialization script
├── docs/                      Product, API, architecture, roadmap, this guide
├── compose.yaml               Local multi-service deployment
├── .env.example               Safe configuration template
└── AGENTS.md                  Repository-specific engineering rules
```

## End-To-End Flow

```mermaid
sequenceDiagram
    participant UI as React dashboard
    participant API as FastAPI API
    participant DB as PostgreSQL
    participant S3 as MinIO
    participant MQ as RabbitMQ
    participant W as CSV worker

    UI->>API: Login; receive JWT
    UI->>API: Multipart CSV upload + bearer token
    API->>S3: Store inputs/<task-id>.csv
    API->>DB: Commit PENDING task + outbox row
    W->>DB: Find unpublished outbox row
    W->>MQ: Publish durable task message
    MQ->>W: Deliver message
    W->>DB: PENDING → PROCESSING; increment attempt count
    W->>S3: Read CSV, write reports/<task-id>.json
    W->>DB: Mark task COMPLETED
    UI->>API: Poll task status
    UI->>API: Download result with bearer token
    API->>S3: Stream JSON report
```

The API deliberately never profiles the entire CSV during the HTTP request. It
does a bounded upload and header check, then returns `202 Accepted` after the
input object and the task/outbox transaction are durable.

## Backend Structure And Responsibilities

### API layer: `backend/app/api`

- `auth_routes.py` provides `POST /api/v1/auth/login`. It verifies an active
  operator's Argon2 password hash and returns an HS256 JWT.
- `routes.py` provides protected task creation, listing, lookup, and report
  download endpoints. Every query is scoped to the current user, so another
  user's task intentionally looks like a `404`.
- `schemas.py` maps database `Task` objects to the public camelCase response.
  Internal storage keys, owner IDs, and infrastructure details are not exposed.

### Application layer: `backend/app/application`

- `upload_validation.py` copies the upload into a spooled temporary file while
  enforcing the size limit. It accepts only `.csv` filenames and permitted CSV
  content types, sanitizes the display name, and verifies a UTF-8 header with
  non-empty, case-insensitively unique columns.
- `task_service.py` stores the input as `inputs/<UUID>.csv`, then commits the
  `Task` and its `OutboxMessage` in one PostgreSQL transaction. If persistence
  fails after object upload, it attempts to remove the unreferenced object.

### Core: `backend/app/core`

- `config.py` defines `Settings`. Environment variables are prefixed
  `CLOUDTASK_`; `.env` is allowed for local development. Do not add hard-coded
  credentials or a second configuration convention.
- `database.py` provides cached SQLAlchemy engine/session factories. Schema
  creation belongs to Alembic, not to application startup.
- `auth.py` owns password hashing, JWT issuance, and the `get_current_user`
  dependency. Tokens expire after `CLOUDTASK_JWT_EXPIRY_MINUTES`.
- `errors.py` defines safe client-facing error types. `main.py` turns them into
  the shared JSON error envelope and prevents unhandled exception details from
  reaching clients.
- `metrics.py` defines the Prometheus counters/histograms used by the API and
  worker.

### Domain: `backend/app/domain`

`TaskStatus` has exactly four public values:

| Status | Meaning |
| --- | --- |
| `PENDING` | Accepted, queued, or awaiting a retry |
| `PROCESSING` | A worker has claimed the task |
| `COMPLETED` | A report key is stored and downloadable |
| `FAILED` | CSV content is invalid or retry attempts are exhausted |

`models.py` maps three PostgreSQL tables:

- `users`: operator email, Argon2 hash, active state, creation time.
- `tasks`: UUID public ID, nullable legacy-safe owner, lifecycle fields,
  display metadata, deterministic input/result keys, attempts, safe error, and
  timestamps.
- `outbox_messages`: one message record per task, with publication state and
  diagnostics.

The current migrations are `20261022_0001_create_tasks.py` and
`20261023_0002_auth_outbox.py`. Altering models without a new migration will
break deployed databases.

### Infrastructure: `backend/app/infrastructure`

- `storage.py` encapsulates the S3 client. It creates/validates the configured
  bucket and supports stream upload, JSON output, retrieval, and cleanup.
- `messaging.py` declares a durable direct exchange, main queue, TTL retry
  queue, and dead-letter exchange/queue. Message payloads carry a task UUID and
  attempt number; messages are persistent.

### Worker: `backend/app/worker`

- `main.py` starts one RabbitMQ consumer with `prefetch_count=1`, exposes
  metrics on port `8001`, and runs the outbox reconciliation loop.
- `service.py` locks task rows while transitioning state. A message for a task
  that is already non-pending is safely treated as a duplicate. It also returns
  expired `PROCESSING` leases to `PENDING` and republishes them through the
  outbox.
- `csv_analysis.py` reads UTF-8 CSV, detects common delimiters, validates every
  row, and calculates row count, headers, estimated type, missing values, and
  numeric count/min/max/mean.

Worker failures are classified as follows:

| Condition | Result |
| --- | --- |
| Invalid encoding/header/row shape | `FAILED`, message sent to dead-letter queue |
| Temporary storage/database/broker issue | `PENDING`, delayed retry queue |
| Retry limit reached | `FAILED`, message sent to dead-letter queue |
| Redelivered completed/non-pending task | Acknowledged as an idempotent duplicate |

The delivery guarantee is at least once. Idempotency comes from task-state
locking and deterministic `reports/<task-id>.json` keys, not exactly-once queue
delivery.

## HTTP Contract

Interactive OpenAPI documentation is at `/docs`; `docs/API.md` is the
human-oriented source of truth.

| Method | Route | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/login` | No | Exchange operator email/password for a bearer token |
| `POST` | `/api/v1/tasks` | Yes | Upload a CSV and create an asynchronous task (`202`) |
| `GET` | `/api/v1/tasks` | Yes | List the caller's tasks with `limit`/`offset` |
| `GET` | `/api/v1/tasks/{taskId}` | Yes | Get current task state |
| `GET` | `/api/v1/tasks/{taskId}/result` | Yes | Stream a completed JSON report |
| `GET` | `/health`, `/health/live` | No | Process liveness |
| `GET` | `/health/ready` | No | Check PostgreSQL, RabbitMQ, and the S3 bucket |
| `GET` | `/metrics` | No | Prometheus metrics |

All handled failures use an envelope containing timestamp, HTTP status, error,
safe message, path, and correlation ID. A caller may supply
`X-Correlation-ID`; otherwise the API generates and returns one.

`GET /api/v1/tasks/{taskId}/result` returns `409` until the task is completed.
There is intentionally no registration, cancellation, delete-task, or generic
file API.

## Frontend

The browser application is plain JavaScript/JSX; do not introduce TypeScript
unless the project requirements change.

- `App.jsx` stores the bearer token in `localStorage`, refreshes tasks every
  five seconds, and coordinates login, upload, and download.
- `components/LoginForm.jsx` signs in with the bootstrap operator account.
- `components/UploadForm.jsx` supports drag-and-drop/file picker, upload
  progress, and the sole `CSV_ANALYSIS` processing type.
- `components/TaskTable.jsx` shows lifecycle labels, errors, and completed
  downloads.
- `api.js` centralizes fetch/XMLHttpRequest calls and bearer headers.
- `nginx.conf` proxies `/api/`, `/docs`, and `/openapi.json` to the API in a
  Compose deployment; the Vite default API base is therefore `/api/v1`.

## Configuration And Local Operations

Copy `.env.example` to an ignored `.env` and replace every `CHANGE_ME` value.
The application container receives settings through `compose.yaml`; direct
development uses the same `CLOUDTASK_*` names.

Important groups are:

| Group | Examples | Notes |
| --- | --- | --- |
| PostgreSQL | `CLOUDTASK_DATABASE_URL`, role/user/password variables | Migration and runtime roles are separate on a fresh volume; legacy fallback is documented in `README.md`. |
| RabbitMQ | `CLOUDTASK_RABBITMQ_URL`, `CLOUDTASK_MAX_ATTEMPTS` | Delayed retry duration is `CLOUDTASK_RETRY_DELAY_SECONDS`. |
| Object storage | `CLOUDTASK_S3_*` | API and worker use the same bucket; bounded network retry/timeout settings are available. |
| Identity | `CLOUDTASK_JWT_SECRET`, bootstrap email/password | JWT secret must be at least 32 chars; bootstrap password at least 12 chars. |
| API protection | `CLOUDTASK_CORS_ORIGINS`, rate-limit variables | Current sliding-window limits are process-local. |
| Recovery | `CLOUDTASK_OUTBOX_POLL_SECONDS`, `CLOUDTASK_TASK_LEASE_SECONDS` | Tune only with an understanding of duplicate-delivery tradeoffs. |

For the complete local stack, use the README workflow:

```powershell
Copy-Item .env.example .env
# Edit .env and replace every CHANGE_ME value.
docker compose up --build -d
docker compose ps
```

Compose runs PostgreSQL, RabbitMQ, MinIO, config validation, migration, initial
operator creation, API, worker, frontend, Prometheus, and Grafana. The API and
worker do not start until migrations and bootstrap creation complete. All
published ports bind to `127.0.0.1`.

Use `docker compose down` to stop the stack while preserving named volumes.
`docker compose down -v` removes volumes and data, so it is deliberately a
manual/destructive recovery action.

## Tests And Development Changes

The test layout mirrors responsibility:

| Tests | Coverage focus |
| --- | --- |
| `backend/tests/unit/test_upload_validation.py` | Upload bounds, filenames, headers, CSV validation |
| `backend/tests/unit/test_task_service.py`, `test_task_routes.py` | Task use cases and routes |
| `backend/tests/unit/test_worker_service.py`, `test_csv_analysis.py` | State transitions, retries, CSV report logic |
| `backend/tests/unit/test_auth.py` | Authentication behavior |
| `backend/tests/integration/test_task_persistence.py` | PostgreSQL persistence via Testcontainers |
| `frontend/src/components/TaskTable.test.jsx` | Dashboard table rendering |

The repository rules require explicit authorization before running tests, builds,
migrations, Docker Compose, linters, or Kubernetes commands. This guide does
not claim that those commands have been run. When authorized, the documented
commands are `pytest tests/unit`, `pytest tests/integration`, `npm run test`,
and `npm run build` (see `README.md` for setup).

When changing the code:

1. Keep FastAPI route code in `api`, business use cases in `application`, and
   external adapters in `infrastructure`.
2. Add or update focused tests with behavior changes.
3. Add an Alembic migration with every schema change; never rely on
   `Base.metadata.create_all()`.
4. Update `README.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/API.md`,
   and `docs/BACKLOG.md` whenever behavior or operations change.
5. Preserve safe errors, owner scoping, generated object keys, and outbox-backed
   task creation.

## Deployment Notes

`infra/kubernetes/base` provides manifests for the stateless frontend, API,
worker, migration job, bootstrap user job, services, config, ingress, namespace,
secret template, and an opt-in NetworkPolicy template. The API has two replicas
and the worker one; both run as non-root user `10001` with dropped Linux
capabilities and runtime-default seccomp.

Kubernetes does **not** deploy PostgreSQL, RabbitMQ, MinIO, Prometheus, or
Grafana. Treat those as managed/separately operated stateful dependencies. Copy
the secret template locally, replace all placeholders, run the migration and
bootstrap jobs before application rollout, and never commit the completed
secret file.

Before a public or production deployment, address the known gaps: shared rate
limiting, coordinated multi-worker lease handling, backups, TLS, alert rules,
scoped object-storage credentials, lifecycle/account management, and retention
cleanup. `docs/BACKLOG.md` contains the prioritized roadmap.

## Useful Starting Points

- Product intent and limitations: `docs/SPEC.md`
- Component and reliability design: `docs/ARCHITECTURE.md`
- Request/response behavior: `docs/API.md`
- Operational setup, compatibility, and manual walkthrough: `README.md`
- Planned work: `docs/BACKLOG.md`
- Contributor rules: `AGENTS.md`
