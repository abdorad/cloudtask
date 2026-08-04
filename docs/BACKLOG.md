# CloudTask Backlog

## MVP: Local End-To-End Backend

Goal: prove the complete CSV task workflow with the smallest useful backend.

- Spring Boot API module.
- PostgreSQL persistence.
- Database migrations.
- `Task` entity with UUID public ID.
- Local temporary file storage behind a `FileStorage` interface.
- One processing type: `CSV_ANALYSIS`.
- One local worker or background executor behind a `TaskDispatcher` interface.
- REST routes:
  - `POST /api/files`
  - `POST /api/tasks`
  - `GET /api/tasks/{id}`
  - `GET /api/tasks`
  - `GET /api/tasks/{id}/result`
  - `GET /actuator/health`
- JSON report containing row count, columns, estimated types, missing values,
  and simple numeric statistics.
- OpenAPI/Swagger documentation.
- `.env.example`.
- README curl examples.
- Unit tests and PostgreSQL integration tests with Testcontainers.

## V2: Distributed Processing

Goal: replace local processing and local storage with distributed components.

- RabbitMQ exchange, processing queue, dead-letter exchange, and dead-letter
  queue.
- Versioned messages with `correlationId`.
- Retry policy with progressive delay.
- Maximum attempt count.
- Idempotent worker behavior for duplicate messages.
- MinIO input and output buckets.
- S3-compatible `ObjectStorage` implementation.
- Temporary download links.
- Docker Compose with services:
  - `api`
  - `worker`
  - `postgres`
  - `rabbitmq`
  - `minio`
- Healthchecks, volumes, internal network, and environment variables.
- Testcontainers tests for PostgreSQL, RabbitMQ, MinIO, retries, DLQ,
  duplicates, and end-to-end processing.

## V3: Security And Users

Goal: make CloudTask multi-user and protect user data.

- User registration and login.
- JWT authentication.
- BCrypt password hashing.
- Token expiration or refresh policy.
- Protected task and file routes.
- Per-user task and file authorization.
- Secure task deletion with file cleanup.
- Sensitive action audit logs.
- Configurable upload size limit.
- MIME type and extension validation.
- Filename sanitization.
- Empty file rejection.
- Path traversal protection.
- Basic rate limiting.
- Configurable CORS.
- No sensitive data in logs.
- Security tests for authentication, authorization, validation, deletion, and
  rate limiting.

## V4: Frontend And Product UX

Goal: provide a simple professional web interface over the stable API.

- React with Vite and TypeScript.
- Responsive UI.
- Registration and login screens.
- Dashboard.
- CSV upload.
- Task creation.
- Task list.
- Task detail.
- Result download.
- Clear error display.
- Reasonable status polling.
- Visible statuses:
  - `PENDING`
  - `PROCESSING`
  - `COMPLETED`
  - `FAILED`
  - `RETRYING`
  - `CANCELLED`
- Frontend tests for forms, authentication, dashboard, and upload-to-result
  workflow.
- Add frontend to Docker Compose.

## CI/CD

Goal: make quality checks repeatable on every push and pull request.

- GitHub Actions workflow.
- Maven compile and tests.
- Frontend build and tests.
- Integration tests.
- Dependency vulnerability analysis.
- Docker image builds.
- Publish images only on the main branch.
- Maven and npm caches.
- Test reports and coverage.
- README badge after workflow exists.
- Document required CI secrets.

## Observability

Goal: make runtime behavior visible and diagnosable.

- Spring Boot Actuator.
- Micrometer.
- Prometheus metrics endpoint.
- JSON structured logs.
- `correlationId` propagation from API to worker.
- Business metrics:
  - total tasks;
  - tasks by status;
  - successes;
  - failures;
  - retries;
  - average duration;
  - RabbitMQ queue size;
  - average file size.
- System metrics:
  - CPU;
  - memory;
  - active workers;
  - restarts;
  - API response time.
- Versioned Grafana dashboard.
- Alerts for high failure rate, saturated queue, missing workers, and slow
  processing.

## Kubernetes

Goal: prepare local Kubernetes deployment after the Docker version is stable.

- Namespace.
- ConfigMaps.
- Fake-value Secrets only.
- API Deployment and Service.
- Worker Deployment.
- Frontend Deployment and Service.
- PostgreSQL demonstration deployment.
- RabbitMQ.
- MinIO.
- Prometheus.
- Grafana.
- Ingress.
- PersistentVolumeClaims.
- Readiness and liveness probes.
- Resource requests and limits.
- HorizontalPodAutoscaler for workers.
- Local validation with kind or minikube.

## Extensions

- Helm chart.
- Terraform for cloud infrastructure.
- Additional file processors.
- Multi-tenant organization model.
- Admin dashboard.
- Webhooks on task completion.
- Advanced CSV profiling.
- Object lifecycle policies.
- Production managed services for PostgreSQL, RabbitMQ, and object storage.

## Final Portfolio Preparation

- Secret scan.
- Remove unused code.
- Verify tests, Docker Compose, Kubernetes manifests, dependencies, and docs.
- Professional README.
- ADRs for important decisions.
- `CONTRIBUTING.md`.
- License.
- Release notes.
- CV description.
- LinkedIn description.
- Two-minute demo script.
- Interview question and answer set.
