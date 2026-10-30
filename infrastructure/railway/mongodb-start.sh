#!/bin/sh
# Railway start guard for MongoDB (infrastructure/railway/mongodb.Dockerfile).
# Without the root and application credentials, the official entrypoint would initialise an empty volume with no
# administrator; the init script would then never run again. Refuse to start instead, leaving the volume untouched.
set -eu

missing=""
for name in MONGO_INITDB_ROOT_USERNAME MONGO_INITDB_ROOT_PASSWORD MONGO_APP_USERNAME MONGO_APP_PASSWORD; do
  eval "value=\${$name:-}"
  [ -n "$value" ] || missing="$missing $name"
done
if [ -n "$missing" ]; then
  echo "efaiw: refusing to start, required variable(s) not set:$missing (docs/operations/railway.md)" >&2
  exit 64
fi

exec docker-entrypoint.sh "$@"
