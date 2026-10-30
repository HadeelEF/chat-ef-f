#!/usr/bin/env bash
# Run every check defined in .github/workflows/ci.yml and security.yml, locally or in a cloud session.
# The heavier container workflows have their own entry points: tests/smoke/*.sh (smoke.yml) and
# scripts/validate/image-scan.sh (image-scan.yml).
# GitHub Actions is not used (#16). This script is an optional developer verification tool in development and a building
# block of the production quality gates (ADR-0011); it is NOT independent CI verification. actionlint/gitleaks versions
# and SHA-256 sums are read from the workflow files so this script cannot drift from CI.
#
# Prerequisite: validation tools on PATH, e.g.
#   python3 -m venv .venv && . .venv/bin/activate
#   python -m pip install --require-hashes -r scripts/validate/requirements.txt
# and Node.js >= 22.6 for the Railway IaC job (the pinned SDK is installed here with `npm ci --prefix .railway`).
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"
cache="${VALIDATE_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/ef-ai-workspace-validate}"
mkdir -p "$cache"

workflow_env() { # <workflow file> <env key>
  python -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))["env"][sys.argv[2]])' "$1" "$2"
}

fetch_verified() { # <name> <url> <archive> <sha256>
  if [[ ! -x "$cache/$1" ]]; then
    curl -fsSL -o "$cache/$3" "$2"
    (cd "$cache" && echo "$4  $3" | sha256sum --check --strict --quiet && tar -xzf "$3" "$1")
  fi
}

failed=()
run() { # <label> <command...>
  echo "::: $1"
  if "${@:2}"; then echo "PASS  $1"; else echo "FAIL  $1"; failed+=("$1"); fi
}

al_ver="$(workflow_env .github/workflows/ci.yml ACTIONLINT_VERSION)"
al_sha="$(workflow_env .github/workflows/ci.yml ACTIONLINT_SHA256)"
gl_ver="$(workflow_env .github/workflows/security.yml GITLEAKS_VERSION)"
gl_sha="$(workflow_env .github/workflows/security.yml GITLEAKS_SHA256)"
fetch_verified actionlint \
  "https://github.com/rhysd/actionlint/releases/download/v${al_ver}/actionlint_${al_ver}_linux_amd64.tar.gz" \
  "actionlint_${al_ver}_linux_amd64.tar.gz" "$al_sha"
fetch_verified gitleaks \
  "https://github.com/gitleaks/gitleaks/releases/download/v${gl_ver}/gitleaks_${gl_ver}_linux_x64.tar.gz" \
  "gitleaks_${gl_ver}_linux_x64.tar.gz" "$gl_sha"

echo "commit: $(git rev-parse HEAD)  python: $(python --version 2>&1)  actionlint: ${al_ver}  gitleaks: ${gl_ver}"

# ci.yml
run "repo_checks" python scripts/validate/repo_checks.py
run "compose_checks" python scripts/validate/compose_checks.py
run "railway sdk (npm ci)" npm ci --prefix .railway --ignore-scripts --no-audit --no-fund --loglevel=error
run "railway_checks" python scripts/validate/railway_checks.py
run "negative policy tests" tests/policy/negative-checks.sh
run "railway emergency deploy path" tests/smoke/railway-manual-deploy.sh
run "yamllint" yamllint --strict .
run "schema: workflows" check-jsonschema --builtin-schema vendor.github-workflows .github/workflows/*.yml
run "schema: dependabot" check-jsonschema --builtin-schema vendor.dependabot .github/dependabot.yml
run "schema: issue forms" check-jsonschema --builtin-schema vendor.github-issue-forms \
  .github/ISSUE_TEMPLATE/bug.yml .github/ISSUE_TEMPLATE/feature.yml
run "schema: issue config" check-jsonschema --builtin-schema vendor.github-issue-config .github/ISSUE_TEMPLATE/config.yml
run "actionlint" "$cache/actionlint" -color=false
# security.yml
run "gitleaks: git history" "$cache/gitleaks" git --redact --no-banner --exit-code 1 .
run "gitleaks: working tree" "$cache/gitleaks" dir --redact --no-banner --exit-code 1 .
run "zizmor" zizmor --offline .github/workflows/

if ((${#failed[@]})); then
  printf '\n%d check(s) failed: %s\n' "${#failed[@]}" "${failed[*]}"
  exit 1
fi
echo -e "\nAll CI and Security workflow checks passed (cloud-session evidence, not independent CI)."
