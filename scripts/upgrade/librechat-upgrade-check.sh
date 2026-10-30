#!/usr/bin/env bash
# LibreChat upgrade check (#118, docs/operations/librechat-upgrade.md): what a move to another upstream version would
# break in this repository's customisation, before any pin changes. Read-only: it changes nothing in the repository.
#
#   1. resolves the target (tag, branch or commit) in danny-avila/LibreChat and, for a tag, the ghcr.io image digest;
#   2. applies infrastructure/common/client/patches in order on the target source (like the Dockerfile's source stage),
#      falling back to a three-way merge against the current pinned source, and names the files that conflict;
#   3. checks ar.json against the target's English locale (stale keys, new keys without Arabic, placeholders);
#   4. checks the upstream asset names build.sh replaces, the client build's Node image and librechat.yaml's version;
#   5. reports whether the ADR-0012 security layer is still needed (package versions in the target's lock file).
#
# Usage: scripts/upgrade/librechat-upgrade-check.sh <tag|branch|commit> [report.md]
# Needs: git, node, network access to github.com (and registry access for the digest; skipped when unavailable).
# Exit 0 = every patch applies and the locale is complete; 1 = work is needed (the report lists it); 2 = usage/fetch error.
set -uo pipefail

target="${1:-}"; report="${2:-/dev/null}"
[[ -n "$target" ]] || { sed -n '2,15p' "$0"; exit 2; }
root="$(git rev-parse --show-toplevel)"
client="$root/infrastructure/common/client"
upstream="https://github.com/danny-avila/LibreChat.git"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
problems=0
: > "$report"
say() { echo "$*" | tee -a "$report"; }
bad() { say "- **NEEDS WORK** $*"; problems=$((problems + 1)); }
good() { say "- OK $*"; }

current_commit="$(grep -oE 'commit=[0-9a-f]{40}' "$root/infrastructure/railway/librechat.Dockerfile" | cut -d= -f2)"
current_image="$(grep -m1 -oE '^FROM ghcr.io/librechat-ai/librechat:[^ ]+' "$root/infrastructure/railway/librechat.Dockerfile" | cut -d' ' -f2)"

# 1. Target.
commit="$(git ls-remote "$upstream" "refs/tags/$target^{}" "refs/tags/$target" "refs/heads/$target" 2>/dev/null | awk 'NR==1{print $1}')"
[[ -z "$commit" && "$target" =~ ^[0-9a-f]{7,40}$ ]] && commit="$target"
[[ -n "$commit" ]] || { echo "upgrade-check: $target is not a tag, branch or commit of $upstream" >&2; exit 2; }
say "# LibreChat upgrade check: $target"
say ""
say "- Current: \`$current_image\` (source \`${current_commit:0:7}\`)"
say "- Target: \`$target\` → commit \`$commit\`"
if git ls-remote --tags "$upstream" "refs/tags/$target" | grep -q .; then
  digest="$(docker buildx imagetools inspect "ghcr.io/librechat-ai/librechat:$target" 2>/dev/null | awk '/^Digest:/{print $2; exit}')"
  if [[ -n "$digest" ]]; then say "- Image: \`ghcr.io/librechat-ai/librechat:$target@$digest\`"; else say "- Image digest: NOT CHECKED (no registry access or no image yet)"; fi
else
  say "- Image: none (not a release tag; the client can be tested, the base image cannot)"
fi
src="$work/src"
# The current pinned source too: its blobs let `git apply --3way` merge a patch that no longer applies as is.
git -C "$work" init -q src && git -C "$src" fetch -q --depth 1 "$upstream" "$current_commit" \
  && git -C "$src" fetch -q --depth 1 "$upstream" "$commit" && git -C "$src" -c advice.detachedHead=false checkout -q "$commit" \
  || { echo "upgrade-check: cannot fetch $commit" >&2; exit 2; }
git -C "$src" -c user.name=check -c user.email=check@example.invalid commit -q --allow-empty -m base
say ""

# 2. Client patches, in order (a later patch may build on an earlier one).
say "## Client patches (ADR-0013)"
applied=0; merged=0; total=0
commit_step() { git -C "$src" add -A && git -C "$src" -c user.name=check -c user.email=check@example.invalid commit -q -m "$1"; }
for p in "$client"/patches/*.patch; do
  total=$((total + 1)); name="$(basename "$p")"
  if git -C "$src" apply --check "$p" 2>/dev/null; then
    git -C "$src" apply "$p" && commit_step "$name"; applied=$((applied + 1)); good "\`$name\` applies as is"
  elif git -C "$src" apply --check -R "$p" 2>/dev/null; then
    good "\`$name\` is already in upstream: delete it"
  elif git -C "$src" apply --3way "$p" >/dev/null 2>&1; then
    commit_step "$name"; merged=$((merged + 1))
    good "\`$name\` applies with a clean three-way merge: regenerate it on the new source (no manual edits)"
  else
    files="$(git -C "$src" diff --name-only --diff-filter=U | tr '\n' ' ')"
    [[ -n "$files" ]] || files="$(git -C "$src" apply --check "$p" 2>&1 | grep -oE 'patch failed: [^:]+' | sed 's/patch failed: //' | sort -u | tr '\n' ' ')"
    git -C "$src" reset -q --hard
    bad "\`$name\` conflicts in ${files:-see git apply}: re-make those parts on the new source"
  fi
done
say "- Result: $total patches: $applied apply as is, $merged merge cleanly, $((total - applied - merged)) need manual work"
say ""

# 3. Arabic overlay against the target's English locale.
say "## Arabic translation (ar.json)"
node - "$src/client/src/locales" "$client/ar.json" <<'EOF' | tee -a "$report"
const { readFileSync } = require('node:fs');
const [loc, overlayPath] = process.argv.slice(2);
const en = JSON.parse(readFileSync(`${loc}/en/translation.json`, 'utf8'));
const ar = JSON.parse(readFileSync(`${loc}/ar/translation.json`, 'utf8'));
const ov = JSON.parse(readFileSync(overlayPath, 'utf8'));
const PLURAL = /^(.*)_(zero|one|two|few|many|other)$/;
const enFor = (k) => (k in en ? en[k] : ((m) => m && (en[`${m[1]}_other`] ?? en[`${m[1]}_one`]))(k.match(PLURAL)));
const stale = Object.keys(ov).filter((k) => enFor(k) === undefined);
const missing = Object.keys(en).filter((k) => !(k in ov) && !(k in ar));
const tok = (s, rx) => (String(s).match(rx) ?? []).sort().join('|');
const ph = Object.keys(ov).filter((k) => enFor(k) !== undefined && tok(enFor(k), /\{\{[^}]+\}\}/g) !== tok(ov[k], /\{\{[^}]+\}\}/g));
const line = (label, list) => console.log(`- ${list.length ? '**NEEDS WORK** ' : 'OK '}${label}: ${list.length}${list.length ? ` (${list.slice(0, 12).join(', ')}${list.length > 12 ? ', …' : ''})` : ''}`);
console.log(`- English keys in the target: ${Object.keys(en).length}`);
line('ar.json keys no longer in English (delete them)', stale);
line('English keys without any Arabic (translate them in ar.json)', missing);
line('ar.json values whose {{placeholders}} changed in English', ph);
process.exitCode = stale.length + missing.length + ph.length > 0 ? 1 : 0;
EOF
[[ "${PIPESTATUS[0]}" == 0 ]] || problems=$((problems + 1))
say ""

# 4. Brand asset names, client Node image, config version.
say "## Build inputs"
for f in $(grep -oE 'for f in [^;]+' "$client/build.sh" | sed 's/for f in //'); do
  [[ -f "$src/client/public/assets/$f" ]] || bad "upstream asset \`client/public/assets/$f\` is gone: update brand/ and build.sh"
done
[[ -d "$src/client/public/fonts" ]] || bad "upstream \`client/public/fonts\` is gone: update build.sh"
up_node="$(grep -m1 -oE '^FROM node:[^ ]+' "$src/Dockerfile" | cut -d' ' -f2)"
our_node="$(grep -oE '^FROM node:[^ @]+' "$root/infrastructure/railway/librechat.Dockerfile" | cut -d' ' -f2)"
if [[ "${up_node%%@*}" == "$our_node" ]]; then good "client build Node image \`$our_node\` matches upstream"; else bad "upstream builds with \`$up_node\`, the client stage uses \`$our_node\`: pin the new one (with its digest)"; fi
up_cfg="$(grep -m1 -oE '^version: [0-9.]+' "$src/librechat.example.yaml" | cut -d' ' -f2)"
our_cfg="$(grep -m1 -oE '^version: [0-9.]+' "$root/infrastructure/common/librechat.yaml" | cut -d' ' -f2)"
if [[ "$up_cfg" == "$our_cfg" ]]; then good "librechat.yaml version $our_cfg"; else bad "librechat.yaml is version $our_cfg, upstream's example is $up_cfg: read the config changelog and update"; fi
say ""

# 5. ADR-0012: is the security layer still needed? (versions resolved in the target's lock file; npm comes from the image)
say "## Security layer (ADR-0012)"
node - "$src/package-lock.json" <<'EOF' | tee -a "$report"
const lock = JSON.parse(require('node:fs').readFileSync(process.argv[2], 'utf8'));
const versions = (name) => [...new Set(Object.entries(lock.packages || {}).filter(([p]) => p.endsWith(`node_modules/${name}`)).map(([, v]) => v.version))];
const newer = (v, min) => { const a = v.split('.').map(Number), b = min.split('.').map(Number); for (let i = 0; i < 3; i++) { if (a[i] !== b[i]) return a[i] > b[i]; } return true; };
for (const [name, fixed] of [['handlebars', '4.7.10'], ['proxy-addr', '2.0.8']]) {
  const v = versions(name);
  const ok = v.length > 0 && v.every((x) => newer(x, fixed));
  console.log(`- ${ok ? 'OK' : 'STILL NEEDED'} ${name}: ${v.join(', ') || 'not found'} (fixed in ${fixed})${ok ? ': remove its entry from the layer' : ''}`);
}
console.log('- npm CLI (R-04) comes from the base image: the layer\'s build guard reports it when the image is pinned');
EOF
say ""

say "## Verdict"
if [[ "$problems" == 0 ]]; then say "Ready to upgrade: bump the pins and run the tests (runbook steps 2 and 6)."
else say "$problems item(s) need work before the pins can move (runbook steps 3–5)."; fi
[[ "$problems" == 0 ]]
