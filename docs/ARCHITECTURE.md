# CloudTask Architecture

## Overview

CloudTask is organized around four main areas:

- Backend API in `backend/`.
- Background execution in `worker/`.
- Web application in `frontend/`.
- Deployment and observability assets in `infra/`.

## Proposed Runtime Flow

```text
client -> frontend -> backend API -> task queue -> worker -> result storage
```

## Components

### Backend

Owns API endpoints, authentication, task validation, and task persistence.

### Worker

Consumes queued tasks, executes work, records outcomes, and emits metrics.

### Frontend

Provides task creation, monitoring, and administration views.

### Infrastructure

Contains local Docker assets, Kubernetes manifests, and monitoring definitions.

## Architecture Decisions

Record decisions here as the project evolves.
