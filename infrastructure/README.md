# infrastructure/ — one platform, three hosting targets (ADR-0008)

| Path | Purpose | Used by |
|---|---|---|
| [`common/librechat.yaml`](common/librechat.yaml) | LibreChat configuration (version 1.3.17, no secrets) | all |
| [`common/librechat.env`](common/librechat.env) | Non-secret application policy (self-registration off per ADR-0024, shared links behind the login, …) | all (Compose `env_file`; mirrored in `.railway/railway.ts`, drift-checked) |
| [`common/mongo-init/`](common/mongo-init/01-create-app-user.js) | Creates the least-privilege MongoDB application user on an empty volume | all |
| [`compose/compose.yaml`](compose/compose.yaml) | Base stack: LibreChat + MongoDB, digest-pinned, no published ports | Windows, Ubuntu |
| [`compose/compose.local.yaml`](compose/compose.local.yaml) | Windows 11 / workstation: `127.0.0.1:3080` | Windows |
| [`compose/compose.onprem.yaml`](compose/compose.onprem.yaml) + [`Caddyfile`](compose/Caddyfile) | Ubuntu Server: Caddy HTTPS reverse proxy (only service with ports) | Ubuntu |
| [`compose/.env.example`](compose/.env.example) | Placeholder template; generate a real `.env` with the setup scripts | Windows, Ubuntu |
| [`railway/`](railway/librechat.Dockerfile) | Minimal derived images (config baked in, single-volume layout, start guards) | Railway |
| [`../.railway/railway.ts`](../.railway/railway.ts) | Railway Infrastructure as Code (evaluated by the Railway CLI) | Railway |

Guides: [deployment](../docs/operations/deployment.md) · [Railway](../docs/operations/railway.md) ·
[Windows 11](../docs/operations/windows-local.md) · [Ubuntu on-prem](../docs/operations/ubuntu-onprem.md) · [runbook](../docs/operations/runbook.md).
Checks: `scripts/validate/compose_checks.py`, `scripts/validate/railway_checks.py`; tests: `tests/smoke/`.
