#!/usr/bin/env bash
# Emergency / rollback deployment of ONE reviewed commit of `main` to Railway `dev` (ADR-0008, ADR-0010).
# Normal deployments are automatic: a push to `main` that changes a service's watched image inputs redeploys it
# (.railway/railway.ts). Use this script only to redeploy an older commit or when autodeploy is unavailable. It exports
# exactly that commit with `git archive` (no untracked or ignored files such as .env) and uploads it with `railway up`.
#
# Usage: scripts/setup/railway-deploy.sh --commit <40-hex SHA on origin/main> [--environment dev]
#                                        [--service mongodb|meilisearch|librechat|admin-panel|all] [--yes]
#   --yes   skip the typed confirmation (only for an authorised, scripted run)
#
# Prerequisites: Railway CLI >= 5.42.1, `railway login` and `railway link` in this repository, services created by an
# authorised `railway config apply`, secrets set (railway-secrets.sh), and an authorisation: ADR-0009 for environment
# `dev`, an explicit owner comment on Issue #15 otherwise. No public domain is created here (SC-18 / D5 gate).
# docs/operations/railway.md §4.
set -euo pipefail

railway_bin="${RAILWAY_BIN:-railway}"   # override only for tests (tests/smoke/railway-manual-deploy.sh)
commit=""; environment="dev"; services=(mongodb meilisearch librechat admin-panel); yes=false
usage() { sed -n '7,9p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit) [[ -n "${2:-}" ]] || usage; commit="$2"; shift 2 ;;
    --environment) [[ -n "${2:-}" ]] || usage; environment="$2"; shift 2 ;;
    --service)
      case "${2:-}" in mongodb|meilisearch|librechat|admin-panel) services=("$2") ;; all) ;; *) usage ;; esac; shift 2 ;;
    --yes) yes=true; shift ;;
    *) usage ;;
  esac
done
[[ "$commit" =~ ^[0-9a-f]{40}$ ]] || { echo "--commit must be a full 40-character commit SHA" >&2; exit 2; }
command -v "$railway_bin" >/dev/null || { echo "Railway CLI not found (https://docs.railway.com/cli)" >&2; exit 1; }

root="$(git rev-parse --show-toplevel)"
cd "$root"
git fetch --quiet origin main
git cat-file -e "$commit^{commit}" 2>/dev/null || { echo "commit $commit not found" >&2; exit 1; }
git merge-base --is-ancestor "$commit" origin/main ||
  { echo "commit $commit is not on origin/main: only reviewed, merged commits are deployed" >&2; exit 1; }

echo "Deploy $commit ($(git log -1 --format=%s "$commit")) to Railway environment '$environment': ${services[*]}"
if ! $yes; then
  [[ -t 0 ]] || { echo "refusing to deploy without a terminal; pass --yes for an authorised scripted run" >&2; exit 1; }
  read -r -p "Owner authorisation for this commit is recorded on Issue #15? Type DEPLOY ${commit:0:12}: " answer
  [[ "$answer" == "DEPLOY ${commit:0:12}" ]] || { echo "not confirmed; nothing deployed" >&2; exit 1; }
fi

export_dir="$(mktemp -d)"
trap 'rm -rf "$export_dir"' EXIT
git archive "$commit" | tar -x -C "$export_dir"
for service in "${services[@]}"; do
  echo "::: railway up --service $service ($commit)"
  "$railway_bin" up "$export_dir" --path-as-root --service "$service" --environment "$environment" --ci \
    --message "efaiw ${commit:0:12} (manual, #15)"
done
echo "Uploaded. Verify in Railway: every deployment Active, librechat /health passed (railway.md §4, RW1/RW4)."
