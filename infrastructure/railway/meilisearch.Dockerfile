# syntax=docker/dockerfile:1
# EF AI Workspace — Meilisearch image for Railway (ADR-0008; conversation search, #125). Built by Railway from the
# repository root.
#
# A minimal derivation of the official image, needed because Railway has no file bind mounts:
#   1. refuses to start while MEILI_MASTER_KEY is missing, so the index is never served without a key;
#   2. listens on IPv6 and IPv4 for Railway private networking (meilisearch.railway.internal), never on a public domain;
#   3. production mode (master key mandatory, no search preview page), no telemetry, data on the service volume.
# The index is derived data: LibreChat rebuilds it from MongoDB (scripts/operations/search-reindex.sh, railway.md).
# The base digest MUST equal infrastructure/compose/compose.yaml (scripts/validate/railway_checks.py).
FROM getmeili/meilisearch:v1.54.3@sha256:e68913ab7d6f5b159529e472cfd362ce3c741fafd3c127961b2142abbe41b3c9

ENV MEILI_HTTP_ADDR="[::]:7700" \
    MEILI_ENV=production \
    MEILI_NO_ANALYTICS=true \
    MEILI_DB_PATH=/meili_data/data.ms
COPY --chmod=0555 infrastructure/railway/meilisearch-start.sh /usr/local/bin/efaiw-meilisearch-start

ENTRYPOINT ["/usr/local/bin/efaiw-meilisearch-start"]
CMD ["/bin/meilisearch"]
