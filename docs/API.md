# CloudTask API Plan

## Status

This is a planning document for Phase 0. The API is not implemented yet.

## MVP Routes

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/files` | Upload a CSV file and return file metadata. |
| `POST` | `/api/tasks` | Create an asynchronous task for an uploaded file. |
| `GET` | `/api/tasks/{id}` | Get task details and current status. |
| `GET` | `/api/tasks` | List tasks. |
| `GET` | `/api/tasks/{id}/result` | Download or retrieve the generated result. |
| `GET` | `/actuator/health` | Health endpoint provided by Spring Boot Actuator. |

## Later Routes

| Method | Route | Phase | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register` | V3 | Register a user. |
| `POST` | `/api/auth/login` | V3 | Authenticate and receive a JWT. |
| `POST` | `/api/auth/refresh` | V3 | Refresh or renew access. |
| `DELETE` | `/api/tasks/{id}` | V3 | Delete a task and its files securely. |
| `POST` | `/api/tasks/{id}/cancel` | V3+ | Request task cancellation. |

## Public Identifiers

All externally exposed resources must use UUID identifiers:

- task ID;
- file ID;
- user ID once authentication exists.

## Planned Request Examples

### Upload CSV

```http
POST /api/files
Content-Type: multipart/form-data
```

Form field:

- `file`: CSV file.

### Create Task

```json
{
  "fileId": "00000000-0000-0000-0000-000000000000",
  "processingType": "CSV_ANALYSIS"
}
```

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
  "path": "/api/files",
  "correlationId": "00000000-0000-0000-0000-000000000000"
}
```

## OpenAPI

The backend must expose OpenAPI/Swagger documentation when the API module is
implemented. The exact route, for example `/swagger-ui.html` or
`/swagger-ui/index.html`, will depend on the selected Springdoc version.
