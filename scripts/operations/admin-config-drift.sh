#!/usr/bin/env bash
# Admin Panel drift check (ADR-0016, #141): platform settings live in Git, never only in MongoDB.
#
# Usage: scripts/operations/admin-config-drift.sh <mongodb-container>              (Compose / emulation)
#        scripts/operations/admin-config-drift.sh --railway [--environment dev]    (Railway, via `railway ssh`)
#
# The Admin Panel can store configuration overrides per role or group (collection `configs`) and create custom roles
# whose permissions LibreChat never resets (librechat.yaml `interface` re-seeds only USER and ADMIN on every start).
# Owner decision (#141): the panel manages users, groups, custom roles and grants only; settings change through a PR on
# infrastructure/common/librechat.yaml. This check fails (exit 1) when either rule is broken:
#   1. any document exists in `configs` (an override shadows librechat.yaml for some users);
#   2. a custom role allows an action that the USER role (seeded from librechat.yaml and roles-policy.js) does not,
#      e.g. MCP servers, code execution, web search or public sharing that ai-safe-defaults closes.
# Read-only: it never changes data. Remove a finding in the panel (Configuration / Access), then re-run.
set -euo pipefail

usage() { sed -n '4,5p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
mode=""; ctr=""; env_args=()
case "${1:-}" in
  --railway) mode=railway; shift
    while [[ $# -gt 0 ]]; do
      case "$1" in --environment) [[ -n "${2:-}" ]] || usage; env_args=(--environment "$2"); shift 2 ;; *) usage ;; esac
    done ;;
  ""|-*) usage ;;
  *) mode=docker; ctr="$1"; [[ $# -eq 1 ]] || usage ;;
esac

# Runs inside the mongodb container as the least-privilege application user (its credentials are that container's env).
# shellcheck disable=SC2016 # $MONGO_* expand inside the container, not here
shell='mongosh --quiet --norc "mongodb://127.0.0.1:27017/${MONGO_APP_DATABASE:-LibreChat}" -u "$MONGO_APP_USERNAME" \
  -p "$MONGO_APP_PASSWORD" --authenticationDatabase "${MONGO_APP_DATABASE:-LibreChat}" --eval "$0"'
js='const issues = [];
const n = db.configs.countDocuments({});
if (n) issues.push("configs: " + n + " override document(s); settings belong in librechat.yaml");
const base = (db.roles.findOne({ name: "USER" }) || {}).permissions || {};
db.roles.find({ name: { $nin: ["ADMIN", "USER"] } }).forEach((r) => {
  for (const [type, actions] of Object.entries(r.permissions || {})) {
    for (const [action, on] of Object.entries(actions || {})) {
      if (on === true && (base[type] || {})[action] !== true) issues.push("role " + r.name + ": " + type + "." + action);
    }
  }
});
print(JSON.stringify(issues));'

if [[ "$mode" == docker ]]; then
  out="$(docker exec "$ctr" sh -c "$shell" "$js")"
else
  command -v "${RAILWAY_BIN:-railway}" >/dev/null || { echo "Railway CLI not found (https://docs.railway.com/cli)" >&2; exit 1; }
  out="$("${RAILWAY_BIN:-railway}" ssh --service mongodb "${env_args[@]}" -- sh -c "$shell" "$js")"
fi

python3 -c '
import json, sys
issues = json.loads(sys.argv[1].strip().splitlines()[-1])
if not issues:
    print("PASS  no admin-panel drift: no configuration overrides, no custom role above the USER baseline")
    sys.exit(0)
print("FAIL  admin-panel drift (ADR-0016): fix in the panel, or propose the setting as a PR on librechat.yaml")
for issue in issues:
    print("  - " + issue)
sys.exit(1)' "$out"
