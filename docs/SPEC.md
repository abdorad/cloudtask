# CloudTask Specification

## Objective

CloudTask is a distributed SaaS platform for asynchronous CSV file processing.

A user must be able to:

1. upload a CSV file;
2. choose a processing type;
3. create an asynchronous task;
4. follow the task status;
5. download the result when processing is complete.

The API must not execute heavy processing directly. It records the request,
validates it, persists metadata, and delegates execution to a worker.

## Current Scope: Phase 0

This phase prepares the repository and documents the target system. It does not
implement the complete business workflow yet.

Phase 0 deliverables:

- repository guidance in `AGENTS.md`;
- product requirements in this file;
- architecture proposal in `docs/ARCHITECTURE.md`;
- API planning in `docs/API.md`;
- structured backlog in `docs/BACKLOG.md`;
- initial README;
- Maven parent project skeleton.

## Target User Workflow

```text
upload CSV -> create task -> worker processes task -> result generated -> user downloads result
```

## Task Lifecycle

| Status | Meaning |
| --- | --- |
| `PENDING` | Task has been created and is waiting for execution. |
| `PROCESSING` | A worker has started processing the task. |
| `COMPLETED` | Processing finished and a result is available. |
| `FAILED` | Processing failed with an error. |
| `RETRYING` | Processing failed temporarily and will be retried. |
| `CANCELLED` | Task was cancelled before successful completion. |

## MVP Functional Requirements

The MVP will provide one end-to-end CSV processing path:

- upload a CSV file;
- create a task for the uploaded file;
- process the task with one local worker;
- generate a JSON report;
- view task status;
- download the result.

The minimal CSV report must include:

- row count;
- column list;
- estimated data types;
- missing values;
- simple statistics for numeric columns.

## Target Technical Requirements

- Java 21.
- Spring Boot for the backend API.
- Maven for compilation and tests.
- PostgreSQL for users, tasks, statuses, and errors.
- Database migrations.
- RabbitMQ for distributed task execution in V2.
- MinIO locally as an S3-compatible object store in V2.
- Docker and Docker Compose.
- Prometheus and Grafana in a later observability phase.
- Kubernetes only after the Docker Compose version is stable.
- A simple React frontend only after backend and security stabilization.

The Spring project page currently lists Spring Boot 4.1.0 as the latest release.
The project will target that line unless local tool compatibility requires a
documented fallback.

## Quality Requirements

- Modular or hexagonal architecture.
- Clear separation between domain, application, infrastructure, and API.
- SOLID principles.
- Dependency injection.
- Input validation.
- Centralized error handling.
- OpenAPI/Swagger documentation.
- Unit tests with JUnit and Mockito.
- Integration tests with Testcontainers.
- No secrets in the repository.
- UUID identifiers for exposed resources.
- Heavy files stored outside PostgreSQL.
- Clear code and documentation suitable for a student project review.

## Explicit Non-Goals For Phase 0

- No complete backend feature implementation.
- No RabbitMQ implementation.
- No MinIO integration.
- No JWT security.
- No frontend.
- No Kubernetes, Terraform, or Helm.
- No monitoring stack.
- No fake test results.

## Open Questions

- Should CloudTask be single-tenant first, then multi-tenant later?
- Which CSV size limit is acceptable for the MVP?
- Which authentication flow is preferred for V3?
- Should the worker be a separate Maven module from the first MVP, or split only
  when RabbitMQ is introduced?
- Which deployment target will be used for portfolio demonstration?
