#!/usr/bin/env bash
# Shared helpers for the bash test suites (tests/smoke/*.sh, tests/policy/*.sh): PASS/FAIL logging and counting.
# Source it after setting `results` (the optional results file; default /dev/null):
#   source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh"
# It sets no trap and never exits: every suite keeps its own cleanup and exit code.
results="${results:-/dev/null}"
failures=0; total=0

log() { echo "$*" | tee -a "$results"; }

check() { # <id> <description> <command...>  — non-zero exit = FAIL; the first 300 characters of output are kept
  local id="$1" desc="$2"; shift 2; total=$((total + 1))
  if out="$("$@" 2>&1)"; then log "PASS  $id  $desc"; else log "FAIL  $id  $desc :: ${out:0:300}"; failures=$((failures + 1)); fi
}

summary() { log "# result: $((total - failures))/$total ${1:-passed}"; } # <suffix> after "N/M"
