# syntax=docker/dockerfile:1
# EF AI Workspace — LibreChat image for Railway (ADR-0008). Built by Railway from the repository root.
#
# A derivation of the official upstream image: the LibreChat server is unchanged, the web client is rebuilt (5.). It
# exists because Railway has no file bind mounts and allows ONE volume per service, and for the Arabic interface:
#   1. bakes infrastructure/common/librechat.yaml into /app/librechat.yaml (the same file Compose bind-mounts);
#   2. maps LibreChat's persistent paths onto the single service volume mounted at /app/storage:
#        /app/uploads -> storage/uploads   /app/client/public/images -> storage/images   /app/data -> storage/data
#      (/app/logs stays ephemeral: Railway collects stdout logs; file logs are not needed for recovery);
#   3. starts as root only to prepare the root-owned Railway volume, then runs LibreChat as the upstream `node` user;
#   4. TEMPORARY (ADR-0012): replaces the packages behind the CRITICAL findings R-01–R-04 until a LibreChat release ships them;
#   5. ADR-0013: replaces the web client (/app/client/dist only) with the Arabic build of the `client` stage below.
#   6. ADR-0017: bakes the platform Skills of ai/skills/ into /app/skill, LibreChat's default DEPLOYMENT_SKILLS_DIR
#      (read-only Skills shown to every user; Compose mounts the same folder).
# The base digest MUST equal infrastructure/compose/compose.yaml (scripts/validate/railway_checks.py).

# Arabic web client (ADR-0013, #89), in two stages:
#   source: the upstream source at the commit of tag v0.8.8 (the base image's release), fetched by commit id and
#           verified, with infrastructure/common/client/patches applied (official buildpack-deps image: git only);
#   client: built on the same Node image as upstream's Dockerfile for v0.8.8, with the Arabic translations merged.
# Without the patches and translations the `client` stage reproduces the official client byte for byte, so the only
# difference from upstream is what infrastructure/common/client contains. The server is not rebuilt.
FROM buildpack-deps:bookworm-scm@sha256:8ea58fbc817960cd62d512044956ff00cb94865e549eeec32c12139413262004 AS source
WORKDIR /src
# The commit is a literal, not an ARG: Railway passes service variables to declared build arguments.
RUN commit=e8f3be08623663d4ad7f7241e693c94469b63bb0 \
  && git init -q \
  && git fetch -q --depth 1 https://github.com/danny-avila/LibreChat.git "$commit" \
  && git -c advice.detachedHead=false checkout -q FETCH_HEAD \
  && test "$(git rev-parse HEAD)" = "$commit"
COPY infrastructure/common/client /efaiw
# In order (a patch may build on an earlier one); any patch that does not apply fails the build.
RUN for p in /efaiw/patches/*.patch; do \
      { git apply --check "$p" && git apply "$p" && echo "efaiw: applied ${p##*/}"; } || exit 1; \
    done \
  && rm -rf .git

FROM node:24.16.0-alpine@sha256:21f403ab171f2dc89bad4dd69d7721bfd15f084ccb46cdd225f31f2bc59b5c9a AS client
WORKDIR /src
COPY --from=source /src /src
# Only the client workspaces, from upstream's integrity-pinned package-lock.json, without install scripts.
RUN npm ci --no-audit --no-fund --ignore-scripts --loglevel=error --include-workspace-root \
  --workspace=packages/data-provider --workspace=packages/client --workspace=client
COPY --from=source /efaiw /efaiw
RUN sh /efaiw/build.sh

FROM ghcr.io/librechat-ai/librechat:v0.8.8@sha256:5b706bcee1ca154a1e2987303aaeca0eb27f97919cccee4bb604226c2f8abf61

USER root
# ADR-0012 security patch layer (docs/security/vulnerability-register.md): handlebars 4.7.10 (R-01, R-02), proxy-addr 2.0.8
# (R-03), npm CLI 11.19.1 = the npm of Node 24.22.0 (R-04, tar). Exact tarballs from registry.npmjs.org, sha256-pinned.
# Exit guard: the build fails unless the base still has the expected vulnerable versions, so a newer upstream image is
# never silently downgraded. When it fails after a LibreChat upgrade, delete the affected entries (or the whole layer).
# NODE_DISABLE_COMPILE_CACHE keeps root out of the node-owned /tmp/node-compile-cache; no npm update check at build time.
RUN set -eu; cd /tmp; \
  export NODE_DISABLE_COMPILE_CACHE=1 NPM_CONFIG_UPDATE_NOTIFIER=false; \
  want() { [ "$2" = "$3" ] || { echo "ADR-0012: $1 is $2, expected $3; remove or update this patch layer" >&2; exit 1; }; }; \
  pkg() { node -p "require('/app/node_modules/$1/package.json').version"; }; \
  want handlebars "$(pkg handlebars)" 4.7.9; want proxy-addr "$(pkg proxy-addr)" 2.0.7; want npm "$(npm -v)" 11.13.0; \
  for f in handlebars/-/handlebars-4.7.10.tgz proxy-addr/-/proxy-addr-2.0.8.tgz npm/-/npm-11.19.1.tgz; do \
    wget -q "https://registry.npmjs.org/$f"; \
  done; \
  printf '%s  %s\n' \
    14f356e6cadb5b064a156d2b39dd843abba8f4b1a38ee036935adecc1a13ad9f handlebars-4.7.10.tgz \
    ffcc8055b78b0852b2889a426ad3a3003b60bc79df704faca194157efa2b2587 proxy-addr-2.0.8.tgz \
    9f58bff01604cb1b14008fef14dceb14d836a49225e45c6c2e37de3be3e707f0 npm-11.19.1.tgz | sha256sum -c -; \
  for p in handlebars-4.7.10 proxy-addr-2.0.8; do \
    dir="/app/node_modules/${p%-*}"; rm -rf "$dir"; mkdir "$dir"; \
    tar -xzf "$p.tgz" -C "$dir" --strip-components=1; chown -R node:node "$dir"; \
  done; \
  npm install -g --offline --no-audit --no-fund --loglevel=error ./npm-11.19.1.tgz; \
  rm -rf /tmp/*.tgz /root/.npm; \
  want handlebars "$(pkg handlebars)" 4.7.10; want proxy-addr "$(pkg proxy-addr)" 2.0.8; want npm "$(npm -v)" 11.19.1
# ADR-0013: the Arabic web client. Root-owned and read-only for the `node` user (the server only reads it).
RUN rm -rf /app/client/dist
COPY --from=client /src/client/dist /app/client/dist
COPY --chmod=0444 infrastructure/common/librechat.yaml /app/librechat.yaml
# ADR-0017: platform Skills (ai/skills/<name>/SKILL.md), root-owned and read-only for the `node` user.
COPY ai/skills /app/skill
# ADR-0018: EF ready commands (ai/prompts/) and the script that creates them once (librechat-start.sh), read-only.
COPY ai/prompts /app/efaiw-prompts
COPY --chmod=0444 infrastructure/common/prompts-seed.js /app/config/efaiw-prompts-seed.js
# ADR-0021: MCP servers for admins only; librechat-start.sh runs it before the server, read-only.
COPY --chmod=0444 infrastructure/common/roles-policy.js /app/config/efaiw-roles-policy.js
COPY --chmod=0555 infrastructure/railway/librechat-start.sh /usr/local/bin/efaiw-librechat-start
RUN rm -rf /app/uploads /app/client/public/images /app/data \
  && mkdir -p /app/storage \
  && ln -s /app/storage/uploads /app/uploads \
  && ln -s /app/storage/images /app/client/public/images \
  && ln -s /app/storage/data /app/data

ENTRYPOINT ["/usr/local/bin/efaiw-librechat-start"]
CMD ["npm", "run", "backend"]
