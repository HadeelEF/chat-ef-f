# CLAUDE.md — Claude Code entry point

The shared engineering policy for all AI coding agents is imported below. Claude Code only loads `AGENTS.md` through
this import (a `CLAUDE.md` without it causes `AGENTS.md` to be ignored), so keep the next line intact.

@AGENTS.md

For every **new session**, first open [`project/START_HERE.md`](project/START_HERE.md). `project/CURRENT_STATE.md` is
the only runtime-state document: planned ≠ implemented ≠ deployed, and a merged document is never evidence of a deployment.

## Claude Code–specific notes

- **Cloud environment.** The owner works only from a phone: do all building, validation and testing in the cloud
  session yourself; never ask the owner to run terminal commands. Deliver via branch + draft PR with a short,
  mobile-friendly summary and direct links.
- **GitHub access.** Use the GitHub MCP tools (`mcp__github__*`) for Issues and PRs. Plain `git` over HTTPS works for
  clone/fetch/push and for `git ls-remote` against upstream repositories.
- **Docker.** If `docker info` fails, start the daemon (`sudo dockerd &`) before running containers or
  `docker compose config`. The cloud kernel has no IPv6: `railway-emulation.sh` reports its IPv6 checks as SKIP.
- **Railway.** `docs.railway.com` may be unreachable; read `railwayapp/docs` / the `railway` npm package in the
  scratchpad. Validate with `railway_checks.py` (offline); `railway config plan/apply` or deployment only under the current ADR-0009 scope and actual owner authorizations (AGENTS.md).
- **Upstream verification.** When docs sites are unreachable, verify against upstream sources by shallow-cloning
  (e.g. `LibreChat-AI/LibreChat` at the pinned tag, `LibreChat-AI/librechat.ai` for docs) into the scratchpad, never
  into this repository.
- **Skills.** Project skills in `.claude/skills/` are loaded automatically; invoke `implement-feature`,
  `review-changes` or `verify-release` when the task matches.
- **Settings.** `.claude/settings.json` denies reading secret files (`.env`, `.env.*`, keys, `secrets/`) at any depth
  while `.env.example` stays readable via a `Read(!.env.example)` carve-out (checked by `repo_checks.py settings`).
  Keep personal overrides in `.claude/settings.local.json` (git-ignored); do not weaken the shared deny rules.
