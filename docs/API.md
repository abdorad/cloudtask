# CloudTask API

## Status

The API contract is not finalized yet.

## Planned Resources

### Tasks

- `POST /tasks`: create a task.
- `GET /tasks`: list tasks.
- `GET /tasks/{id}`: get task details.
- `POST /tasks/{id}/cancel`: request task cancellation.

### Health

- `GET /health`: service health check.
- `GET /ready`: readiness check.

## Task Lifecycle

```text
created -> queued -> running -> succeeded
                         \-> failed
                         \-> canceled
```

## Error Format

To be defined.
