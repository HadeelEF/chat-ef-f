# Delivery Governance v1.1 — حوكمة المنتج والتنفيذ

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس سياسة سارية.** القواعد الحية مدمجة في [تعريف الإنجاز](../../quality/definition-of-done.md)؛ هدف GitHub Project في #59؛ الفهرس: [docs/history/README.md](../README.md).

| الطبقة | المصدر الوحيد |
|---|---|
| Vision, FR/NFR | [Product scope](../../product/scope.md) · [FR](../../product/functional-requirements.md) · [NFR](../../product/non-functional-requirements.md) |
| Product outcomes / release gates | [ROADMAP.md §2–§3](../../../project/ROADMAP.md) |
| Engineering M0–M8 | [ROADMAP.md §4](../../../project/ROADMAP.md); closed checklists in [docs/history](../README.md) |
| Version tags / publication | [ROADMAP.md §5](../../../project/ROADMAP.md) |
| Work status / accountable tasks | Live GitHub Issues and PRs: [ROADMAP.md §2/§6](../../../project/ROADMAP.md) for navigation only |
| Verified runtime | [CURRENT_STATE.md](../../../project/CURRENT_STATE.md) with actual test evidence |
| Architecture decisions | [ADR registry](../../architecture/adr/README.md) |
| Quality | [Definition of Done](../../quality/definition-of-done.md) + [Testing Strategy](../../quality/testing-strategy.md); dev-phase policy [ADR-0011](../../architecture/adr/0011-production-only-quality-gates.md) |

**Owner approval (2026-10-19):** product release sequence R0.1→R1.0 and tracking process approved.
**Not authorized by roadmap alone:** LLM provider choice, spending, real-data handling, SSO, DNS, public exposure, production.

## 1. Planning method — Rolling-wave + Gate

`Product Release (R0.x)` → `Epic Issue` → `Feature / Task / Bug Issue` → `focused branch` → `implementation` →
`task-appropriate verification` → `PR` → `diff review` → `squash merge` → `Issue + CURRENT_STATE update` →
`owner release decision` (per R0.x, on product outcomes).

- R0.2/R0.3 are detailed in [ROADMAP §6](../../../project/ROADMAP.md); later product epics are
  **directional** until their implementation sprint is ready and business/technical acceptance is refined.
- Each Issue: release ID, type, priority P0/P1/P2, outcome, in/out, FR/NFR, dependencies, testable ACs, evidence and rollback.
- Each Epic: intent, dependencies/decision owners, exit gate, linked Issue list; not a giant multi-feature implementation PR.
- One Issue → one branch → one focused PR. Linking a PR isn't proof of deployment.
- No duplicate backlog file; an Issue with a current title/body controls actual status.

## 2. Distinguish work status, capability status, and approvals

| Context | Allowed states |
|---|---|
| Delivery task | `Backlog`, `Ready`, `In Progress`, `In Review`, `Blocked`, `Done` |
| Runtime capability | `Planned` → `Implemented` → `Configured` → `Tested (cloud session)` → `Verified (target environment)` → `Approved` |
| Requirements | `Draft`, `Approved`, `Deferred`, `Withdrawn` |
| Architectural decision | `Proposed`, `Accepted`, `Superseded`, `Deprecated` |

**Do not** translate `Done` in GitHub to `Verified (target environment)` unless the feature was exercised in
the actual target and evidence recorded. Code/docs present ≠ feature working ≠ production approved.

## 3. Definition of Ready (before code)

- Business outcome and scoped deliverables explicit.
- FR/NFR and acceptance criteria are testable with permitted synthetic test data.
- Decision-gates closed or ticket is `Blocked`; no hidden assumption that #5 or #7 is approved.
- Source/owner of external integration and secret provisioning clear without putting secrets in Git.
- Practical verification approach, rollback and image-watched path impact known.
- Owner/specialist approvals exist for sensitive identity or high-impact workflow.

## 4. Definition of Done and release decisions

**Owner decision 2026-10-19 ([ADR-0011](../../architecture/adr/0011-production-only-quality-gates.md)): formal quality gates are
for Production only.** During development, testing and demo:

1. No mandatory per-PR quality gate, GitHub Actions, full `run-all.sh`, Docker smoke or image scan for docs-only changes,
   and no formal architecture/security review for ordinary PRs. An ordinary merge is never blocked only because
   `run-all.sh` was not run.
2. Verification is **task-appropriate engineering work**: docs → review + links where practical; functional → build/test
   the affected behaviour and fix defects; infrastructure/security-sensitive → deployment and security impact, relevant
   checks and any required authorization ([DoD §1](../../quality/definition-of-done.md#1-مرحلة-التطوير-والاختبار-والعرض-الحالية)).
3. Honest evidence: never label an unrun test PASS; static validation and review do not substitute for runtime proof.
4. The agent merges development PRs under [ADR-0009](../../architecture/adr/0009-development-phase-agent-delegation.md)
   (as amended by ADR-0011) after self-review of the diff; docs and CURRENT_STATE reflect only evidenced changes.
5. Change to Railway Docker watched paths on `main` may autodeploy immediately per
   [ADR-0010](../../architecture/adr/0010-railway-dev-autodeploy-from-main.md): understand its deployment consequence before merging.
6. Product Owner records Go/No-Go and residual risks per R0.x on product outcomes; no invented percentages, dates,
   reliability targets. R0.x decisions are **not** formal QA gates.
7. **Production (R1.0):** formal quality gates (functional, integration, security, vulnerability, accessibility,
   performance, DR, deployment validation), independent review and owner/security approvals are defined and enforced
   before any go-live ([DoD §2](../../quality/definition-of-done.md#2-الإنتاج--بوابات-الجودة-الرسمية-planned-قبل-أي-go-live), #58).

## 5. Accountability and parallel safety track

- **Product owner:** release scope, provider/account, cost, official identity, expansion and Gate decisions.
- **Engineering/agent:** small reviewed PRs, task-appropriate verification and honest evidence, rollback, state accuracy.
- **Security/Privacy/Infrastructure:** independent decision before real EF data, Entra tenant, Saudi hosting or production.
- **Domain business owners:** RFP and high-impact evaluation/contracts/finance assistants; outputs remain human reviewed.
- Security checks (SC-18 weekly scans; ADR-0012 layer removal on upgrade), backups, protection of main and private DB continue **in parallel**
  with R0.2/R0.3; safety is not deferred until R1.0.

## 6. GitHub Project / Milestone target

**Actual platform status:** native GitHub Projects v2/Milestone create/edit capability is unavailable in current connector.
The 28 product issues are real; Project Board and native milestones **not created or verified**.
Owner action [#59](https://github.com/faenazi/ef-ai-workspace/issues/59) remains OPEN.

**Target Project name:** `Baseer — Product Delivery`.
Custom fields: Status (`Backlog/Ready/In Progress/In Review/Blocked/Done`),
Type (`Epic/Feature/Task/Bug/Decision`), Priority (`P0/P1/P2`),
Product Release (`R0.1/R0.2/R0.3/R0.4/R0.5/R0.6/R1.0`),
Engineering Milestone (`M0..M8`), Owner, Verification Level, Blocker/Risk.
Views: Product Roadmap, Kanban Delivery, Release Progress, Decisions & Risks.
Native Milestones (R0.1–R1.0) should have link to product Epic, **no invented due dates**;
map existing #5/#7 to release dependency, not duplicate them.

## 7. Reporting KPIs — evidence first

- ACs **accepted with evidence** / ACs planned per release, with Blocked/NOT RUN separately.
- Number of high-risk unverified controls and expiring decisions, assigned owner and expiry.
- Verified user journey per Release Gate, test version, environment, SHA.
- No claim of 100% completion from closed Issues alone, no performance/SLA targets until OD-04 owner approval.
