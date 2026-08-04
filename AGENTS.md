# CloudTask Agent Notes

## Project Intent

CloudTask is a private repository for a cloud task management and execution platform.
Keep changes small, documented, and aligned with the structure in this repository.

## Repository Map

- `backend/`: backend services and API implementation.
- `worker/`: background task execution and queue consumers.
- `frontend/`: user-facing web application.
- `infra/docker/`: local containers and Docker build assets.
- `infra/kubernetes/`: Kubernetes manifests and deployment overlays.
- `infra/monitoring/`: observability, dashboards, alerts, and metrics assets.
- `docs/`: product, architecture, and API documentation.

## Working Guidelines

- Update `docs/SPEC.md` when product behavior changes.
- Update `docs/ARCHITECTURE.md` when system boundaries, data flow, or infrastructure decisions change.
- Update `docs/API.md` when API contracts change.
- Prefer reproducible local commands and document them in `README.md`.
- Do not commit generated secrets, local credentials, or environment-specific files.

## Expected Commands

These commands are placeholders until concrete modules are added:

```powershell
git status
mvn validate
```
