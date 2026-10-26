# CloudTask Specification

## Purpose

CloudTask accepts CSV files and performs asynchronous data profiling. It demonstrates a durable processing pipeline: upload validation, database-backed task state, queue-based work delivery, isolated worker execution, S3-compatible file storage, and a browser interface for tracking reports.

## User workflow

1. The user signs in to the React dashboard with the deployment-provisioned operator account.
2. The user selects a `.csv` file and submits it as `CSV_ANALYSIS`.
3. The API checks the file extension, configured size limit, UTF-8 header, and unique non-empty header columns.
4. The API stores the input using a generated UUID object key and atomically writes a `PENDING` task, its owner, and a durable outbox entry to PostgreSQL.
5. The worker changes the task to `PROCESSING`, reads the CSV from MinIO, creates a report, stores it, then marks the task `COMPLETED`.
6. The dashboard polls task state and lets the user download the completed JSON report.

## Supported task lifecycle

| Status | Meaning |
| --- | --- |
| `PENDING` | The task was accepted or is waiting for a retry. |
| `PROCESSING` | A worker is producing the report. |
| `COMPLETED` | The report is stored and can be downloaded. |
| `FAILED` | The CSV is invalid or all configured attempts failed. |

`RETRYING` and `CANCELLED` from the previous Java-era plan are not part of the current public lifecycle. A temporary retry is represented by `PENDING` plus `attemptCount`; task cancellation is intentionally out of scope until the queue and task-ownership semantics are expanded.

## CSV report contract

The worker generates JSON with:

- `taskId` and `generatedAt` for traceability;
- `rowCount` excluding the header;
- `columns` in input order;
- `estimatedTypes` with `integer`, `number`, `string`, or `unknown` per column;
- `missingValues` count per column;
- `numericStatistics` for wholly numeric columns: `count`, `min`, `max`, and `mean`.

The API performs a lightweight upload check. The worker completes validation of every row because that work must not extend the HTTP request lifetime. A malformed later row therefore creates a `FAILED` task with a safe user-facing reason.

## Functional scope

Included:

- CSV upload and status/result API.
- React dashboard and periodic status refresh.
- PostgreSQL persistence and Alembic migration.
- Separate bootstrap, migration-owner, and runtime PostgreSQL identities for local first-run setup. Existing local volumes whose `.env` omits the dedicated-role variables keep using their established PostgreSQL identity until explicitly migrated.
- RabbitMQ durable delivery, retry delay, and dead-letter handling.
- MinIO-compatible input and result storage.
- Bounded S3 client retries and readiness checks for PostgreSQL, RabbitMQ, and the application bucket.
- Prometheus metrics and a small Grafana dashboard.
- Docker Compose and Kubernetes app manifests.

Excluded:

- Public self-registration and multi-tenant organizations.
- Task cancellation.
- Other file types or arbitrary data transformations.
- Large-file streaming analytics, scheduled cleanup, backup automation, TLS, and production alerting.

## Safety and validation requirements

- `CLOUDTASK_UPLOAD_MAX_BYTES` enforces an upload limit; its Compose default is 20 MiB.
- Object keys are generated as `inputs/<uuid>.csv` and `reports/<uuid>.json`.
- User filenames are never used as local paths or S3 keys.
- Input must have a `.csv` extension and a readable UTF-8 header with non-empty, unique columns.
- API errors share a timestamp, status, message, request path, and correlation ID. Internal stack traces and infrastructure details are not returned.
- Configuration uses `CLOUDTASK_*` variables only. Credentials belong in an ignored `.env` or a Kubernetes Secret.
- JWT authentication is mandatory for tasks and reports; task ownership is enforced in every task query.

## Success criteria

The implementation is functionally complete when a configured local Compose deployment can accept a valid CSV, produce a persisted task, update its status through the defined lifecycle, and return a stored report through both the API and React interface. Automated tests document the expected behavior, but their execution is a separate manual verification step.
