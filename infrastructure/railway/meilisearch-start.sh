#!/bin/sh
# Railway start guard for Meilisearch (infrastructure/railway/meilisearch.Dockerfile).
# Without MEILI_MASTER_KEY there is nothing to protect the index of chat text with: refuse to start instead.
# (Production mode would also refuse, but only after creating its database on the volume.)
set -eu

if [ -z "${MEILI_MASTER_KEY:-}" ]; then
  echo "efaiw: refusing to start, required variable(s) not set: MEILI_MASTER_KEY (docs/operations/railway.md)" >&2
  exit 64
fi

exec tini -- "$@"
