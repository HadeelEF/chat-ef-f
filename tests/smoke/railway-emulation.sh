#!/usr/bin/env bash
# Railway runtime emulation: builds infrastructure/railway/*.Dockerfile exactly as Railway does (repository root as the
# build context) and runs them under Railway's constraints, reproduced locally with plain Docker:
#   - private network that is IPv6-ONLY (worst case: Railway legacy environments) with <service>.railway.internal names;
#   - exactly ONE volume per service, mounted EMPTY and root-owned (like Railway volumes), no bind mounts;
#   - environment variables shaped like .railway/railway.ts (policy from infrastructure/common/librechat.env);
#   - a "redeploy" replaces the container while keeping the volume.
# It proves the derived images, start guards, storage layout and IPv6 connectivity. It is NOT a Railway deployment:
# Railway's edge/HTTPS, healthcheck runner, build service and volume backups are not exercised (docs/operations/railway.md).
#
# Secrets are created, recovered and restored by the real scripts/setup/railway-secrets.sh (stub `railway` CLI), including
# a restore rehearsal with unchanged keys and a negative key-drift check.
#
# Usage: tests/smoke/railway-emulation.sh [results-file]
#   RAILWAY_EMULATION_LIBRECHAT_IMAGE=<tag>: use this prebuilt LibreChat image instead of building librechat.Dockerfile
#   (for hosts whose builds cannot reach GitHub, e.g. a test copy built behind a proxy; R01 then names the image).
#   RAILWAY_EMULATION_ADMIN_PANEL_IMAGE=<tag>: the same for admin-panel.Dockerfile (ADR-0016).
# Needs: docker (Docker >= 28 for IPv6-only networks), python3, openssl. Exit 0 = no check failed.
# On a host kernel without IPv6 the private network falls back to IPv4 (Railway environments created after
# 2025-10-16 are dual-stack), mongod runs without --ipv6, and the IPv6 checks are reported as SKIP (NOT RUN), never PASS.
set -uo pipefail

root="$(git rev-parse --show-toplevel)"
results="${1:-/dev/null}"
tag="efaiw-rw-$$"
net="$tag-net"
mongo_img="$tag-mongodb:local"; app_img="$tag-librechat:local"; meili_img="$tag-meilisearch:local"
panel_img="$tag-admin-panel:local"
mongo_vol="$tag-mongodb-data"; app_vol="$tag-librechat-storage"; meili_vol="$tag-meilisearch-data"
mongo_ctr="$tag-mongodb"; app_ctr="$tag-librechat"; meili_ctr="$tag-meilisearch"; panel_ctr="$tag-admin-panel"
work="$(mktemp -d)"
failures=0; total=0; skipped=0
ipv6=false; [[ -d /proc/sys/net/ipv6 ]] && ipv6=true

log() { echo "$*" | tee -a "$results"; }
check() { # <id> <description> <command...>
  local id="$1" desc="$2"; shift 2; total=$((total + 1))
  if out="$("$@" 2>&1)"; then log "PASS  $id  $desc"; else log "FAIL  $id  $desc :: ${out:0:300}"; failures=$((failures + 1)); fi
}
skip() { log "SKIP  $1  $2 :: NOT RUN — $3"; skipped=$((skipped + 1)); }
cleanup() {
  docker rm -fv "$app_ctr" "$mongo_ctr" "$meili_ctr" "$panel_ctr" "$tag-probe" >/dev/null 2>&1
  docker volume rm "$mongo_vol" "$app_vol" "$meili_vol" >/dev/null 2>&1
  docker network rm "$net" >/dev/null 2>&1
  docker image rm "$mongo_img" "$app_img" "$meili_img" "$panel_img" >/dev/null 2>&1
  rm -rf "$work"
}
trap cleanup EXIT

# --- Railway variables, created by the real scripts/setup/railway-secrets.sh against a stub `railway` CLI that keeps a
# per-service variable store in $work (throwaway; never written to the repository) ---
umask 077
mkdir -p "$work/bin" "$work/vars"
cat > "$work/bin/railway" <<'STUB'
#!/usr/bin/env python3
# Minimal stand-in for `railway variable list/set` (only what railway-secrets.sh calls).
import json, os, sys
args = sys.argv[1:]
service = args[args.index("--service") + 1]
path = os.path.join(os.environ["RAILWAY_STUB_DIR"], service + ".json")
data = json.load(open(path)) if os.path.exists(path) else {}
if args[:2] == ["variable", "list"] and "--json" in args:
    print(json.dumps(data))
elif args[:2] == ["variable", "set"] and "--stdin" in args and "--skip-deploys" in args:
    data[args[2]] = sys.stdin.read()
    json.dump(data, open(path, "w"))
else:
    sys.exit(f"stub: unsupported call {args}")
STUB
chmod +x "$work/bin/railway"
export RAILWAY_BIN="$work/bin/railway" RAILWAY_STUB_DIR="$work/vars" EFAIW_RECOVERY_PASSFILE="$work/passphrase"
openssl rand -hex 16 > "$work/passphrase"
secrets() { "$root/scripts/setup/railway-secrets.sh" "$@"; }
var() { python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$work/vars/$1.json" "$2"; }
write_env_files() { # Railway-shaped variables per service, as .railway/railway.ts declares them
  cat > "$work/mongodb.env" <<EOF
MONGO_INITDB_ROOT_USERNAME=$(var mongodb MONGO_INITDB_ROOT_USERNAME)
MONGO_INITDB_ROOT_PASSWORD=$(var mongodb MONGO_INITDB_ROOT_PASSWORD)
MONGO_APP_DATABASE=LibreChat
MONGO_APP_USERNAME=librechat
MONGO_APP_PASSWORD=$(var mongodb MONGO_APP_PASSWORD)
EOF
  echo "MEILI_MASTER_KEY=$(var meilisearch MEILI_MASTER_KEY)" > "$work/meilisearch.env"
  cat > "$work/librechat.env" <<EOF
HOST=0.0.0.0
PORT=3080
DOMAIN_CLIENT=$domain
DOMAIN_SERVER=$domain
MONGO_URI=mongodb://librechat:$(var mongodb MONGO_APP_PASSWORD)@$mongo_host:27017/LibreChat?authSource=LibreChat
CREDS_KEY=$(var librechat CREDS_KEY)
CREDS_IV=$(var librechat CREDS_IV)
JWT_SECRET=$(var librechat JWT_SECRET)
JWT_REFRESH_SECRET=$(var librechat JWT_REFRESH_SECRET)
MEILI_HOST=http://$meili_host:7700
MEILI_MASTER_KEY=$(var meilisearch MEILI_MASTER_KEY)
ADMIN_PANEL_URL=$panel_domain
EOF
  cat > "$work/admin-panel.env" <<EOF
PORT=3000
API_SERVER_URL=http://$app_host:3080
VITE_API_BASE_URL=$domain
SESSION_SECRET=$(var admin-panel SESSION_SECRET)
EOF
}
admin_email="synthetic.admin@example.invalid"; admin_pw="$(openssl rand -hex 12)"
user_email="synthetic.user@example.invalid"; user_pw="$(openssl rand -hex 12)"
reg_email="synthetic.reg@example.invalid"; reg_pw="Aa1!$(openssl rand -hex 8)"
domain="https://efaiw-emulated.up.railway.app"; panel_domain="https://efaiw-admin-emulated.up.railway.app"
mongo_host="mongodb.railway.internal"; meili_host="meilisearch.railway.internal"; app_host="librechat.railway.internal"
app_uri() { echo "mongodb://librechat:$(var mongodb MONGO_APP_PASSWORD)@$mongo_host:27017/LibreChat?authSource=LibreChat"; }
grep -E '^[A-Z_]+=' "$root/infrastructure/common/librechat.env" > "$work/policy.env"

log "# Railway emulation  commit=$(git -C "$root" rev-parse --short=12 HEAD)  date=$(date -u +%FT%TZ)  docker=$(docker version --format '{{.Server.Version}}')  ipv6=$ipv6"
mongo_cmd=() # empty = the image CMD (mongod --auth --ipv6 --bind_ip ::,0.0.0.0 ...)
$ipv6 || mongo_cmd=(mongod --auth --bind_ip_all --setParameter diagnosticDataCollectionEnabled=false)
meili_addr=() # empty = the image ENV (MEILI_HTTP_ADDR=[::]:7700); IPv4 fallback on a kernel without IPv6
$ipv6 || meili_addr=(-e MEILI_HTTP_ADDR=0.0.0.0:7700)

run_mongo() { # [extra docker args...]
  docker run -d --name "$mongo_ctr" --network "$net" --network-alias "$mongo_host" \
    --mount "type=volume,src=$mongo_vol,dst=/data/db,volume-nocopy" "$@" "$mongo_img" "${mongo_cmd[@]}" >/dev/null
}
run_meili() { # [extra docker args...]
  docker run -d --name "$meili_ctr" --network "$net" --network-alias "$meili_host" \
    --mount "type=volume,src=$meili_vol,dst=/meili_data,volume-nocopy" "${meili_addr[@]}" "$@" "$meili_img" >/dev/null
}
wait_meili() { # ready = /health answers inside the container
  for _ in $(seq 1 30); do
    [[ "$(docker inspect -f '{{.State.Running}}' "$meili_ctr" 2>/dev/null)" == true ]] || { docker logs --tail 20 "$meili_ctr" 2>&1; return 1; }
    docker exec "$meili_ctr" wget -q -O /dev/null http://127.0.0.1:7700/health 2>/dev/null && return 0
    sleep 2
  done
  echo "meilisearch not ready"; return 1
}
run_app() { # [extra docker args...]
  docker run -d --name "$app_ctr" --network "$net" --network-alias "$app_host" \
    --mount "type=volume,src=$app_vol,dst=/app/storage,volume-nocopy" \
    --env-file "$work/policy.env" "$@" "$app_img" >/dev/null
}
in_app() { docker exec -i "$app_ctr" "$@"; }
run_panel() { # [extra docker args...]: no volume (ADR-0016), read-only root filesystem
  docker run -d --name "$panel_ctr" --network "$net" --read-only --tmpfs /tmp "$@" "$panel_img" >/dev/null
}
panel_fetch() { # <path> [json-body] -> HTTP status, from inside the panel container to LibreChat (private network)
  docker exec -i "$panel_ctr" bun -e '
    const [p, b] = process.argv.slice(1);
    fetch(process.env.API_SERVER_URL + p, { method: b ? "POST" : "GET", headers: { "Content-Type": "application/json" },
      body: b || undefined }).then(r => console.log(r.status)).catch(e => { console.error(e.message); process.exit(1); });' "$@"
}
wait_panel() { # ready = /health inside the container
  for _ in $(seq 1 30); do
    [[ "$(docker inspect -f '{{.State.Running}}' "$panel_ctr" 2>/dev/null)" == true ]] || { docker logs --tail 20 "$panel_ctr" 2>&1; return 1; }
    docker exec "$panel_ctr" bun -e 'fetch("http://127.0.0.1:3000/health").then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))' 2>/dev/null && return 0
    sleep 2
  done
  echo "admin-panel not ready"; return 1
}
logs_have() { docker logs "$1" 2>&1 | grep -c -- "$2" >/dev/null; } # grep -c reads all input (no SIGPIPE under pipefail)
http() { # <method> <path> [json-body] [bearer] -> prints "<status> <body>" (from inside the container: the network is IPv6-only)
  in_app node -e '
    const [m, p, b, t] = process.argv.slice(1);
    const h = { "Content-Type": "application/json" }; if (t) h.Authorization = "Bearer " + t;
    fetch("http://127.0.0.1:3080" + p, { method: m, headers: h, body: b || undefined })
      .then(async r => console.log(r.status, await r.text())).catch(e => { console.error(e.message); process.exit(1); });' "$@"
}
wait_health() { # LibreChat /health within ~4 minutes
  for _ in $(seq 1 48); do
    [[ "$(http GET /health 2>/dev/null)" == "200 OK" ]] && return 0
    [[ "$(docker inspect -f '{{.State.Running}}' "$app_ctr" 2>/dev/null)" == true ]] || { docker logs --tail 20 "$app_ctr" 2>&1; return 1; }
    sleep 5
  done
  echo "not healthy"; return 1
}
wait_mongo() { # ready = the application user authenticates over the private network (after first-run init)
  for _ in $(seq 1 40); do
    [[ "$(docker inspect -f '{{.State.Running}}' "$mongo_ctr" 2>/dev/null)" == true ]] || { docker logs --tail 20 "$mongo_ctr" 2>&1; return 1; }
    [[ "$(probe_mongo "$(app_uri)" 'db.runCommand({ ping: 1 }).ok' 2>/dev/null)" == 1 ]] && return 0
    sleep 3
  done
  echo "mongodb not ready"; return 1
}
probe_mongo() { # <uri> <js> : a separate container on the private network (like another Railway service)
  docker run --rm --name "$tag-probe" --network "$net" --entrypoint mongosh "$mongo_img" --quiet --norc "$1" --eval "$2"
}
login_token() {
  http POST /api/auth/login "{\"email\":\"$admin_email\",\"password\":\"$admin_pw\"}" | python3 -c '
import sys, json; status, _, body = sys.stdin.read().partition(" "); d = json.loads(body)
assert status == "200", status; assert d["user"]["role"] == "ADMIN", d["user"]["role"]; print(d["token"])'
}

# ---------------------------------------------------------------- checks
t_secrets_create() { # verified encrypted recovery copy + 9 values set through stdin, no plaintext in the copy
  secrets --recovery-file "$work/recovery.enc" >/dev/null || return 1
  [[ "$(python3 -c 'import json,sys; print(sum(len(json.load(open(f))) for f in sys.argv[1:]))' "$work"/vars/*.json)" == 9 ]] || { echo "not 9 variables"; return 1; }
  ! grep -qF -- "$(var librechat CREDS_KEY)" "$work/recovery.enc" || { echo "plaintext in recovery copy"; return 1; }
  cp -r "$work/vars" "$work/vars.orig"
  write_env_files
}
t_secrets_no_overwrite() { secrets --accept-no-recovery >/dev/null && diff -r "$work/vars.orig" "$work/vars" >/dev/null; }
t_secrets_restore() { # Railway variables lost (new environment): restore the SAME values from the recovery copy
  rm -f "$work"/vars/*.json && secrets --from-recovery "$work/recovery.enc" >/dev/null && diff -r "$work/vars.orig" "$work/vars" >/dev/null
}
t_secrets_old_copy() { # a copy without MEILI_MASTER_KEY (#125) and SESSION_SECRET (ADR-0016) restores; both are generated
  local cipher=(openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 -salt -pass "file:$EFAIW_RECOVERY_PASSFILE")
  local old="$work/recovery-old.enc" status=0
  "${cipher[@]}" -d -in "$work/recovery.enc" | grep -Ev '^(MEILI_MASTER_KEY|SESSION_SECRET)=' | "${cipher[@]}" -e -out "$old" || return 1
  mv "$work/vars" "$work/vars.keep" && mkdir "$work/vars" && secrets --from-recovery "$old" >/dev/null || return 1
  diff "$work/vars.orig/mongodb.json" "$work/vars/mongodb.json" >/dev/null &&
    diff "$work/vars.orig/librechat.json" "$work/vars/librechat.json" >/dev/null &&
    [[ "$(var meilisearch MEILI_MASTER_KEY)" =~ ^[0-9a-f]{64}$ && "$(var admin-panel SESSION_SECRET)" =~ ^[0-9a-f]{64}$ ]] || status=1
  rm -rf "$work/vars" && mv "$work/vars.keep" "$work/vars"; return $status
}
t_redeploy_restored_keys() { # redeploy with restored keys: healthy, admin logs in, no credential-drift warning
  write_env_files && docker rm -fv "$app_ctr" >/dev/null && run_app --env-file "$work/librechat.env" && wait_health && login_token >/dev/null &&
  ! logs_have "$app_ctr" 'do not match the database credential record'
}
t_drift_detected() { # negative: a different CREDS_KEY is detected by LibreChat's key-drift check
  docker rm -fv "$app_ctr" >/dev/null
  sed "s/^CREDS_KEY=.*/CREDS_KEY=$(openssl rand -hex 32)/" "$work/librechat.env" > "$work/wrong.env"
  run_app --env-file "$work/wrong.env" && wait_health && logs_have "$app_ctr" 'do not match the database credential record'
  local status=$?; docker rm -fv "$app_ctr" >/dev/null; run_app --env-file "$work/librechat.env" && wait_health; return $status
}
t_no_public_domain() { # before a domain exists Railway renders https://${{RAILWAY_PUBLIC_DOMAIN}} as "https://"
  docker rm -fv "$app_ctr" >/dev/null
  sed 's#^\(DOMAIN_CLIENT\|DOMAIN_SERVER\|ADMIN_PANEL_URL\)=.*#\1=https://#' "$work/librechat.env" > "$work/nodomain.env"
  run_app --env-file "$work/nodomain.env" -e RAILWAY_PRIVATE_DOMAIN=librechat.railway.internal && wait_health &&
  logs_have "$app_ctr" 'DOMAIN_CLIENT=http://librechat.railway.internal:3080' &&
  logs_have "$app_ctr" 'ADMIN_PANEL_URL unset' && t_no_errors
  local status=$?; docker rm -fv "$app_ctr" >/dev/null; run_app --env-file "$work/librechat.env" && wait_health; return $status
}
t_images_empty_upstream() { # the official image ships no files under the path replaced by the symlink
  [[ -z "$(docker run --rm --entrypoint find "$(grep -m1 '^FROM ghcr.io/librechat-ai/' "$root/infrastructure/railway/librechat.Dockerfile" | cut -d' ' -f2)" /app/client/public/images -mindepth 1)" ]]
}
t_avatar_served() { # the stored avatar is served over HTTP from the volume (/images authorises via the session cookie)
  local path; path="$(in_app sh -c 'cd /app/storage/images && find . -type f -name "avatar*" | head -1')" || return 1
  in_app node -e 'const [p, email, pw] = process.argv.slice(1); (async () => {
    const l = await fetch("http://127.0.0.1:3080/api/auth/login", { method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password: pw }) });
    const cookie = l.headers.getSetCookie().map(c => c.split(";")[0]).join("; ");
    const r = await fetch("http://127.0.0.1:3080/images/" + p.replace(/^\.\//, ""), { headers: { Cookie: cookie } });
    const c = r.headers.get("content-type"); if (!r.ok || !/^image\//.test(c)) { console.error(r.status, c); process.exit(1); }
  })()' "$path" "$admin_email" "$admin_pw"
}

t_build() {
  docker build -q -f "$root/infrastructure/railway/mongodb.Dockerfile" -t "$mongo_img" "$root" >/dev/null || return 1
  docker build -q -f "$root/infrastructure/railway/meilisearch.Dockerfile" -t "$meili_img" "$root" >/dev/null || return 1
  if [[ -n "${RAILWAY_EMULATION_ADMIN_PANEL_IMAGE:-}" ]]; then
    docker tag "$RAILWAY_EMULATION_ADMIN_PANEL_IMAGE" "$panel_img" || return 1
  else
    docker build -q -f "$root/infrastructure/railway/admin-panel.Dockerfile" -t "$panel_img" "$root" >/dev/null || return 1
  fi
  if [[ -n "${RAILWAY_EMULATION_LIBRECHAT_IMAGE:-}" ]]; then
    docker tag "$RAILWAY_EMULATION_LIBRECHAT_IMAGE" "$app_img"
  else
    docker build -q -f "$root/infrastructure/railway/librechat.Dockerfile" -t "$app_img" "$root" >/dev/null
  fi
}
t_base_digest() { # the derived images are built FROM the exact digests pinned for Compose
  local f img
  local -A repo=([librechat]=librechat-ai/librechat: [mongodb]=mongo: [meilisearch]=meilisearch: [admin-panel]=librechat-admin-panel:)
  for f in librechat mongodb meilisearch admin-panel; do
    img="$(grep -E "^\s+image: \S*${repo[$f]}" "$root/infrastructure/compose/compose.yaml" | awk '{print $2}')"
    [[ -n "$img" && "$img" != *$'\n'* ]] || { echo "$f: no unique compose image"; return 1; }
    [[ "$(grep -E '^FROM ' "$root/infrastructure/railway/$f.Dockerfile" | tail -1)" == "FROM $img" ]] ||
      { echo "$f: final FROM differs from compose ($img)"; return 1; }
  done
}
t_network() { docker network create --ipv4=false --ipv6 "$net" >/dev/null &&
              [[ "$(docker network inspect -f '{{.EnableIPv4}} {{.EnableIPv6}}' "$net")" == "false true" ]]; }
t_network_v4() { docker network create "$net" >/dev/null; }
t_mongo_guard() { # no secrets -> exit 64, volume left empty
  docker volume create "$mongo_vol" >/dev/null
  run_mongo; sleep 3
  local code; code="$(docker inspect -f '{{.State.ExitCode}}' "$mongo_ctr")"
  logs_have "$mongo_ctr" 'refusing to start' || { echo "no guard message (exit $code)"; return 1; }
  docker rm -fv "$mongo_ctr" >/dev/null
  [[ "$code" == 64 ]] || { echo "exit $code"; return 1; }
  [[ -z "$(docker run --rm --mount "type=volume,src=$mongo_vol,dst=/v" --entrypoint ls "$mongo_img" -A /v)" ]] || { echo "volume not empty"; return 1; }
}
t_meili_guard() { # no key -> exit 64, volume left empty (production mode would create its database first)
  docker volume create "$meili_vol" >/dev/null
  run_meili; sleep 3
  local code; code="$(docker inspect -f '{{.State.ExitCode}}' "$meili_ctr")"
  logs_have "$meili_ctr" 'refusing to start' || { echo "no guard message (exit $code)"; return 1; }
  docker rm -fv "$meili_ctr" >/dev/null
  [[ "$code" == 64 ]] || { echo "exit $code"; return 1; }
  [[ -z "$(docker run --rm --mount "type=volume,src=$meili_vol,dst=/v" --entrypoint ls "$meili_img" -A /v)" ]] || { echo "volume not empty"; return 1; }
}
t_meili_up() { run_meili --env-file "$work/meilisearch.env" && wait_meili; }
t_meili_v6() { docker exec "$meili_ctr" sh -c 'cat /proc/net/tcp6' | grep -ci ':1E14 ' >/dev/null; } # 7700 = 0x1E14, on ::
t_meili_key() { # from another service on the private network: 401 without the key, 200 with it
  local js='const [h, k] = process.argv.slice(1);
    Promise.all([fetch(h + "/indexes"), fetch(h + "/indexes", { headers: { Authorization: "Bearer " + k } })])
      .then(r => console.log(r.map(x => x.status).join(" "))).catch(e => console.log(e.message))'
  local out; out="$(docker run --rm --name "$tag-probe" --network "$net" --entrypoint node "$app_img" -e "$js" \
    "http://$meili_host:7700" "$(var meilisearch MEILI_MASTER_KEY)")"
  [[ "$out" == "401 200" ]] || { echo "$out"; return 1; }
}
t_search_enabled() { [[ "$(http GET /api/search/enable "" "$(login_token)")" == "200 true" ]]; }
t_app_guard() {
  docker volume create "$app_vol" >/dev/null
  run_app; sleep 3
  local code; code="$(docker inspect -f '{{.State.ExitCode}}' "$app_ctr")"
  logs_have "$app_ctr" 'refusing to start' || { echo "no guard message (exit $code)"; return 1; }
  docker rm -fv "$app_ctr" >/dev/null; [[ "$code" == 64 ]] || { echo "exit $code"; return 1; }
}
t_mongo_up()     { run_mongo --env-file "$work/mongodb.env" && wait_mongo &&
                   logs_have "$mongo_ctr" 'Created application user'; }
t_mongo_v6()     { docker exec "$mongo_ctr" sh -c 'cat /proc/net/tcp6' | grep -ci ':6989 ' >/dev/null; } # 27017 = 0x6989, listening on ::
t_mongo_auth()   { [[ "$(probe_mongo "$(app_uri)" 'db.runCommand({ ping: 1 }).ok')" == 1 ]]; }
t_mongo_noauth() { ! probe_mongo "mongodb://$mongo_host:27017/LibreChat" 'db.getCollectionNames()'; }
t_mongo_least()  { ! probe_mongo "$(app_uri)" 'db.createUser({ user: "x", pwd: "x", roles: [] })'; }
t_app_up()       { run_app --env-file "$work/librechat.env" && wait_health; }
t_app_user() { # every npm/node process of the application runs as uid 1000 (node), none as root
  local procs; procs="$(docker top "$app_ctr" -eo pid,uid,args | awk 'NR>1 && ($3 ~ /node|npm/) {print $2}' | sort -u)"
  [[ "$procs" == 1000 ]] || { echo "uids of node/npm processes: ${procs:-none}"; return 1; }
}
t_config_loaded() { logs_have "$app_ctr" 'Custom config file loaded'; }
t_mongo_conn()    { logs_have "$app_ctr" 'Connected to MongoDB'; }
t_roles_policy() { # ADR-0021: the start script sets the MCP permissions before the server listens
  local out p l
  out="$(docker logs "$app_ctr" 2>&1 | sed 's/\x1b\[[0-9;]*m//g')"
  p="$(grep -n -m1 'efaiw-roles-policy: MCP_SERVERS applied' <<<"$out" | cut -d: -f1)"
  l="$(grep -n -m1 'Server listening' <<<"$out" | cut -d: -f1)"
  [[ -n "$p" && -n "$l" && "$p" -lt "$l" ]] || { echo "policy log line ${p:-missing}, listening line ${l:-missing}"; return 1; }
  probe_mongo "$(app_uri)" 'const m = Object.fromEntries(db.roles.find().toArray().map((r) => [r.name, r.permissions.MCP_SERVERS]));
const off = (b, keys) => keys.every((k) => b[k] === false);
const ok = m.ADMIN && m.ADMIN.USE === true && m.ADMIN.CREATE === true && off(m.ADMIN, ["SHARE", "SHARE_PUBLIC", "CONFIGURE_OBO"])
  && m.USER && off(m.USER, ["USE", "CREATE", "SHARE", "SHARE_PUBLIC", "CONFIGURE_OBO"]);
if (!ok) { print(JSON.stringify(m)); quit(1); }'
}
t_no_errors()     { local e; e="$(docker logs "$app_ctr" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -E ' error: ' || true)"; [[ -z "$e" ]] || { echo "$e" | head -3; return 1; }; }
t_api_config()    { http GET /api/config | python3 -c 'import sys,json; s,_,b=sys.stdin.read().partition(" "); c=json.loads(b)
assert s=="200" and c["registrationEnabled"] is False and c["socialLoginEnabled"] is False, c'; }
t_register() { # ADR-0024: self-registration is refused and creates no account
  local s; s="$(http POST /api/auth/register "{\"name\":\"Synthetic Reg\",\"username\":\"synthreg\",\"email\":\"$reg_email\",\"password\":\"$reg_pw\",\"confirm_password\":\"$reg_pw\"}" | cut -d' ' -f1)"
  [[ "$s" == 403 ]] || { echo "register HTTP $s"; return 1; }
  s="$(http POST /api/auth/login "{\"email\":\"$reg_email\",\"password\":\"$reg_pw\"}" | cut -d' ' -f1)"
  [[ "$s" != 200 ]] || { echo "login HTTP $s"; return 1; }
}
t_bootstrap()     { printf '%s\n' "$admin_pw" | in_app npm run --silent create-user -- "$admin_email" "Synthetic Admin" synthadmin --email-verified=true; }
t_admin_login()   { login_token >/dev/null; }
t_avatar() { # a real upload through LibreChat: the avatar is written under /app/client/public/images -> the volume
  local token; token="$(login_token)" || return 1
  in_app node -e '
    const png = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==", "base64");
    const fd = new FormData(); fd.append("file", new Blob([png], { type: "image/png" }), "avatar.png"); fd.append("manual", "true");
    // LibreChat rejects non-browser User-Agents on file routes ("Illegal request").
    const h = { Authorization: "Bearer " + process.argv[1], "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0" };
    fetch("http://127.0.0.1:3080/api/files/images/avatar", { method: "POST", headers: h, body: fd })
      .then(async r => { const t = await r.text(); if (!r.ok) { console.error(r.status, t); process.exit(1); } })' "$token" &&
  [[ -n "$(in_app find /app/storage/images -type f -name '*avatar*')" ]] || { echo "no avatar file in the volume"; return 1; }
}
t_markers_write() { in_app su -s /bin/sh node -c 'echo synthetic-marker | tee /app/uploads/m.txt /app/data/m.txt >/dev/null'; }
t_markers() {
  local f; for f in /app/storage/uploads/m.txt /app/storage/data/m.txt; do
    [[ "$(in_app cat "$f")" == synthetic-marker ]] || { echo "missing: $f"; return 1; }; done
  [[ -n "$(in_app find /app/storage/images -type f -name '*avatar*')" ]] || { echo "avatar missing"; return 1; }
}
t_redeploy() { docker rm -fv "$app_ctr" "$mongo_ctr" "$meili_ctr" >/dev/null && t_mongo_up_again && t_meili_up &&
               run_app --env-file "$work/librechat.env" && wait_health; }
t_mongo_up_again() { run_mongo --env-file "$work/mongodb.env" && wait_mongo; }
# Admin Panel (ADR-0016): start guard, private connectivity, admin-only access, exit guard of the security layer.
t_panel_guard() { # no variables -> exit 64; a short SESSION_SECRET -> exit 64
  run_panel; sleep 3
  local code; code="$(docker inspect -f '{{.State.ExitCode}}' "$panel_ctr")"
  logs_have "$panel_ctr" 'refusing to start' || { echo "no guard message (exit $code)"; return 1; }
  docker rm -fv "$panel_ctr" >/dev/null; [[ "$code" == 64 ]] || { echo "exit $code"; return 1; }
  run_panel --env-file "$work/admin-panel.env" -e SESSION_SECRET=short; sleep 3
  code="$(docker inspect -f '{{.State.ExitCode}}' "$panel_ctr")"
  logs_have "$panel_ctr" 'at least 32 characters' || { echo "no length message (exit $code)"; return 1; }
  docker rm -fv "$panel_ctr" >/dev/null; [[ "$code" == 64 ]] || { echo "exit $code"; return 1; }
}
t_panel_up() { run_panel --env-file "$work/admin-panel.env" && wait_panel; }
t_panel_user() { # the panel runs as the upstream bun user (uid 1000), never as root
  local uid; uid="$(docker exec "$panel_ctr" id -u)"; [[ "$uid" == 1000 ]] || { echo "uid $uid"; return 1; }
}
t_panel_metrics() { # /metrics needs a bearer token that is not configured: 401
  [[ "$(docker exec "$panel_ctr" bun -e 'fetch("http://127.0.0.1:3000/metrics").then(r=>console.log(r.status))')" == 401 ]]
}
t_panel_admin() { # over librechat.railway.internal: the administrator passes the admin login, a USER is refused
  printf '%s\n' "$user_pw" | in_app npm run --silent create-user -- "$user_email" "Synthetic User" synthuser --email-verified=true >/dev/null || return 1
  local a u
  a="$(panel_fetch /api/admin/login/local "{\"email\":\"$admin_email\",\"password\":\"$admin_pw\"}")" || return 1
  u="$(panel_fetch /api/admin/login/local "{\"email\":\"$user_email\",\"password\":\"$user_pw\"}")" || return 1
  [[ "$a $u" == "200 403" ]] || { echo "admin=$a user=$u (expected 200 403)"; return 1; }
}
t_panel_link() { # /api/config gives the Admin Panel link to the administrator
  local token; token="$(login_token)" || return 1
  [[ "$(http GET /api/config "" "$token" | python3 -c 'import sys,json; s,_,b=sys.stdin.read().partition(" "); print(json.loads(b).get("adminPanelURL"))')" == "$panel_domain" ]]
}
t_panel_exit_guard() { # the security layer's exit guard rejects a base whose react-start is not the vulnerable 1.167.30
  local guard out
  guard="$(awk '/^RUN set -eu; \\$/ {f=1} f {print} f && !/\\$/ {exit}' "$root/infrastructure/railway/admin-panel.Dockerfile" |
    sed -e '1s/^RUN //' -e 's/\\$//')"
  [[ "$guard" == *"want @tanstack/react-start"* ]] || { echo "guard not found in the Dockerfile"; return 1; }
  out="$(docker run --rm --user root --entrypoint sh "$panel_img" -c "$guard" 2>&1)" && { echo "guard passed on a patched base"; return 1; }
  [[ "$out" == *"ADR-0016: @tanstack/react-start is 1.168.61, expected 1.167.30"* ]] || { echo "$out"; return 1; }
}

t_no_leaks() {
  local logs v; logs="$(docker logs "$app_ctr" 2>&1; docker logs "$mongo_ctr" 2>&1; docker logs "$meili_ctr" 2>&1; docker logs "$panel_ctr" 2>&1)"
  for v in $(python3 -c 'import json,sys; [print(v) for f in sys.argv[1:] for v in json.load(open(f)).values()]' "$work"/vars.orig/*.json) \
           "$admin_pw" "$(cat "$work/passphrase")"; do
    grep -qF -- "$v" <<<"$logs" && { echo "a secret value appears in logs"; return 1; }; done; return 0
}

check R26 "railway-secrets.sh writes a verified encrypted recovery copy, then sets 9 secrets via stdin" t_secrets_create
check R27 "railway-secrets.sh never overwrites variables that already exist" t_secrets_no_overwrite
check R01 "Railway Dockerfiles build from the repository root (Railway build context)${RAILWAY_EMULATION_LIBRECHAT_IMAGE:+; librechat: prebuilt $RAILWAY_EMULATION_LIBRECHAT_IMAGE}" t_build
check R31 "the official image ships an empty /app/client/public/images (the symlink discards no asset)" t_images_empty_upstream
check R02 "derived images use the exact base digests pinned in compose.yaml" t_base_digest
if $ipv6; then check R03 "IPv6-only private network (Railway legacy private networking) is created" t_network
else skip R03 "IPv6-only private network" "host kernel has no IPv6; using an IPv4 private network"; t_network_v4; fi
check R04 "mongodb refuses to start without secrets and leaves its volume empty" t_mongo_guard
check R05 "librechat refuses to start without secrets" t_app_guard
check R34 "meilisearch refuses to start without MEILI_MASTER_KEY and leaves its volume empty" t_meili_guard
check R06 "mongodb initialises its empty root-owned volume and creates the app user" t_mongo_up
check R35 "meilisearch starts on its empty root-owned volume with the key" t_meili_up
if $ipv6; then check R36 "meilisearch listens on IPv6 (::) for private networking" t_meili_v6
else skip R36 "meilisearch listens on IPv6 (::)" "host kernel has no IPv6; image ENV MEILI_HTTP_ADDR=[::]:7700 not exercised"; fi
if $ipv6; then check R07 "mongodb listens on IPv6 (::) for private networking" t_mongo_v6
else skip R07 "mongodb listens on IPv6 (::)" "host kernel has no IPv6; image CMD (--ipv6 --bind_ip ::,0.0.0.0) not exercised"; fi
check R08 "app user authenticates via mongodb.railway.internal from another service (private network)" t_mongo_auth
check R09 "unauthenticated access over the private network is rejected" t_mongo_noauth
check R10 "app user has no administrative privileges" t_mongo_least
check R11 "librechat becomes healthy on the private network (GET /health = OK)" t_app_up
check R12 "LibreChat runs as the unprivileged node user, not root" t_app_user
check R13 "baked librechat.yaml is loaded" t_config_loaded
check R14 "LibreChat connected to MongoDB via the private DNS name" t_mongo_conn
check R47 "MCP for admins only (ADR-0021): the role policy ran before the server; ADMIN use+create, USER none, no sharing" t_roles_policy
check R15 "no ERROR-level lines in the LibreChat startup log" t_no_errors
check R16 "/api/config: registration off, social login off (ADR-0024)" t_api_config
check R18 "create-user bootstraps the first administrator" t_bootstrap
check R19 "administrator logs in with role ADMIN" t_admin_login
check R17 "self-registration (POST /api/auth/register) is refused (403) and creates no account" t_register
check R37 "meilisearch answers 401 without the key and 200 with it via meilisearch.railway.internal" t_meili_key
check R38 "conversation search is enabled: LibreChat reaches meilisearch over the private network" t_search_enabled
check R40 "admin-panel refuses to start without its variables or with a short SESSION_SECRET" t_panel_guard
check R41 "admin-panel starts without a volume on a read-only root filesystem (GET /health = ok)" t_panel_up
check R42 "admin-panel runs as the unprivileged bun user, not root" t_panel_user
check R43 "admin-panel /metrics answers 401 (no scrape token configured)" t_panel_metrics
check R44 "via librechat.railway.internal: admin login 200 for the administrator, 403 for a USER" t_panel_admin
check R45 "/api/config gives the administrator the Admin Panel link (ADMIN_PANEL_URL)" t_panel_link
check R46 "the ADR-0016 exit guard fails the build on a base without react-start 1.167.30" t_panel_exit_guard
check R20 "avatar upload is written through the symlink into the single volume" t_avatar
check R21 "uploads/ and data/ paths write into the single volume as node" t_markers_write
check R22 "redeploy (containers replaced, volumes kept) becomes healthy again" t_redeploy
check R23 "administrator still logs in after redeploy (database persisted)" t_admin_login
check R24 "uploads, images and data persisted across the redeploy" t_markers
check R32 "the uploaded avatar is served over HTTP (/images/...) from the volume" t_avatar_served
check R28 "variables lost: --from-recovery restores the identical values" t_secrets_restore
check R39 "a recovery copy without MEILI_MASTER_KEY and SESSION_SECRET restores the rest and generates both" t_secrets_old_copy
check R29 "redeploy with restored keys: healthy, admin logs in, no credential-drift warning" t_redeploy_restored_keys
check R30 "negative: a different CREDS_KEY triggers LibreChat's credential-drift warning" t_drift_detected
check R33 "no public domain yet (DOMAIN_*, ADMIN_PANEL_URL rendered as https://): private fallback, panel URL unset, healthy" t_no_public_domain
check R25 "no secret value appears in container logs" t_no_leaks

log "# result: $((total - failures))/$total passed, $skipped skipped (NOT RUN)"
exit $((failures > 0))
