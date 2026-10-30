#!/bin/sh
# Railway start guard for the LibreChat Admin Panel (infrastructure/railway/admin-panel.Dockerfile, ADR-0016).
# POSIX sh (busybox). Runs as the upstream `bun` user; the panel keeps no data (sessions live in an encrypted cookie).
#   1. Refuses to start while a required variable is missing or SESSION_SECRET is shorter than 32 characters.
#   2. Refuses to start while the LibreChat URLs render as a bare scheme (no domain resolved yet).
set -eu

missing=""
for name in SESSION_SECRET API_SERVER_URL VITE_API_BASE_URL; do
  eval "value=\${$name:-}"
  case "$value" in
    ""|http://|https://|http://:*) missing="$missing $name" ;;
  esac
done
if [ -n "$missing" ]; then
  echo "efaiw: refusing to start, required variable(s) not set:$missing (docs/operations/railway.md)" >&2
  exit 64
fi
if [ "${#SESSION_SECRET}" -lt 32 ]; then
  echo "efaiw: refusing to start, SESSION_SECRET must be at least 32 characters (scripts/setup/railway-secrets.sh)" >&2
  exit 64
fi

exec "$@"
