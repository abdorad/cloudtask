# CloudTask Agent Instructions

CloudTask is a learning-oriented, portfolio-quality application for durable asynchronous CSV analysis. Keep the implementation simple enough for a third-year computer-science student to follow.

## Stack and boundaries

- Backend and worker: Python 3.12, FastAPI, SQLAlchemy, Alembic.
- Web client: React with JavaScript and JSX only. Do not add TypeScript files.
- Persistence: PostgreSQL stores task metadata and lifecycle state.
- Messaging: RabbitMQ distributes durable task messages.
- File storage: MinIO through its S3-compatible API stores uploaded CSV files and JSON reports.
- Observability: Prometheus scrapes API and worker metrics; Grafana visualizes them.
- Local orchestration: Docker Compose. Kubernetes manifests deploy stateless app components and expect external stateful dependencies.

## Product rules

1. The API accepts, validates, stores, and queues a CSV. It never generates the report in the HTTP request.
2. Public task IDs are UUIDs.
3. The supported lifecycle is `PENDING`, `PROCESSING`, `COMPLETED`, and `FAILED`.
4. Object keys are generated from task UUIDs. Never use an uploaded filename as a path or object key.
5. PostgreSQL is the source of truth for task state. RabbitMQ can redeliver messages, so worker handling must remain idempotent.
6. Never add authentication unless the product specification is changed first.

## Engineering conventions

- Keep HTTP routes in `backend/app/api`, use cases in `backend/app/application`, integrations in `backend/app/infrastructure`, and CSV processing in `backend/app/worker`.
- Read configuration only from `CLOUDTASK_*` environment variables. Do not hardcode credentials, endpoints, or secrets.
- Add an Alembic migration for every schema change. Do not use `Base.metadata.create_all()` as a deployment path.
- Preserve the single shared API error shape and avoid returning internal exceptions to clients.
- Keep direct dependencies pinned in `backend/pyproject.toml` and `backend/requirements.txt`.
- Update `README.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, and `docs/BACKLOG.md` when behavior or operations change.

## Testing and operations

- Backend tests live in `backend/tests`; React tests live beside the UI components.
- The PostgreSQL integration test uses Testcontainers and requires Docker.
- Tests, builds, linters, Docker Compose, migrations, and Kubernetes commands must only be run when the current task explicitly authorizes them. Report only commands that actually ran.
- `.env`, copied Kubernetes secrets, runtime data, and dependency directories must remain outside Git.
