#!/bin/sh
# Railway start adapter for LibreChat (infrastructure/railway/librechat.Dockerfile). POSIX sh (busybox).
#   1. Refuses to start while a required variable is missing (secrets are set once with scripts/setup/railway-secrets.sh).
#   2. Falls back to the private service address while no public domain exists (see below).
#   3. Leaves ADMIN_PANEL_URL unset until the Admin Panel has a public domain (ADR-0016).
#   4. Prepares the single Railway volume at /app/storage (mounted root-owned) for the unprivileged `node` user.
#   5. Sets the MCP permissions of the two roles before the server starts (ADR-0021); stops here if that fails.
#   6. Starts the one-off creation of the EF ready commands in the background (ADR-0018; it waits for the server).
#   7. Drops privileges and execs LibreChat; the container never runs the application as root.
set -eu

missing=""
for name in MONGO_URI CREDS_KEY CREDS_IV JWT_SECRET JWT_REFRESH_SECRET DOMAIN_CLIENT DOMAIN_SERVER; do
  eval "value=\${$name:-}"
  [ -n "$value" ] || missing="$missing $name"
done
if [ -n "$missing" ]; then
  echo "efaiw: refusing to start, required variable(s) not set:$missing (docs/operations/railway.md)" >&2
  exit 64
fi

# Until a public domain is generated (blocked by the SC-18 gate, docs/operations/railway.md §3), Railway renders
# https://${{RAILWAY_PUBLIC_DOMAIN}} as "https://", which LibreChat rejects ("Failed to start server: Invalid URL").
# Use the private address instead: reachable only inside the project network. A generated domain wins on redeploy.
for name in DOMAIN_CLIENT DOMAIN_SERVER; do
  eval "value=\$$name"
  case "$value" in
    http://|https://)
      value="http://${RAILWAY_PRIVATE_DOMAIN:-localhost}:${PORT:-3080}"
      export "$name=$value"
      echo "efaiw: no public domain yet; $name=$value (private network only)" >&2 ;;
  esac
done

# The Admin Panel URL (ADR-0016) references the panel's generated domain; until it exists it renders as "https://",
# which LibreChat would expose as the admins' Settings link. Leave it unset until the domain exists.
case "${ADMIN_PANEL_URL:-}" in
  http://|https://) unset ADMIN_PANEL_URL; echo "efaiw: no admin panel domain yet; ADMIN_PANEL_URL unset" >&2 ;;
esac

# MCP servers for admins only (ADR-0021): before the server, which caches the roles once read. Fails closed (set -e).
policy='cd /app && exec node config/efaiw-roles-policy.js'
# EF ready commands (ADR-0018): created once, never overwritten; the script waits for the server's roles and an ADMIN.
seed='cd /app && exec node config/efaiw-prompts-seed.js /app/efaiw-prompts/ef-templates.json'

if [ "$(id -u)" = "0" ]; then
  mkdir -p /app/storage/uploads /app/storage/images /app/storage/data
  # Only entries not yet owned by node (first start, or files restored from a backup) are changed.
  find /app/storage -xdev ! -user node -exec chown node:node {} +
  su -s /bin/sh node -c "$policy"
  su -s /bin/sh node -c "$seed" &
  exec su -s /bin/sh node -c 'exec "$0" "$@"' "$@"
fi
sh -c "$policy"
sh -c "$seed" &
exec "$@"
