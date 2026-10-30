#!/usr/bin/env bash
# Vulnerability scan (Trivy) of every image pinned in infrastructure/compose/*.yaml — the same digests the Railway
# Dockerfiles build FROM. REPORT-ONLY by default: the acceptance policy (which severities block a release, how
# exceptions are recorded) is an open owner decision (docs/security/security-baseline.md SC-18); this script never
# invents a threshold. Pass --fail-on CRITICAL (or HIGH,CRITICAL) to enforce one explicitly.
#
# --include-railway also builds infrastructure/railway/*.Dockerfile locally and scans the derived images as built.
# Register of findings and their disposition: docs/security/vulnerability-register.md.
#
# Usage: TRIVY=/path/to/trivy scripts/validate/image-scan.sh [--fail-on SEVERITIES] [--include-railway] [output-dir]
# Pulls the images (~6 GB). Results are a point-in-time snapshot of the vulnerability database.
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
trivy="${TRIVY:-trivy}"
fail_on=""; railway=false
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --fail-on) fail_on="$2"; shift 2 ;;
    --include-railway) railway=true; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
out="${1:-$(mktemp -d)}"
mkdir -p "$out"
command -v "$trivy" >/dev/null || { echo "trivy not found (set TRIVY=...)" >&2; exit 2; }

mapfile -t images < <(grep -hE '^\s+image:\s+\S+@sha256:' "$root"/infrastructure/compose/compose*.yaml | awk '{print $2}' | sort -u)
if $railway; then
  for f in librechat mongodb meilisearch admin-panel; do
    docker build -q -f "$root/infrastructure/railway/$f.Dockerfile" -t "efaiw-railway-$f:scan" "$root" >/dev/null
    images+=("efaiw-railway-$f:scan")
  done
fi
echo "trivy $("$trivy" --version | head -1 | awk '{print $2}')  images: ${#images[@]}  output: $out"
echo
echo "| Image | CRITICAL | HIGH | fixable (C/H) |"
echo "|---|---|---|---|"
status=0
for image in "${images[@]}"; do
  report="$out/$(echo "${image%%@*}" | tr '/:' '__').json"
  "$trivy" image --quiet --scanners vuln --severity HIGH,CRITICAL --format json -o "$report" "$image"
  python3 - "$image" "$report" <<'EOF'
import json, sys
image, report = sys.argv[1], sys.argv[2]
count = {"CRITICAL": [0, 0], "HIGH": [0, 0]}
for result in json.load(open(report)).get("Results", []):
    for v in result.get("Vulnerabilities") or []:
        count[v["Severity"]][0] += 1
        count[v["Severity"]][1] += bool(v.get("FixedVersion"))
c, h = count["CRITICAL"], count["HIGH"]
print(f"| `{image.split('@')[0]}` | {c[0]} | {h[0]} | {c[1]}/{h[1]} |")
EOF
  if [[ -n "$fail_on" ]]; then
    "$trivy" image --quiet --scanners vuln --severity "$fail_on" --exit-code 1 --format table "$image" >/dev/null || status=1
  fi
done
echo
echo "Detailed JSON reports: $out"
exit "$status"
