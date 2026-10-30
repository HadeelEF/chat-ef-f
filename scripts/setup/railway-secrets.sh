#!/usr/bin/env bash
# Set the Railway secrets declared with preserve() in .railway/railway.ts — once per Railway environment — and keep an
# owner-held, ENCRYPTED recovery copy so the same keys can be restored later (volume backups do not contain variables).
#
# Usage (exactly one mode):
#   scripts/setup/railway-secrets.sh --recovery-file <path.enc>   generate fresh values, write the encrypted recovery
#                                                                   copy FIRST (verified by decryption), then set them
#   scripts/setup/railway-secrets.sh --from-recovery <path.enc>   restore the same values from a recovery copy
#                                                                   (rebuilt environment / restore rehearsal)
#   scripts/setup/railway-secrets.sh --prompt                      type each value (e.g. pre-generated in an approved
#                                                                   password manager or vault); nothing is echoed
#   scripts/setup/railway-secrets.sh --accept-no-recovery          generate values with NO recovery copy (only for a
#                                                                   throwaway synthetic demo; losing them = data loss)
#   options: --environment <name>
#
# Prerequisites: Railway CLI >= 5.42.1, `railway login`, `railway link`, services created by `railway config apply`
# (docs/operations/railway.md), and an explicit owner authorisation on Issue #15.
# Secrets never appear on a command line, in output, or in Git: values go to Railway via `railway variable set --stdin`,
# and the recovery copy is AES-256 encrypted with openssl (PBKDF2, 600000 iterations, passphrase typed at the prompt,
# or read from the file named by EFAIW_RECOVERY_PASSFILE for automation). Store the copy and its passphrase apart, in
# owner-controlled storage (password manager / approved vault) — never in this repository or in chat.
# Variables that already exist in Railway are NEVER overwritten (rotating CREDS_KEY/CREDS_IV breaks stored data).
# Regenerable: MEILI_MASTER_KEY (#125) guards a search index that is rebuilt from MongoDB, so a recovery copy made
# before it existed still restores (a fresh key is generated). So is the Admin Panel SESSION_SECRET (ADR-0016): a new
# value only ends open admin sessions.
# Deploys are skipped; redeploy mongodb and meilisearch, then librechat, then admin-panel.
set -euo pipefail

railway_bin="${RAILWAY_BIN:-railway}"   # override only for tests (tests/smoke/railway-emulation.sh)
mode=""; file=""; env_args=()
usage() { sed -n '5,16p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --recovery-file|--from-recovery) [[ -z "$mode" && -n "${2:-}" ]] || usage; mode="$1"; file="$2"; shift 2 ;;
    --prompt|--accept-no-recovery) [[ -z "$mode" ]] || usage; mode="$1"; shift ;;
    --environment) [[ -n "${2:-}" ]] || usage; env_args=(--environment "$2"); shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$mode" ]] || usage
command -v "$railway_bin" >/dev/null || { echo "Railway CLI not found (https://docs.railway.com/cli)" >&2; exit 1; }
command -v openssl >/dev/null || { echo "openssl is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

# service:KEY:validation-regex — the secrets declared with preserve() in .railway/railway.ts
specs=(
  "mongodb:MONGO_INITDB_ROOT_USERNAME:^[A-Za-z0-9]{4,64}$"
  "mongodb:MONGO_INITDB_ROOT_PASSWORD:^[A-Za-z0-9]{24,128}$"
  "mongodb:MONGO_APP_PASSWORD:^[A-Za-z0-9]{24,128}$"
  "meilisearch:MEILI_MASTER_KEY:^[0-9a-f]{64}$"
  "librechat:CREDS_KEY:^[0-9a-f]{64}$"
  "librechat:CREDS_IV:^[0-9a-f]{32}$"
  "librechat:JWT_SECRET:^[A-Za-z0-9]{32,256}$"
  "librechat:JWT_REFRESH_SECRET:^[A-Za-z0-9]{32,256}$"
  "admin-panel:SESSION_SECRET:^[0-9a-f]{64}$"
)
cipher=(openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 -salt)
pass_args=()
[[ -n "${EFAIW_RECOVERY_PASSFILE:-}" ]] && pass_args=(-pass "file:$EFAIW_RECOVERY_PASSFILE")

generate() { # <KEY>
  case "$1" in
    MONGO_INITDB_ROOT_USERNAME) echo "root$(openssl rand -hex 4)" ;;
    CREDS_KEY|JWT_SECRET|JWT_REFRESH_SECRET|MEILI_MASTER_KEY|SESSION_SECRET) openssl rand -hex 32 ;;
    CREDS_IV) openssl rand -hex 16 ;;
    *) openssl rand -hex 24 ;;
  esac
}

declare -A values
case "$mode" in
  --recovery-file|--accept-no-recovery)
    for spec in "${specs[@]}"; do key="${spec#*:}"; key="${key%%:*}"; values[$key]="$(generate "$key")"; done ;;
  --prompt)
    for spec in "${specs[@]}"; do
      key="${spec#*:}"; key="${key%%:*}"
      read -r -s -p "$key: " "values[$key]" </dev/tty; echo >&2
    done ;;
  --from-recovery)
    [[ -f "$file" ]] || { echo "recovery file not found: $file" >&2; exit 1; }
    plain="$("${cipher[@]}" -d "${pass_args[@]}" -in "$file")" || { echo "cannot decrypt $file (wrong passphrase?)" >&2; exit 1; }
    while IFS='=' read -r key value; do [[ "$key" =~ ^[A-Z_]+$ ]] && values[$key]="$value"; done <<<"$plain"
    unset plain
    for key in MEILI_MASTER_KEY SESSION_SECRET; do # regenerable: absent from copies made before #125 / ADR-0016
      [[ -n "${values[$key]:-}" ]] || values[$key]="$(generate "$key")"
    done ;;
esac

for spec in "${specs[@]}"; do # validate every value before touching Railway
  service="${spec%%:*}"; rest="${spec#*:}"; key="${rest%%:*}"; regex="${rest#*:}"
  [[ "${values[$key]:-}" =~ $regex ]] || { echo "invalid or missing value for $service.$key (expected $regex)" >&2; exit 1; }
done

if [[ "$mode" == --recovery-file ]]; then # write and verify the encrypted copy BEFORE anything reaches Railway
  [[ -e "$file" ]] && { echo "refusing to overwrite existing recovery file $file" >&2; exit 1; }
  umask 077
  for spec in "${specs[@]}"; do key="${spec#*:}"; key="${key%%:*}"; printf '%s=%s\n' "$key" "${values[$key]}"; done |
    "${cipher[@]}" -e "${pass_args[@]}" -out "$file"
  check="$("${cipher[@]}" -d "${pass_args[@]}" -in "$file" | sha256sum)"
  expected="$(for spec in "${specs[@]}"; do key="${spec#*:}"; key="${key%%:*}"; printf '%s=%s\n' "$key" "${values[$key]}"; done | sha256sum)"
  [[ "$check" == "$expected" ]] || { echo "recovery copy verification failed; nothing was set in Railway" >&2; rm -f "$file"; exit 1; }
  echo "wrote  encrypted recovery copy $file (verified). Store it and its passphrase separately, outside Git."
fi

existing_keys() { # <service> -> variable names only (values are parsed in-process and discarded)
  "$railway_bin" variable list --service "$1" "${env_args[@]}" --json |
    python3 -c 'import json, sys; print("\n".join(sorted(json.load(sys.stdin))))'
}
declare -A keys
for service in mongodb meilisearch librechat admin-panel; do keys[$service]="$(existing_keys "$service")"; done

for spec in "${specs[@]}"; do
  service="${spec%%:*}"; rest="${spec#*:}"; key="${rest%%:*}"
  if grep -qx -- "$key" <<<"${keys[$service]}"; then echo "keep   $service.$key (already set; never overwritten)"; continue; fi
  printf '%s' "${values[$key]}" | "$railway_bin" variable set "$key" --stdin --service "$service" "${env_args[@]}" --skip-deploys >/dev/null
  echo "set    $service.$key"
done

cat <<'EOF'
Done. Next (docs/operations/railway.md):
  1. Optionally seal each secret in the dashboard (Variables -> ... -> Seal); sealed values cannot be read back,
     so the encrypted recovery copy is the only way to restore the same keys.
  2. Redeploy mongodb and meilisearch, wait for both to be Active, then redeploy librechat, then admin-panel.
EOF
