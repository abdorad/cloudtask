# CloudTask Backlog

## Delivered implementation

- Python 3.12 FastAPI API and separate Python worker process.
- Operator authentication, owner-scoped tasks, and protected report downloads.
- Argon2 password hashes, expiring JWT bearer tokens, and deployment bootstrap account creation.
- Durable outbox reconciliation and stale-processing recovery.
- Process-local request/upload/login rate limits and normalized API metric route labels.
- PostgreSQL task persistence and first Alembic migration.
- RabbitMQ durable task delivery, TTL retry, and dead-letter queue topology.
- MinIO/S3-compatible input and report storage.
- CSV validation, profiling, task status API, and report streaming.
- React JavaScript dashboard with upload feedback, status polling, and report download.
- Docker Compose configuration for app, data services, and monitoring.
- Prometheus metrics, Grafana datasource/dashboard provisioning, and Kubernetes app manifests.
- Unit tests for validation, CSV analysis, and worker behavior; Testcontainers database integration test; React component test.

## Manual verification still required

1. Install local Python and Node dependencies.
2. Run unit, integration, and frontend tests.
3. Start Docker Compose and perform the upload-to-report walkthrough, including fresh-volume PostgreSQL role setup or existing-volume legacy-role compatibility, migration completion, API readiness, and worker metrics after queue registration.
4. Inspect retry/dead-letter behavior by temporarily making the worker's object-storage connection unavailable.
5. Validate image tags and manifests against the target Docker/Kubernetes environment before publishing.

## Next product priorities

1. Replace the process-local rate limiter with a shared edge or Redis-backed limiter before scaling the API.
2. Add password reset, account lifecycle controls, and a production identity provider if multiple operators are needed.
3. Add a distributed worker lease/heartbeat for improved multi-worker coordination.
4. Add report retention policies and scheduled cleanup for MinIO objects and old task rows.
5. Add rate limiting, content malware scanning, and more complete CSV dialect/encoding support.
6. Add pagination totals, filtering, task deletion semantics, and real-time progress delivery if the product needs them.
7. Add CI that runs the existing tests, builds images, and scans dependencies.
8. Add production backups, TLS, ingress policies, alert rules, and managed stateful services.

## Intentionally deferred

- Multi-tenant organizations and billing.
- Cancellation lifecycle and task ownership.
- Large-scale streaming analysis and multiple processing types.
- Helm charts or Terraform.
- A Kubernetes deployment for PostgreSQL, RabbitMQ, MinIO, Prometheus, and Grafana. Production deployments should choose supported operators or managed services instead.
