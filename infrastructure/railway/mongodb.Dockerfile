# syntax=docker/dockerfile:1
# EF AI Workspace — MongoDB image for Railway (ADR-0008). Built by Railway from the repository root.
#
# A minimal derivation of the official image, needed because Railway has no file bind mounts:
#   1. bakes infrastructure/common/mongo-init/ (least-privilege application user, created once on an empty volume);
#   2. refuses to start while a required secret is missing, so the volume is never initialised without authentication;
#   3. listens on IPv6 and IPv4 for Railway private networking (mongodb.railway.internal), with authentication on.
# The official entrypoint still fixes volume ownership and runs mongod as the unprivileged mongodb user.
# The base digest MUST equal infrastructure/compose/compose.yaml (scripts/validate/railway_checks.py).
FROM mongo:8.0.34@sha256:4a4ab5d4834207389e0d7270fac988e21ffedccecba77991a552f755df229907

COPY --chmod=0444 infrastructure/common/mongo-init/ /docker-entrypoint-initdb.d/
COPY --chmod=0555 infrastructure/railway/mongodb-start.sh /usr/local/bin/efaiw-mongodb-start

ENTRYPOINT ["/usr/local/bin/efaiw-mongodb-start"]
CMD ["mongod", "--auth", "--ipv6", "--bind_ip", "::,0.0.0.0", "--setParameter", "diagnosticDataCollectionEnabled=false"]
