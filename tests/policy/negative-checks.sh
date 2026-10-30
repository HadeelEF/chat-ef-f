#!/usr/bin/env bash
# Negative policy tests: each case weakens ONE control in a throwaway copy of the working tree and requires the policy
# checker to FAIL with the expected message. Proves that compose_checks.py and railway_checks.py reject, among others,
# Railway deployment sources other than this repository's main without Wait for CI (ADR-0010), missing watch paths, drift from the approved D3 targets, public
# database or search-index exposure, an Admin Panel outside its isolation (ADR-0016) and secrets in Git. Nothing is deployed; the repository itself is never modified.
#
# Usage: tests/policy/negative-checks.sh [results-file]
# Needs what the checkers need: python3 with scripts/validate/requirements.txt, docker compose, Node.js >= 22.6 and
# `npm ci --prefix .railway`. Exit 0 = every weakened configuration was rejected.
set -uo pipefail

root="$(git rev-parse --show-toplevel)"
results="${1:-/dev/null}"
source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh" # log, failures/total, summary (case_ below logs its own PASS/FAIL)
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
[[ -d "$root/.railway/node_modules/railway" ]] || { echo "run: npm ci --prefix .railway" >&2; exit 1; }

# <id> <checker: railway|compose> <file> <expected message> <python replacement: old -> new>
case_() {
  local id="$1" checker="$2" file="$3" expected="$4" old="$5" new="$6" copy="$work/$1" out
  total=$((total + 1))
  mkdir -p "$copy"
  (cd "$root" && git ls-files -z --cached --others --exclude-standard | xargs -0 cp -P --parents -t "$copy")
  ln -s "$root/.railway/node_modules" "$copy/.railway/node_modules"
  if ! python3 - "$copy/$file" "$old" "$new" <<'EOF'
import pathlib, sys
path, old, new = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3].encode().decode("unicode_escape")
text = path.read_text() if path.exists() else ""
if old == "<create>":
    path.write_text(new); sys.exit(0)
if text.count(old) != 1:
    sys.exit(f"anchor not found exactly once in {path.name}: {old!r}")
path.write_text(text.replace(old, new))
EOF
  then log "FAIL  $id  test anchor drifted (update this test)"; failures=$((failures + 1)); return; fi
  git -C "$copy" init --quiet && git -C "$copy" add -A
  out="$(cd "$copy" && python3 "scripts/validate/${checker}_checks.py" 2>&1)" && {
    log "FAIL  $id  weakened config ACCEPTED by ${checker}_checks.py"; failures=$((failures + 1)); return; }
  if grep -qF -- "$expected" <<<"$out"; then log "PASS  $id  rejected: $expected"
  else log "FAIL  $id  rejected for another reason :: ${out:0:300}"; failures=$((failures + 1)); fi
  rm -rf "$copy"
}

log "# Negative policy tests  commit=$(git -C "$root" rev-parse --short=12 HEAD)  date=$(date -u +%FT%TZ)"
ts=.railway/railway.ts
# Railway: deployment source (autodeploy from main only, ADR-0010)
case_ N01 railway "$ts" "mongodb: deployment source must be exactly" \
  'const fromMain = () => github(REPO, { branch: "main", checkSuites: false });' \
  'const fromMain = () => github(REPO, { branch: "dev", checkSuites: false });'
case_ N02 railway "$ts" "librechat: deployment source must be exactly" \
  'const fromMain = () => github(REPO, { branch: "main", checkSuites: false });' \
  'const fromMain = () => github(REPO, { branch: "main", checkSuites: true });'
case_ N03 railway "$ts" "mongodb: deployment source must be exactly" \
  'const fromMain = () => github(REPO, { branch: "main", checkSuites: false });' \
  'const fromMain = () => ({ type: "image" as const, image: "mongo:8" });'
case_ N17 railway "$ts" "librechat: watch paths must be exactly" \
  '"/infrastructure/common/librechat.yaml",' '"/infrastructure/common/README.md",'
case_ N20 railway infrastructure/railway/librechat.Dockerfile "must be named (AS ...) and pinned by version and digest" \
  'FROM node:24.16.0-alpine@sha256:21f403ab171f2dc89bad4dd69d7721bfd15f084ccb46cdd225f31f2bc59b5c9a AS client' \
  'FROM node:24-alpine AS client'
# Railway: approved D3 targets
case_ N04 railway "$ts" "must run in the approved region" \
  'const REGION = "europe-west4-drams3a";' 'const REGION = "us-west2";'
case_ N05 railway "$ts" "sizeMB must be the approved 5000" \
  'const VOLUME_SIZE_MB = 5_000;' 'const VOLUME_SIZE_MB = 50_000;'
case_ N06 railway "$ts" "librechat: resource caps must be the approved" \
  'cpu: 2, memoryBytes: 2_000_000_000' 'cpu: 8, memoryBytes: 8_000_000_000'
case_ N07 railway "$ts" "exactly one replica" \
  'replicas: { [REGION]: 1 },
    deploy: {
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
      // Approved cap (#16 D3): 2 vCPU' 'replicas: { [REGION]: 2 },
    deploy: {
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
      // Approved cap (#16 D3): 2 vCPU'
# Railway: exposure and secrets
case_ N08 railway "$ts" "mongodb: TCP proxies are not allowed" \
  'volumeMounts: { "/data/db": mongodbData },' \
  'volumeMounts: { "/data/db": mongodbData },\n    tcp: [27017],'
case_ N09 railway "$ts" "librechat: no public Railway domain in IaC" \
  'volumeMounts: { "/app/storage": librechatStorage },' \
  'volumeMounts: { "/app/storage": librechatStorage },\n    networking: { serviceDomains: { librechat: { port: 3080 } } },'
case_ N10 railway "$ts" "mongodb: custom domains are an owner decision" \
  'volumeMounts: { "/data/db": mongodbData },' \
  'volumeMounts: { "/data/db": mongodbData },\n    domains: ["db.example.invalid"],'
case_ N11 railway "$ts" "librechat.JWT_SECRET: secrets must be declared as preserve()" \
  'JWT_SECRET: preserve(),' 'JWT_SECRET: "synthetic-literal-value",'
case_ N19 railway "$ts" "librechat.QWEN_API_KEY: secrets must be declared as preserve()" \
  'QWEN_API_KEY: preserve(),' 'QWEN_API_KEY: "sk-synthetic-literal-value",'
case_ N12 railway "$ts" "differs from infrastructure/common/librechat.env" \
  'ALLOW_REGISTRATION: "false",' 'ALLOW_REGISTRATION: "true",'
case_ N13 railway railway.json "Config as Code is deprecated" '<create>' '{"deploy": {}}'
# Conversation search (#125, ADR-0014): Meilisearch stays private and keyed
case_ N24 railway "$ts" "librechat.MEILI_MASTER_KEY must be exactly" \
  'MEILI_MASTER_KEY: ref("meilisearch", "MEILI_MASTER_KEY"),' 'MEILI_MASTER_KEY: "synthetic-literal-value",'
case_ N25 railway "$ts" "meilisearch: TCP proxies are not allowed" \
  'volumeMounts: { "/meili_data": meilisearchData },' \
  'volumeMounts: { "/meili_data": meilisearchData },\n    tcp: [7700],'
# Compose (Windows/Ubuntu)
case_ N14 compose infrastructure/common/librechat.env "ALLOW_REGISTRATION must be 'false'" \
  'ALLOW_REGISTRATION=false' 'ALLOW_REGISTRATION=true'
case_ N15 compose infrastructure/compose/compose.local.yaml "must bind 127.0.0.1 only" \
  '"127.0.0.1:${LOCAL_HTTP_PORT:-3080}:3080"' '"${LOCAL_HTTP_PORT:-3080}:3080"'
case_ N16 compose infrastructure/compose/compose.yaml "mongodb: must run with --auth" \
  '["mongod", "--auth"]' '["mongod"]'
case_ N18 compose infrastructure/common/librechat.env "HELP_AND_FAQ_URL looks environment-specific or secret" \
  'HELP_AND_FAQ_URL=/assets/ef-help.html' 'HELP_AND_FAQ_URL=https://help.example.invalid'
case_ N21 compose infrastructure/compose/compose.yaml "meilisearch: compose.yaml must not publish ports" \
  '      - meilisearch-data:/meili_data' '      - meilisearch-data:/meili_data\n    ports:\n      - "7700:7700"'
case_ N22 compose infrastructure/compose/compose.yaml "meilisearch: must be attached to internal networks only" \
  '      - backend
    healthcheck:
      test: ["CMD", "wget"' '      - backend\n      - frontend\n    healthcheck:\n      test: ["CMD", "wget"'
case_ N23 compose infrastructure/compose/compose.yaml "meilisearch: needs MEILI_ENV=production" \
  'MEILI_ENV: production' 'MEILI_ENV: development'
# Admin Panel (ADR-0016, #141): secret, isolation, exit guard, caps
case_ N26 railway "$ts" "admin-panel.SESSION_SECRET: secrets must be declared as preserve()" \
  '      SESSION_SECRET: preserve(),' '      SESSION_SECRET: "synthetic-literal-session-secret",'
case_ N27 railway "$ts" "admin-panel: resource caps must be the approved" \
  'memoryBytes: 512_000_000' 'memoryBytes: 2_000_000_000'
case_ N28 railway "$ts" "admin-panel.API_SERVER_URL must be exactly" \
  'API_SERVER_URL: "http://" + ref("librechat", "RAILWAY_PRIVATE_DOMAIN") + ":3080",' \
  'API_SERVER_URL: "https://" + ref("librechat", "RAILWAY_PUBLIC_DOMAIN"),'
case_ N29 railway infrastructure/railway/admin-panel.Dockerfile "the ADR-0016 exit guard on the base image's react-start version is missing" \
  'want @tanstack/react-start "$(bun' 'echo skipped "$(bun'
case_ N30 railway infrastructure/railway/admin-panel.Dockerfile "the panel must run as the upstream bun user" \
  'USER bun
' 'USER root
'
case_ N31 compose infrastructure/compose/compose.yaml "admin-panel: must be attached to the frontend network only" \
  '      - frontend
    tmpfs:' '      - frontend\n      - backend\n    tmpfs:'
case_ N32 compose infrastructure/compose/compose.yaml "admin-panel: SESSION_COOKIE_SECURE must be true" \
  'SESSION_COOKIE_SECURE: "true"' 'SESSION_COOKIE_SECURE: "false"'
case_ N33 compose infrastructure/compose/compose.local.yaml "must bind 127.0.0.1 only" \
  '"127.0.0.1:${LOCAL_ADMIN_PORT:-3000}:3000"' '"${LOCAL_ADMIN_PORT:-3000}:3000"'

summary "weakened configurations rejected"
[[ $failures -eq 0 ]]
