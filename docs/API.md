# CloudTask API Plan

## Status

This is a planning document for Phase 0. The API is not implemented yet.

## MVP Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/tasks` | Upload a CSV file and create an asynchronous task. |
| `GET` | `/api/v1/tasks/{id}` | Get task details and current status. |
| `GET` | `/api/v1/tasks` | List tasks. |
| `GET` | `/api/v1/tasks/{id}/result` | Download the generated JSON report. |
| `DELETE` | `/api/v1/tasks/{id}` | Request cancellation when the task has not completed. |
| `GET` | `/actuator/health` | Health endpoint provided by Spring Boot Actuator. |

## Later Routes

| Method | Route | Phase | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Phase 3 | Register a user. |
| `POST` | `/api/v1/auth/login` | Phase 3 | Authenticate and receive a JWT. |
| `POST` | `/api/v1/auth/refresh` | Phase 3 | Refresh or renew access. |

## Public Identifiers

All externally exposed resources must use UUID identifiers:

- task ID;
- file ID;
- user ID once authentication exists.

## Planned Request Examples

### Upload CSV And Create Task

```http
POST /api/v1/tasks
Content-Type: multipart/form-data
```

Form field:

- `file`: CSV file.
- `processingType`: `CSV_ANALYSIS`.

### Task Response

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "status": "PENDING",
  "processingType": "CSV_ANALYSIS",
  "createdAt": "2026-08-04T18:00:00Z",
  "updatedAt": "2026-08-04T18:00:00Z",
  "error": null,
  "resultAvailable": false
}
```

## Task Status Values

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`
- `RETRYING`
- `CANCELLED`

## Error Response Shape

The implementation should use one central error format:

```json
{
  "timestamp": "2026-08-04T18:00:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "CSV file is required",
  "path": "/api/v1/tasks",
  "correlationId": "00000000-0000-0000-0000-000000000000"
}
```

## OpenAPI

The backend must expose OpenAPI/Swagger documentation when the API module is
implemented. The exact route, for example `/swagger-ui.html` or
`/swagger-ui/index.html`, will depend on the selected Springdoc version.
