#!/usr/bin/env sh
set -eu

invalid=0
check_pair() {
  case "$1" in
    ""|"up") ;;
    *) echo >&2 "$2 user and password must be configured together."; invalid=1 ;;
  esac
}

check_pair "${CLOUDTASK_POSTGRES_APPLICATION_ROLE_PARTS:-}" "Application database role"
check_pair "${CLOUDTASK_POSTGRES_MIGRATION_ROLE_PARTS:-}" "Migration database role"

jwt_secret=${CLOUDTASK_JWT_SECRET-}
bootstrap_email=${CLOUDTASK_BOOTSTRAP_USER_EMAIL-}
bootstrap_password=${CLOUDTASK_BOOTSTRAP_USER_PASSWORD-}

if [ "${#jwt_secret}" -lt 32 ]; then
  echo >&2 "CLOUDTASK_JWT_SECRET must be configured with at least 32 characters."
  invalid=1
fi
if [ -z "$bootstrap_email" ] || [ "${#bootstrap_password}" -lt 12 ]; then
  echo >&2 "Bootstrap operator email and a password of at least 12 characters are required."
  invalid=1
fi
exit "$invalid"
