---
name: verify-release
description: Verify release or milestone readiness for EF AI Workspace - build and validation status, security checks, configuration completeness, migration and rollback considerations, deployment prerequisites and outstanding risks - and produce an evidence-based go/no-go report. Use before tagging a release, closing a milestone, or requesting deployment approval.
---

# Verify release readiness

Produce an evidence-based report. Every row needs evidence (command output, CI run link, commit, PR). If something
cannot be verified, mark it `NOT VERIFIED` — never assume.

## 1. Scope

- Identify the target: product increment (R0.x), milestone (M0–M8) and/or version (see `project/ROADMAP.md` §1 and §5).
- Collect the milestone acceptance criteria from `project/ROADMAP.md` and the linked Issues.

## 2. Checks

| Area | What to verify |
|---|---|
| Build & validation | Development/demo increments (R0.x): task-relevant evidence for the release outcome (ADR-0011). Production (R1.0): the formal quality gates of `docs/quality/definition-of-done.md` §2 on the release commit. Record as `Tested (cloud session)`; GitHub Actions is not used (#16 D2 revised) |
| Security | gitleaks clean on full history; zizmor clean; no published internal ports; images pinned by tag + digest |
| Configuration completeness | `.env.example` lists every required variable with placeholders; `librechat.yaml` version matches the pinned LibreChat release; no `latest` tags |
| Secrets | Required runtime secrets documented with owner and location; none in Git |
| Data | Synthetic data only in non-approved environments; retention settings documented |
| Migration | Upstream release notes reviewed; config version changes; data/volume migrations; backup taken before upgrade |
| Rollback | Previous version/digest recorded; rollback steps documented and, for deployments, tested |
| Deployment prerequisites | VPS, domain, HTTPS, provider approvals (D-xx / OD-xx in `docs/product/scope.md`) — available or blocking |
| Documentation | `CHANGELOG.md`, `project/CURRENT_STATE.md`, affected docs and ADRs updated |
| Production gates (≥ v1.0.0 only) | Entra ID SSO, RBAC, audit, tested backup/restore, data residency — formally approved |

## 3. Output

1. Verdict: `GO`, `GO with conditions`, or `NO-GO`.
2. Table: check, result (PASS / FAIL / NOT VERIFIED), evidence.
3. Outstanding risks and blockers (link Issues).
4. Explicit statement of what was **not** verified.

Never tag, release, merge or deploy as part of this skill — the project owner decides.
