# AGENTS.md — Shared Engineering Policy for AI Coding Agents

Applies to every AI coding agent (Claude Code, OpenAI Codex, others) and to humans. Claude Code loads this file via
`@AGENTS.md` in `CLAUDE.md`; Codex reads it natively. Keep it concise (< 250 lines, < 32 KiB — enforced by CI).
Detail lives in `docs/` and in skills; read only what the current task needs.

## Project identity

EF AI Workspace: an internal, Arabic-first, bilingual (AR/EN) Enterprise AI Workspace for the Environment Fund (صندوق البيئة),
Saudi Arabia. Built on upstream **LibreChat** (baseline v0.8.8). It is a **PLATFORM**, not an RFP-only app; specialized
assistants (RFP first) are later capabilities on top of it. Repository: `faenazi/ef-ai-workspace` (private).

## Non-negotiable rules

1. **The repository is the single source of truth.** Never rely on chat history; never infer completed work without
   checking evidence (git, PRs, CI, `project/CURRENT_STATE.md`).
2. **Synthetic data only.** Never upload or commit confidential Environment Fund data, real employee records, or real
   knowledge documents — not to Git, any unapproved server or environment, or external model APIs.
3. **No secrets in Git.** Placeholders only in `*.example` files. Runtime secrets live in the deployment platform.
4. **Do not** deploy publicly, change DNS, create paid infrastructure, change repo visibility, or disable security
   controls. Changes go through a feature branch and a PR. During the development phase the agent may merge its own
   PRs and deploy to Railway `dev` under the owner's delegation (ADR-0009); everything else needs the owner.
5. **Do not assume** the VPS, domain, secrets, approved AI providers, brand assets, or Entra ID tenant exist.
6. **Do not invent** business policies, brand colors/fonts/logos, SLA/RTO/RPO/latency targets, or compliance claims.
   Mark unknowns `TBD` and link the open decision (`docs/product/scope.md` OD-xx).
7. **Verified status only.** Distinguish *planned → implemented → configured → tested → verified → approved*.
   Documentation existing is not functionality working.

## Where things live (authoritative locations)

| Need | Location |
|---|---|
| **New session / agent bootstrap** | `project/START_HERE.md` — read first, then verify live GitHub |
| Current verified state, blockers, next task | `project/CURRENT_STATE.md` |
| **Approved roadmap: R0.1–R1.0 outcomes and exit gates, M0–M8, execution order** | `project/ROADMAP.md` |
| Archived reports, original plans, old state ledgers (history, never policy) | `docs/history/README.md` |
| Backlog (tasks, bugs) | **GitHub Issues** (no BACKLOG.md) |
| Vision, scope, open decisions | `docs/product/vision.md`, `docs/product/scope.md` |
| Requirements (FR-xxx / NFR-xxx) | `docs/product/functional-requirements.md`, `docs/product/non-functional-requirements.md` |
| Architecture & decisions | `docs/architecture/` and `docs/architecture/adr/` (the only decision registry) |
| Security controls & data handling | `SECURITY.md`, `docs/security/` |
| Design, brand, UX | `docs/design/` |
| Deployment & operations | `docs/operations/` |
| Definition of Done, testing | `docs/quality/` |
| Runtime AI assets (platform agents/skills/evals) | `ai/` — see `ai/README.md` |
| Development workflows (skills) | `.claude/skills/` (Codex: `.agents/skills` symlink) |
| Full documentation index | `docs/README.md` |

## Session start protocol

Before any task, in a fresh session:

1. Read `project/START_HERE.md` (navigator, not an alternate state ledger); then `git status`, `git log --oneline -15`, current branch; fetch `main`.
2. Read `project/CURRENT_STATE.md` (state, blockers, next priority).
3. List open PRs and open Issues (GitHub tools). Prefer finishing open PR work over starting new work.
4. Pick the task: the next **Ready** Issue from `project/CURRENT_STATE.md` §4 (execution order in `project/ROADMAP.md`
   §6), or the one the owner requested. Status lives there and in the Issues, never in this file.
5. Read the Issue, its linked FR/NFR acceptance criteria, and only the docs/ADRs relevant to it.
6. If acceptance criteria are missing or ambiguous, write them into the Issue/PR as a proposal; do not invent scope.

## Architecture constraints

1. Prefer official upstream LibreChat images and supported configuration (`.env`, `librechat.yaml`); avoid a long-lived
   fork. Customization order is defined in ADR-0006 (config → mounts → build from unmodified source → upstream PR → fork).
2. Pin images by version **and digest**; verify against official upstream sources at implementation time.
3. Support multiple external and local LLM endpoints; policy-based routing is a future capability.
4. Plan for Agents, Skills, RAG, MCP, Artifacts, Arabic/English UX and corporate branding.
5. Entra ID SSO, RBAC, audit, backup, restore and data residency are **production gates** — never claim them done
   without verification evidence.
6. Databases and internal services stay private: no published MongoDB/search/RAG/vector/DB-admin ports (the Admin Panel, ADR-0016, is an
   authenticated app entry point); persistent
   volumes; least-privilege secrets; HTTPS; secure defaults.
7. Do not assume Agents or Skills are deployed by placing files in Git; use the verified mechanisms in `ai/README.md`.
8. Brand via supported configuration first; document anything that needs a fork.
9. One portable platform on three hosts (ADR-0008): Railway (dev/demo, synthetic data only), Windows 11 local and Ubuntu
   on-prem. Shared config lives in `infrastructure/common/`; Railway specifics stay in `.railway/` and
   `infrastructure/railway/`; images are identical by digest. No Coolify; no unnecessary services or microservices.
10. Railway `config plan/apply`, secrets and deploys of `main` commits: environment `dev` only, under ADR-0009, each
    recorded on the tracking Issue. Domains, other environments, new projects or spend changes need an explicit owner
    authorization. `dev` autodeploys from `main` (ADR-0010: this repository only, no Wait for CI, watch paths = image
    inputs), so your review before merge is the only control before deploy: treat watched-path changes as infrastructure
    changes (ADR-0011); `railway-deploy.sh` is the manual fallback.

## Product release governance

Owner-approved product roadmap: `R0.1 Foundation → R0.2 AI Activation → R0.3 Brand & RTL →
R0.4 Controlled Preview → R0.5 EF Knowledge/Skills → R0.6 RFP/other Assistants → R1.0 Saudi Production`.
`R0.x` is a **product outcome ID**, NOT Git tag `v0.x.y`, and does not replace engineering `M0–M8`.
See `project/ROADMAP.md` and `docs/quality/definition-of-done.md`.
Approval of roadmap ≠ approval of any provider, real-data access, identity integration, spend or production.
Live model integration needs OD-01 (`#5`) decided first; anything called "official brand" needs D-04 (`#7`).
Current Railway is synthetic-only; no confidential EF data/employee directory allowed.

## Development workflow

1. One Issue → one branch → one focused PR. Branch names: `feature/<scope>`, `fix/<scope>`, `docs/<scope>`, `chore/<scope>`.
2. Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `refactor:`, `test:`).
3. Implement the smallest change that meets the acceptance criteria. Match surrounding style; no speculative abstractions.
4. Verify as the task needs (below), then open a **draft** PR using `.github/PULL_REQUEST_TEMPLATE.md`, with evidence.
5. Owner reads from a phone: keep PR descriptions short, scannable, with direct links. Squash-merge under ADR-0009 as
   amended by ADR-0011: self-review of the diff and task-appropriate verification done; then update the Issue and
   `project/CURRENT_STATE.md` (if verified state changed).

Use the matching skill when it fits: `implement-feature`, `review-changes`, `verify-release`.

## Verification (development phase — ADR-0011)

Owner decision 2026-10-19: **no mandatory formal quality gate during development, testing and demo**; no mandatory
GitHub Actions or full `run-all.sh` before merge. Verify what the task needs, as engineering work, not as a gate:

- **Docs only:** review for correctness; check affected links/format where practical (`repo_checks.py links adr`).
- **Functional:** build/test the affected behaviour where feasible (e.g. `tests/integration/`); fix defects before merging.
- **Infrastructure/security-sensitive** (watched image inputs, `.railway/`, Compose, secrets, auth, exposure): assess
  deploy and security impact, run the relevant checks, obtain any required authorization. Never knowingly merge broken
  or unsafe configuration.

```bash
python3 -m venv .venv && . .venv/bin/activate                       # once per environment
python -m pip install --require-hashes -r scripts/validate/requirements.txt
python3 scripts/validate/repo_checks.py links adr                   # quick docs check
scripts/validate/run-all.sh      # optional full suite: ci.yml + security.yml equivalent (gitleaks, actionlint, zizmor…)
tests/smoke/compose-stack.sh local|onprem; tests/smoke/railway-emulation.sh   # useful when infrastructure changes
scripts/validate/image-scan.sh --include-railway   # SC-18: required when an image digest changes / before public exposure
```

State only what you actually ran (`Tested (cloud session)`, never `Verified (GitHub CI)`); never report an unrun check as
passed. SC-18 and every safety rule above still apply. Formal quality gates (functional, integration, security,
vulnerability, accessibility, performance, DR, deployment validation, independent review, approvals) are established and
enforced **before Production** (`docs/quality/definition-of-done.md` §2). Never delete or disable workflows, checks or
test scripts — they stay for optional use and production qualification. Details: `scripts/validate/README.md`.

## Coding & configuration standards

- YAML: 2-space indent, `yamllint --strict` clean. JSON: strict (no comments). Text files: UTF-8, LF (see `.editorconfig`).
- Shell/Python helpers: standard library first; pin any new tool by version and hash; justify new dependencies in the PR.
- GitHub Actions: pin actions to full commit SHA with a version comment; `permissions: {}` at workflow level and
  minimal per-job permissions; `persist-credentials: false`; never interpolate untrusted input into `run:`.
- Secrets are referenced as `${ENV_VAR}`; never echo them in logs.

## Documentation rules

- Update affected docs in the **same PR** as the change. No duplicate authoritative content — link instead.
- Human-facing docs in Arabic where useful, technical identifiers in English. Agent-facing files may be English.
- Relative Markdown links only for in-repo targets; `repo_checks.py links` checks links and anchors.
- New decision → new ADR (`docs/architecture/adr/README.md`). New requirement → next free FR/NFR ID, never reuse IDs.
- Detailed feature specs are written when the feature's implementation begins (progressive documentation).
- Policy and reference documents (`AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/`) carry no live status. What is deployed,
  tested or blocked is written only in `project/CURRENT_STATE.md` and the Issues.
- History lives in Git, `CHANGELOG.md`, the Issues and `docs/history/` (moved there with `git mv`). Living documents keep
  no strikethrough text, no "formerly", no superseded paragraphs.
- One owning document per fact; everything else links to it. A decision is explained only in its ADR; other documents
  cite it in one sentence.
- Readable from a phone: no Markdown line longer than 400 characters outside code blocks (`docs/history/` and ADRs
  exempt); narrative goes into lists, not table cells.
- No screenshots in the repository: attach them to the PR or Issue and permalink a commit when a stable reference is
  needed. `project/CURRENT_STATE.md` and `project/START_HERE.md` have size budgets enforced by `repo_checks.py budgets`.

## Recording verified progress

- Update `project/CURRENT_STATE.md` when state changes: what was verified, how, when, with links (PR, CI run, commit).
- Every completion claim needs evidence. Never mark a milestone complete because its documents exist.
- Add a `CHANGELOG.md` entry under `Unreleased` for user-visible or governance changes.
- Blockers and owner decisions go into GitHub Issues (label `blocked` or `decision`) and are linked from `CURRENT_STATE.md`.

## Definition of Done

See `docs/quality/definition-of-done.md`. In short (development phase): acceptance criteria met with honest evidence,
task-appropriate verification, docs/ADRs/state updated, diff self-reviewed, squash-merged through a PR (ADR-0009/0011).
Production: formal quality gates, independent review and explicit owner/security approval.

## Pull requests & issues

- PR title: Conventional Commit style. Body: follow the PR template (summary, linked Issue, evidence, risks, rollback).
- Mark capabilities explicitly as implemented / configured / tested / future.
- Issues use the forms in `.github/ISSUE_TEMPLATE/`; reference FR/NFR IDs and the milestone (M0–M8).
