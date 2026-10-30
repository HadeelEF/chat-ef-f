# syntax=docker/dockerfile:1
# EF AI Workspace — LibreChat Admin Panel image for Railway (ADR-0016, #141). Built by Railway from the repository root.
#
# A derivation of the official upstream image, TEMPORARY like ADR-0012: the official image ships TanStack Start 1.167.30,
# whose server-function responses allow an unauthenticated reflected XSS (CVE-2026-102989, CRITICAL, reachable on the
# public Railway link; no upstream fix yet). The panel is rebuilt from the same upstream commit with dependency versions
# changed (infrastructure/railway/admin-panel/patches/0001: package.json + bun.lock) and a session check on the YAML
# import (0003, #165), in three stages:
#   source:    the upstream source at the commit of the base image, fetched by commit id and verified, patches applied;
#   build:     upstream's own Dockerfile steps on the same Bun image (install, vite build);
#   prod-deps: upstream's production dependency step (install, then --production);
# then the final image replaces dist/, node_modules/, src/server/ and package.json of the official image, upgrades
# Alpine's OpenSSL, musl and zlib, and runs the panel as the upstream `bun` user behind a start guard.
# The EF brand (#160, owner decision 2026-10-23) rides the same rebuild: patch 0002 plus the brand files below, copied
# unaltered into public/ef. When the security layer goes, the source rebuild stays for 0002 alone (ADR-0016, item 5).
# Exit guard: the build fails once the base no longer ships react-start 1.167.30; then remove this layer (ADR-0016).
# The base digest MUST equal infrastructure/compose/compose.yaml (scripts/validate/railway_checks.py).

FROM buildpack-deps:bookworm-scm@sha256:8ea58fbc817960cd62d512044956ff00cb94865e549eeec32c12139413262004 AS source
WORKDIR /src
# The commit is a literal, not an ARG: Railway passes service variables to declared build arguments.
RUN commit=82fb4b61409d5c2e6eceb3d116b89bc957c1620e \
  && git init -q \
  && git fetch -q --depth 1 https://github.com/ClickHouse/librechat-admin-panel.git "$commit" \
  && git -c advice.detachedHead=false checkout -q FETCH_HEAD \
  && test "$(git rev-parse HEAD)" = "$commit"
COPY infrastructure/railway/admin-panel/patches /efaiw/patches
# In order; any patch that does not apply fails the build.
RUN for p in /efaiw/patches/*.patch; do \
      { git apply --check "$p" && git apply "$p" && echo "efaiw: applied ${p##*/}"; } || exit 1; \
    done \
  && rm -rf .git
# EF brand files for patch 0002 (#160), unaltered, served by the panel from /ef/.
COPY infrastructure/common/client/brand/fonts/aktiv-grotesk-regular.otf /src/public/ef/fonts/aktiv-grotesk-regular.otf
COPY infrastructure/common/client/brand/fonts/aktiv-grotesk-semibold.otf /src/public/ef/fonts/aktiv-grotesk-semibold.otf
COPY infrastructure/common/client/brand/fonts/aktiv-grotesk-bold.otf /src/public/ef/fonts/aktiv-grotesk-bold.otf
COPY infrastructure/common/client/brand/assets/logo.svg /src/public/ef/logo.svg
COPY infrastructure/common/client/brand/assets/logo-dark.svg /src/public/ef/logo-dark.svg
COPY infrastructure/common/client/brand/assets/ef-app-icon.svg /src/public/ef/ef-app-icon.svg
COPY infrastructure/common/client/brand/assets/favicon-32x32.png /src/public/ef/favicon-32x32.png

# Upstream's builder image (Dockerfile at the pinned commit: oven/bun:1.3.11-alpine), by digest.
FROM oven/bun:1.3.11-alpine@sha256:7ed9f74c326d1c260abe247ac423ccbf5ac92af62bb442d515d1f92f21e8ea9b AS build
WORKDIR /app
COPY --from=source /src /app
RUN bun install --frozen-lockfile
RUN VITE_BASE_PATH=/ NODE_ENV=production bun run build

FROM oven/bun:1.3.11-alpine@sha256:7ed9f74c326d1c260abe247ac423ccbf5ac92af62bb442d515d1f92f21e8ea9b AS prod-deps
WORKDIR /app
COPY --from=source /src/package.json /src/bun.lock /src/.npmrc ./
COPY --from=source /src/patches patches
COPY --from=source /src/tools tools
RUN bun install --frozen-lockfile && bun install --frozen-lockfile --production

FROM ghcr.io/librechat-ai/librechat-admin-panel:82fb4b61409d5c2e6eceb3d116b89bc957c1620e@sha256:75b30880268f7e9351963e9e278d12eefd8845405fbb7867c36e35a993ce662f

USER root
RUN set -eu; \
  want() { [ "$2" = "$3" ] || { echo "ADR-0016: $1 is $2, expected $3; remove or update this security layer" >&2; exit 1; }; }; \
  want @tanstack/react-start "$(bun -p 'require("/app/node_modules/@tanstack/react-start/package.json").version')" 1.167.30; \
  rm -rf /app/dist /app/node_modules /app/src/server /app/package.json
COPY --from=prod-deps --chown=bun:bun /app/node_modules /app/node_modules
COPY --from=build --chown=bun:bun /app/dist /app/dist
COPY --from=build --chown=bun:bun /app/src/server /app/src/server
COPY --from=build --chown=bun:bun /app/package.json /app/package.json
# Alpine base packages with HIGH/CRITICAL findings in the official image (OpenSSL CVE-2026-31789 is 32-bit only).
RUN set -eu; \
  apk upgrade --no-cache libssl3 libcrypto3 musl musl-utils zlib; \
  v="$(bun -p 'require("/app/node_modules/@tanstack/react-start/package.json").version')"; \
  [ "$v" = 1.168.61 ] || { echo "ADR-0016: react-start is $v after the rebuild, expected 1.168.61" >&2; exit 1; }
COPY --chmod=0555 infrastructure/railway/admin-panel-start.sh /usr/local/bin/efaiw-admin-panel-start
USER bun

ENTRYPOINT ["/usr/local/bin/efaiw-admin-panel-start"]
CMD ["bun", "run", "start"]
