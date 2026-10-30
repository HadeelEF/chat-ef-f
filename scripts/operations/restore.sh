#!/usr/bin/env bash
# Restore an EF AI Workspace backup produced by scripts/operations/backup.sh.
#
# Usage: scripts/operations/restore.sh <mongodb-container> <librechat-container> <backup-dir>
#
# DESTRUCTIVE: the LibreChat database is replaced (mongorestore --drop) and backed-up files overwrite existing ones.
# Take a fresh backup first. It ends by restarting the librechat container (caches and the search index are rebuilt).
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <mongodb-container> <librechat-container> <backup-dir>" >&2
  exit 2
fi
mongo_ctr="$1"
app_ctr="$2"
dir="$3"

(cd "$dir" && sha256sum --check --strict SHA256SUMS)

echo "Restoring MongoDB database into ${mongo_ctr} (drop + restore) ..."
docker exec -i "$mongo_ctr" sh -c \
  'mongorestore --quiet --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" \
     --authenticationDatabase admin --nsInclude "${MONGO_APP_DATABASE:-LibreChat}.*" --drop --archive --gzip' \
  < "$dir/mongodb.archive.gz"

echo "Restoring file volumes into ${app_ctr} ..."
docker exec -i "$app_ctr" tar -xzf - -C /app < "$dir/files.tar.gz"

# The search index is derived data (not in the backup): mark everything for re-indexing and restart LibreChat.
"$(dirname "$0")/search-reindex.sh" "$mongo_ctr" "$app_ctr"
echo "Restore complete."
