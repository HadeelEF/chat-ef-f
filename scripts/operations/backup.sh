#!/usr/bin/env bash
# Back up the LibreChat MongoDB database and file volumes of an EF AI Workspace stack.
#
# Usage: scripts/operations/backup.sh <mongodb-container> <librechat-container> <output-dir>
#   Find container names with: docker ps --format '{{.Names}}' | grep -E 'mongodb|librechat'
#
# Produces <output-dir>/<UTC timestamp>/{mongodb.archive.gz,files.tar.gz,SHA256SUMS}.
# files.tar.gz covers every persistent LibreChat path except logs: /app/uploads, /app/client/public/images and
# /app/data (violation/ban records and agent-plugin data). /app/logs is excluded on purpose.
# For the Docker Compose stacks (Windows WSL2 local, Ubuntu on-prem). Railway uses volume backups instead
# (docs/operations/railway.md).
# Database credentials are read inside the container from its own environment; none are passed on the command line.
# Store backups only on approved, encrypted storage (docs/operations/runbook.md). Never commit them.
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <mongodb-container> <librechat-container> <output-dir>" >&2
  exit 2
fi
mongo_ctr="$1"
app_ctr="$2"
out="$3/$(date -u +%Y%m%dT%H%M%SZ)"
umask 077
mkdir -p "$out"

echo "Backing up MongoDB database from ${mongo_ctr} ..."
docker exec "$mongo_ctr" sh -c \
  'mongodump --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" \
     --authenticationDatabase admin --db "${MONGO_APP_DATABASE:-LibreChat}" --archive --gzip' \
  > "$out/mongodb.archive.gz"

echo "Backing up file volumes (uploads, images, data) from ${app_ctr} ..."
docker exec "$app_ctr" tar -czf - -C /app uploads client/public/images data > "$out/files.tar.gz"

(cd "$out" && sha256sum mongodb.archive.gz files.tar.gz > SHA256SUMS)
echo "Backup written to $out"
ls -l "$out"
