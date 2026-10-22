# CloudTask

CloudTask is a private local project for a distributed SaaS platform that
processes CSV files asynchronously.

The target workflow is:

```text
upload CSV -> create task -> worker processing -> JSON report -> result download
```

## Current Status

Phase 0 is complete: repository preparation, specifications, architecture, API
contract, and backlog are documented. No business feature has been implemented
yet.

The next planned lot is Phase 1, the MVP: a local Spring Boot backend with
PostgreSQL, one multipart CSV upload-and-task endpoint, one worker, JSON report
generation, status lookup, result download, and cancellation request.

## Target Stack

- Java 21.
- Spring Boot for the API.
- Maven for build and tests.
- PostgreSQL for users, tasks, statuses, and errors.
- RabbitMQ for distributed workers in Phase 2.
- MinIO for S3-compatible local object storage in Phase 2.
- Docker Compose for local orchestration.
- Prometheus and Grafana for observability in a later phase.
- Kubernetes only after the Docker Compose version is stable.
- React with Vite and TypeScript for the later frontend.

## Repository Layout

```text
cloudtask/
├── AGENTS.md
├── README.md
├── pom.xml
├── docs/
│   ├── SPEC.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── BACKLOG.md
├── backend/
├── worker/
├── frontend/
├── infra/
│   ├── docker/
│   ├── kubernetes/
│   └── monitoring/
└── .github/
    └── workflows/
```

## Documentation

- [Specification](docs/SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API plan](docs/API.md)
- [Backlog](docs/BACKLOG.md)

## Planned Maven Commands

These commands will be used once Maven and project modules are available:

```powershell
mvn validate
mvn test
mvn verify
```

After Docker-based integration tests are added:

```powershell
docker compose up --build
mvn verify
```

## Local Repository

This repository is local only. No remote is configured.
