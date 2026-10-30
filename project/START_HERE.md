# START HERE — agent session bootstrap

Navigator only. Verified state lives in [CURRENT_STATE.md](CURRENT_STATE.md) and live GitHub; policy lives in
[AGENTS.md](../AGENTS.md). Nothing in this file is evidence of anything working.

## Identity and boundaries

- EF AI Workspace (working name «بصير», **PROVISIONAL**): Arabic-first, bilingual enterprise AI platform for the
  Environment Fund, built on upstream LibreChat v0.8.8 + MongoDB 8.0.34. Private repository `faenazi/ef-ai-workspace`.
- Three hosts ([ADR-0008](../docs/architecture/adr/0008-multi-environment-hosting-railway-windows-ubuntu.md)):
  Railway `dev` (**synthetic data only**; image inputs merged to `main` autodeploy —
  [ADR-0010](../docs/architecture/adr/0010-railway-dev-autodeploy-from-main.md)), Windows 11 (Ubuntu WSL2 + Docker
  Engine) and Ubuntu on-prem. Production needs a Saudi-approved environment (R1.0).
- Development phase: no mandatory formal quality gate
  ([ADR-0011](../docs/architecture/adr/0011-production-only-quality-gates.md)); the agent merges its own PRs and
  deploys `dev` under [ADR-0009](../docs/architecture/adr/0009-development-phase-agent-delegation.md). Domains,
  spend, real data, SSO, other environments and production stay with the owner.

## Read in this order

1. [AGENTS.md](../AGENTS.md) — rules, session start protocol, verification, documentation rules.
2. [CURRENT_STATE.md](CURRENT_STATE.md) — verified now, NOT RUN, blockers, next task.
3. [ROADMAP.md](ROADMAP.md) — §6 current execution order; §2–§3 release outcomes and exit gates.
4. The selected Issue, its FR/NFR acceptance criteria, and only the docs/ADRs it links.

Then live GitHub: `main` head, open PRs, open Issues. Newer GitHub evidence supersedes any document snapshot.
Follow the [session start protocol](../AGENTS.md#session-start-protocol) in AGENTS.md; it is not repeated here.

## Stop gates

- **LLM provider** — only what OD-01 approves in [scope.md](../docs/product/scope.md) ([#5](https://github.com/faenazi/ef-ai-workspace/issues/5)),
  synthetic data only; any other provider, model or real data needs a new decision; keys only in runtime secrets, never in Git.
- **Official brand** — [#7](https://github.com/faenazi/ef-ai-workspace/issues/7) (D-04): nothing is "official"
  until approved; `APP_TITLE` is a provisional name.
- **Container security** — SC-18 image scan before any digest change or public exposure; the
  [ADR-0012](../docs/architecture/adr/0012-temporary-security-patch-layer.md) patch layer is temporary
  ([#16](https://github.com/faenazi/ef-ai-workspace/issues/16)).
- **`main`** — branch protection is an owner action ([#3](https://github.com/faenazi/ef-ai-workspace/issues/3));
  a merge touching watched paths deploys `dev` immediately, so review before merge is the only control.
- **Owner approval only** — real EF data, employee accounts, the Entra tenant, domains, spend, other environments,
  production. GitHub Projects/Milestones are not verified to exist ([#59](https://github.com/faenazi/ef-ai-workspace/issues/59)).

## Report format

Current verified state (sha, evidence) → what changed → tests run and not run → blocked decisions/risks → next Ready Issue.
