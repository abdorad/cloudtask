#!/usr/bin/env sh
set -eu

if [ -z "${CLOUDTASK_DATABASE_URL:-}" ]; then
    echo >&2 "CLOUDTASK_DATABASE_URL is required for Alembic migrations. Configure the dedicated migration connection before starting CloudTask."
    exit 2
fi

echo "Running Alembic migrations with the dedicated migration database connection."
if ! alembic upgrade head; then
    echo >&2 "Alembic migration failed. Check that the PostgreSQL data volume was initialized with the CloudTask migration role, or follow the non-destructive recovery procedure in README.md."
    exit 1
fi
