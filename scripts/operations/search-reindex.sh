#!/usr/bin/env bash
# Rebuild the conversation search index (Meilisearch, #125) of an EF AI Workspace stack from MongoDB.
#
# Usage: scripts/operations/search-reindex.sh <mongodb-container> <librechat-container>
#
# LibreChat v0.8.8 records "indexed" per conversation and message in MongoDB (_meiliIndex), not in Meilisearch. An
# empty index (new or lost Meilisearch volume) is rebuilt on LibreChat's next start on its own; but when the index
# exists and lacks chats that MongoDB marks as indexed (a database restore), they stay unsearchable. This script clears
# those marks (as upstream's batchResetMeiliFlags does, api/db/utils.js) and restarts LibreChat, whose start-up sync then
# indexes everything again (tests/integration M56). Safe to repeat; chats are not changed. restore.sh runs it.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <mongodb-container> <librechat-container>" >&2
  exit 2
fi
mongo_ctr="$1"
app_ctr="$2"

echo "Marking conversations and messages for re-indexing in ${mongo_ctr} ..."
docker exec "$mongo_ctr" sh -c 'mongosh --quiet --norc "mongodb://127.0.0.1:27017/${MONGO_APP_DATABASE:-LibreChat}" \
  -u "$MONGO_APP_USERNAME" -p "$MONGO_APP_PASSWORD" --authenticationDatabase "${MONGO_APP_DATABASE:-LibreChat}" \
  --eval "$0"' 'for (const c of ["conversations", "messages"]) {
    const r = db.getCollection(c).updateMany({ _meiliIndex: { $ne: false } }, { $set: { _meiliIndex: false } });
    print(c + ": " + r.modifiedCount);
  }'

echo "Restarting ${app_ctr}: its start-up sync re-indexes everything ..."
docker restart "$app_ctr" >/dev/null
echo "Done. Search returns old chats again once the sync has finished (LibreChat log: [indexSync])."
