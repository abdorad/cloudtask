# CloudTask Agent Instructions

You are the lead software engineer for CloudTask.

CloudTask is a private local repository for a distributed SaaS platform that
processes uploaded CSV files asynchronously. The codebase must remain clear,
incremental, testable, and explainable by a third-year undergraduate student.

## Current Phase

Phase 0 is documented and committed. The next authorized implementation phase is
Phase 1: the MVP. Do not start Phase 2 distributed infrastructure, security,
frontend, monitoring, or Kubernetes until the MVP is stable.

## Product Goal

A user must be able to:

1. upload a CSV file;
2. choose a processing type;
3. create an asynchronous task;
4. follow the task status;
5. download the result when processing is complete.

The API must never execute heavy processing directly. It records the request
and delegates execution to a worker.

## Task Lifecycle

The domain status values are:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`
- `RETRYING`
- `CANCELLED`

## Target Architecture

- Java 21.
- Spring Boot for the backend API.
- Maven for builds.
- PostgreSQL for users, tasks, statuses, and errors.
- RabbitMQ for task distribution.
- Worker process or module for CSV processing.
- MinIO locally as an S3-compatible object store.
- Docker and Docker Compose for local orchestration.
- Prometheus and Grafana for observability.
- Kubernetes in a later phase only.
- Simple web frontend after backend stabilization.

## Engineering Rules

- Build one phase at a time.
- Do not start RabbitMQ, MinIO, Kubernetes, Terraform, Helm, frontend, or
  monitoring during the MVP.
- Avoid unnecessary microservices.
- Keep domain, application, infrastructure, and API concerns separated.
- Prefer modular or hexagonal architecture.
- Use dependency injection and SOLID design.
- Validate inputs.
- Use centralized error handling.
- Document the API with OpenAPI/Swagger.
- Use migrations for database schema changes.
- Use UUIDs for externally exposed resources.
- Never store heavy file contents directly in PostgreSQL.
- Never commit secrets, credentials, generated tokens, or real local `.env` files.
- Do not add a technology without documenting why it is useful.
- Do not claim that tests passed unless they were actually executed.

## Testing Expectations

- Unit tests with JUnit and Mockito.
- Integration tests with Testcontainers.
- Run available tests before reporting completion.
- Report real command results, including failures and skipped commands.

## Repository Map

- `backend/`: future Spring Boot API module.
- `worker/`: future worker module or process.
- `frontend/`: future React/Vite frontend.
- `infra/docker/`: Docker and Docker Compose assets.
- `infra/kubernetes/`: later Kubernetes manifests.
- `infra/monitoring/`: later Prometheus and Grafana assets.
- `docs/`: specifications, architecture, API notes, and backlog.

## Documentation Rules

- Update `docs/SPEC.md` when product behavior changes.
- Update `docs/ARCHITECTURE.md` when system boundaries or technology choices change.
- Update `docs/API.md` when API contracts change.
- Update `docs/BACKLOG.md` when scope moves between phases.
- Keep `README.md` aligned with actual commands and implemented capabilities.
