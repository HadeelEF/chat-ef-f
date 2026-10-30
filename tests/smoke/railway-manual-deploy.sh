#!/usr/bin/env bash
# Emergency/rollback Railway deployment path (the manual fallback kept by ADR-0010): exercises the real
# scripts/setup/railway-deploy.sh against a throwaway git remote and a stub `railway` CLI that records each
# `railway up` call and the files it would upload.
# Proves: only full SHAs already on origin/main are deployed; no unconfirmed or non-interactive run without --yes; the
# upload is exactly the committed tree (no .env, untracked or uncommitted files); mongodb and meilisearch before
# librechat; a failed upload stops the run; the temporary export is removed. Railway itself is NOT contacted (no token,
# no deployment).
#
# Usage: tests/smoke/railway-manual-deploy.sh [results-file]      Needs: git, python3. Exit 0 = no check failed.
set -uo pipefail

root="$(git rev-parse --show-toplevel)"
results="${1:-/dev/null}"
source "$(dirname "${BASH_SOURCE[0]}")/../lib.sh" # log, check, failures/total, summary
deploy="$root/scripts/setup/railway-deploy.sh"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# --- throwaway remote: main has the reviewed commit; a feature commit is not merged ---
export GIT_AUTHOR_NAME=test GIT_AUTHOR_EMAIL=test@example.invalid GIT_COMMITTER_NAME=test GIT_COMMITTER_EMAIL=test@example.invalid
git init --quiet --bare --initial-branch=main "$work/remote.git"
git clone --quiet "$work/remote.git" "$work/repo" 2>/dev/null
cd "$work/repo"
git checkout --quiet -b main
mkdir -p infrastructure/railway && echo "FROM scratch" > infrastructure/railway/librechat.Dockerfile
echo "reviewed" > app.txt && printf '.env\n*.log\n' > .gitignore
git add -A && git commit --quiet -m "reviewed change" && git push --quiet origin main 2>/dev/null
reviewed="$(git rev-parse HEAD)"
git checkout --quiet -b feature && echo "unreviewed" > app.txt && git commit --quiet -am "unmerged change"
unmerged="$(git rev-parse HEAD)"
git checkout --quiet main
echo "SYNTHETIC_SECRET=do-not-upload" > .env; echo "debug" > build.log; echo "untracked" > notes.txt
echo "uncommitted edit" > app.txt

# --- stub railway CLI: records calls and the uploaded file list; fails on demand ---
mkdir -p "$work/bin"
cat > "$work/bin/railway" <<'STUB'
#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
if args[:1] != ["up"] or "--path-as-root" not in args:
    sys.exit(f"stub: unsupported call {args}")
path, service = args[1], args[args.index("--service") + 1]
files = sorted(os.path.relpath(os.path.join(d, f), path) for d, _, fs in os.walk(path) for f in fs)
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps({"args": args, "files": files, "app": open(os.path.join(path, "app.txt")).read()}) + "\n")
if service == os.environ.get("STUB_FAIL_SERVICE"):
    sys.exit("stub: upload failed")
STUB
chmod +x "$work/bin/railway"
export RAILWAY_BIN="$work/bin/railway" STUB_LOG="$work/calls.jsonl"
calls() { python3 -c 'import json,sys; [print(eval(sys.argv[2], {}, {"c": json.loads(l)})) for l in open(sys.argv[1])]' "$STUB_LOG" "$1"; }
reset_log() { rm -f "$STUB_LOG"; touch "$STUB_LOG"; }
no_uploads() { [[ ! -s "$STUB_LOG" ]] || { echo "unexpected upload"; return 1; }; }

log "# Railway manual deploy path  commit=$(git -C "$root" rev-parse --short=12 HEAD)  date=$(date -u +%FT%TZ)"

t_short_sha() { reset_log; ! "$deploy" --commit "${reviewed:0:12}" --yes && no_uploads; }
t_unmerged() { reset_log; ! "$deploy" --commit "$unmerged" --yes && no_uploads; }
t_no_tty() { reset_log; ! "$deploy" --commit "$reviewed" </dev/null && no_uploads; }
t_deploy() {
  reset_log; "$deploy" --commit "$reviewed" --yes >/dev/null || return 1
  [[ "$(calls 'c["args"][c["args"].index("--service") + 1]' | tr '\n' ' ')" == "mongodb meilisearch librechat admin-panel " ]] || { echo "order"; return 1; }
  calls '" ".join(c["args"][2:])' | grep -qv -- "--path-as-root --service .* --environment dev --ci --message efaiw ${reviewed:0:12}" &&
    { echo "unexpected arguments: $(calls 'c["args"]')"; return 1; }
  return 0
}
t_exact_tree() { # the upload equals the committed tree: no .env, ignored, untracked or uncommitted content
  [[ "$(calls 'c["files"]' | sort -u)" == "$(python3 -c 'import sys; print(sorted(sys.argv[1:]))' $(git ls-tree -r --name-only "$reviewed"))" ]] &&
    [[ "$(calls 'c["app"].strip()' | sort -u)" == "reviewed" ]]
}
t_export_removed() { local dir; dir="$(calls 'c["args"][1]' | head -1)"; [[ -n "$dir" && ! -e "$dir" ]]; }
t_single_service() { reset_log; "$deploy" --commit "$reviewed" --service librechat --yes >/dev/null && [[ "$(calls 'c["args"][c["args"].index("--service") + 1]')" == librechat ]]; }
t_stop_on_failure() { reset_log; ! STUB_FAIL_SERVICE=mongodb "$deploy" --commit "$reviewed" --yes >/dev/null 2>&1 && [[ "$(wc -l < "$STUB_LOG")" == 1 ]]; }

check D01 "refuses an abbreviated commit SHA (nothing uploaded)" t_short_sha
check D02 "refuses a commit that is not on origin/main (nothing uploaded)" t_unmerged
check D03 "refuses a non-interactive run without --yes (nothing uploaded)" t_no_tty
check D04 "deploys the reviewed commit: mongodb, meilisearch, librechat, then admin-panel; railway up --path-as-root --environment dev --ci" t_deploy
check D05 "upload is exactly the committed tree (no .env, ignored, untracked or uncommitted files)" t_exact_tree
check D06 "the temporary export is removed after the run" t_export_removed
check D07 "--service librechat uploads only librechat" t_single_service
check D08 "a failed mongodb upload stops the run before librechat" t_stop_on_failure

summary
[[ $failures -eq 0 ]]
