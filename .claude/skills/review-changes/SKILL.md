---
name: review-changes
description: Structured review of a diff, branch or pull request in EF AI Workspace for correctness, architecture alignment, security, maintainability, complexity, test coverage, documentation consistency, performance and breaking changes. Use before opening or approving a PR, or when asked to review changes.
---

# Review changes

Review the diff (`git diff origin/main...HEAD` or the PR files). Read surrounding context only as needed.
Report findings ranked by severity: **Blocker**, **Major**, **Minor**, **Nit**. Each finding: file:line, the
problem, a concrete failure scenario, and a suggested fix. Do not report style preferences as defects.

## Checklist

1. **Correctness** — Does it do what the Issue's acceptance criteria require? Edge cases, error paths, typos in
   config keys (verify against upstream for the pinned version).
2. **Architecture alignment** — Consistent with `AGENTS.md` constraints and accepted ADRs? Upstream-first (ADR-0006)?
   Any new decision without an ADR?
3. **Security**
   - No secrets, tokens, real data, or sensitive documents (also check git history of the branch).
   - No published ports for MongoDB/search/RAG/vector/admin; HTTPS; least-privilege secrets.
   - GitHub Actions: SHA-pinned actions, `permissions: {}` + minimal job permissions, `persist-credentials: false`,
     no untrusted `${{ }}` interpolation in `run:`, no `pull_request_target` with checkout of PR code.
   - AI-specific: data leaving the boundary (provider, embeddings, CDN, MCP), tool permissions, prompt-injection exposure.
4. **Maintainability & complexity** — Smallest coherent change? Unnecessary services, abstractions or files?
5. **Tests & validation** — Were relevant checks run with evidence? Missing tests for new behaviour?
6. **Documentation consistency** — Docs, ADRs, requirement IDs, `CURRENT_STATE.md`, `CHANGELOG.md` updated in the
   same PR? No duplicated authoritative content? Status labels honest (planned vs implemented vs tested)?
7. **Performance** — Resource impact (containers, memory, CI time). Unbounded operations.
8. **Breaking changes** — Config/env var renames, volume or data migrations, upgrade and rollback path documented.

## Output

1. One-line verdict: `Ready`, `Ready with minor fixes`, or `Changes required`.
2. Findings table (severity, location, issue, fix).
3. Validation you ran yourself and the results (or NOT RUN with reason).
