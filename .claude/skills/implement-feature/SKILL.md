---
name: implement-feature
description: Standard workflow for implementing a GitHub Issue in EF AI Workspace end to end - read requirements and acceptance criteria, inspect affected architecture, plan, implement, validate, update docs and project state, and open a draft pull request with evidence. Use when starting work on any feature, configuration, infrastructure or documentation task.
---

# Implement a feature (Issue → verified draft PR)

Follow every step. Skip a step only if it clearly does not apply, and say so in the PR.

## 1. Orient (no edits yet)

1. Run the session start protocol in `AGENTS.md` (git state, `project/CURRENT_STATE.md`, open PRs/Issues).
2. Read the Issue. Identify the milestone (M0–M8) and linked `FR-xxx` / `NFR-xxx` IDs.
3. Open only the relevant requirement sections in `docs/product/` and the ADRs/docs they reference.
4. Write down the acceptance criteria you will satisfy. If missing or ambiguous, propose them in the Issue/PR
   instead of inventing scope. Stop and report if a blocking open decision (OD-xx) or dependency (D-xx) is unresolved.

## 2. Verify upstream facts before coding

- For LibreChat, Railway, Docker or GitHub Actions behaviour, verify against official sources for the pinned version
  (shallow-clone upstream into the scratchpad if docs sites are unreachable). Record what you verified and where.
- Never rely on memory for versions, config keys, image digests or action SHAs.

## 3. Plan

- Smallest change that meets the criteria. List files to create/modify.
- Check the plan against `AGENTS.md` architecture constraints (upstream-first, pinned versions, private services,
  no secrets, synthetic data only). If a new architectural decision is needed, draft an ADR (status `Proposed`).

## 4. Implement

- Work on a branch `feature/<scope>` (or `fix/`, `docs/`, `chore/`). Conventional Commit messages.
- Match surrounding style. Reference secrets as `${ENV_VAR}`; placeholders only in `*.example` files.

## 5. Verify as the task needs (ADR-0011 — no mandatory gate in development)

- Docs only: review the content; `python3 scripts/validate/repo_checks.py links adr` for affected links.
- Functional: build/run the affected behaviour (e.g. `tests/integration/`), fix what you find before merging.
- Infrastructure/security-sensitive (watched image inputs, `.railway/`, Compose, secrets, auth): understand the deploy
  and security impact; run the relevant checks (`railway_checks.py`, `compose_checks.py`, smoke, gitleaks via
  `run-all.sh`); SC-18 image scan when a digest changes.

Capture what you ran and its result. Never report an unrun check as passed; no exhaustive NOT RUN table is required.

## 6. Update records

- Docs affected by the change (same PR). New requirement IDs never reuse old ones.
- `project/CURRENT_STATE.md`: what is now implemented/configured/tested, with evidence links.
- `CHANGELOG.md` under `Unreleased`.

## 7. Pull request

- Push and open a **draft** PR to `main` using `.github/PULL_REQUEST_TEMPLATE.md`; link the Issue (`Closes #N`).
- Keep the summary short and mobile-readable. Include validation evidence, risks, rollback, and what remains.
- Squash-merge (and deploy to Railway `dev` only) under ADR-0009 as amended by ADR-0011, after self-review of the diff
  and task-appropriate verification; record the merge SHA on the Issue. Anything outside ADR-0009 stays with the owner.
- After a `dev` deploy: one deploy-log comment on #15 (commit, PR, deployment IDs and status, log checks) and a one-line
  link on the Issue (ADR-0023). No separate «deployed» PR: `CURRENT_STATE.md` changes only when verified state changes.
