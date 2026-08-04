# CloudTask

Private repository for CloudTask.

CloudTask is planned as a cloud task orchestration platform with a backend API,
background workers, a frontend application, and infrastructure definitions.

## Initial Layout

```text
cloudtask/
├── AGENTS.md
├── README.md
├── pom.xml
├── docs/
│   ├── SPEC.md
│   ├── ARCHITECTURE.md
│   └── API.md
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
- [API](docs/API.md)

## Development

The repository currently contains the initial skeleton only.

```powershell
mvn validate
```

## Repository Status

- Visibility: private by default when kept local.
- Remote hosting: not configured yet.
