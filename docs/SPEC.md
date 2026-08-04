# CloudTask Specification

## Purpose

CloudTask will provide a system for creating, scheduling, running, and tracking
cloud-based tasks.

## Initial Scope

- Define task creation and lifecycle states.
- Expose an API for task submission and status lookup.
- Execute background work through worker processes.
- Provide a frontend for operators and users.
- Prepare deployment and monitoring assets.

## Open Questions

- Which task queue or broker will be used?
- Which authentication model is required?
- Which cloud provider or deployment target is preferred?
- Which frontend framework will be used?

## Non-Goals For Bootstrap

- Production deployment.
- Final data model.
- Full API schema.
- Complete UI flows.
