# Baseer — GitHub Issue Map and Traceability

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس حالة حالية ولا سياسة.** الحالة الحية: [project/CURRENT_STATE.md](../../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](../README.md).

**Purpose:** Navigation links only, **not** a second backlog or status ledger.
Latest phase closure evidence: [2026-10-19 Audit](../reports/2026-10-19-foundation-closure-audit.md).
No automatic claim that a milestone is complete because GitHub Issues exist. GitHub Issues/PRs hold execution state,
[PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md) holds approved outcomes,
[CURRENT_STATE.md](../2026-10-20-current-state-ledger.md) holds evidence of actual operation.

| Product increment | Epic and pre-existing decision | Execution Issues | Engineering |
|---|---|---|---|
| R0.1 Foundation | [#15 baseline](https://github.com/faenazi/ef-ai-workspace/issues/15) | [#17 target test](https://github.com/faenazi/ef-ai-workspace/issues/17), [#3 branch rule](https://github.com/faenazi/ef-ai-workspace/issues/3), [#16 SC-18](https://github.com/faenazi/ef-ai-workspace/issues/16), [#62 image upgrade](https://github.com/faenazi/ef-ai-workspace/issues/62) | M0/M1/M1.1 |
| R0.2 AI Activation | [#31 Epic](https://github.com/faenazi/ef-ai-workspace/issues/31), [#5 Provider decision](https://github.com/faenazi/ef-ai-workspace/issues/5) | [#37 Provider](https://github.com/faenazi/ef-ai-workspace/issues/37), [#38 mock tests](https://github.com/faenazi/ef-ai-workspace/issues/38), [#39 controls](https://github.com/faenazi/ef-ai-workspace/issues/39), [#40 file scope](https://github.com/faenazi/ef-ai-workspace/issues/40), [#41 gate](https://github.com/faenazi/ef-ai-workspace/issues/41) | M3 |
| R0.3 Brand/UX | [#32 Epic](https://github.com/faenazi/ef-ai-workspace/issues/32), [#7 Brand dependency](https://github.com/faenazi/ef-ai-workspace/issues/7) | [#42 audit](https://github.com/faenazi/ef-ai-workspace/issues/42), [#43 assets](https://github.com/faenazi/ef-ai-workspace/issues/43), [#44 RTL/A11y](https://github.com/faenazi/ef-ai-workspace/issues/44), [#45 gate](https://github.com/faenazi/ef-ai-workspace/issues/45) | M2 |
| R0.4 Preview | [#33 Epic](https://github.com/faenazi/ef-ai-workspace/issues/33) | [#46 privacy/access](https://github.com/faenazi/ef-ai-workspace/issues/46), [#47 feedback](https://github.com/faenazi/ef-ai-workspace/issues/47) | M8/M6 |
| R0.5 EF Intelligence | [#34 Epic](https://github.com/faenazi/ef-ai-workspace/issues/34) | [#48 instructions](https://github.com/faenazi/ef-ai-workspace/issues/48), [#49 RAG](https://github.com/faenazi/ef-ai-workspace/issues/49), [#50 Skills/MCP/Artifacts](https://github.com/faenazi/ef-ai-workspace/issues/50) | M4/M5 |
| R0.6 Assistants | [#35 Epic](https://github.com/faenazi/ef-ai-workspace/issues/35) | [#51 framework](https://github.com/faenazi/ef-ai-workspace/issues/51), [#52 RFP](https://github.com/faenazi/ef-ai-workspace/issues/52), [#53 bids](https://github.com/faenazi/ef-ai-workspace/issues/53), [#54 contracts](https://github.com/faenazi/ef-ai-workspace/issues/54), [#55 finance](https://github.com/faenazi/ef-ai-workspace/issues/55) | M7 |
| R1.0 Production | [#36 Epic](https://github.com/faenazi/ef-ai-workspace/issues/36) | [#56 Saudi infra](https://github.com/faenazi/ef-ai-workspace/issues/56), [#57 SSO/RBAC](https://github.com/faenazi/ef-ai-workspace/issues/57), [#58 Security/DR](https://github.com/faenazi/ef-ai-workspace/issues/58) | M6/M8 |
| Governance | [#60 Roadmap adoption QA](https://github.com/faenazi/ef-ai-workspace/issues/60) (superseded by ADR-0011) | [#59 Project/Milestones setup](https://github.com/faenazi/ef-ai-workspace/issues/59), [#8 Codex check](https://github.com/faenazi/ef-ai-workspace/issues/8), [PR #19 closed, unmerged](https://github.com/faenazi/ef-ai-workspace/pull/19), [#62 upgrade review](https://github.com/faenazi/ef-ai-workspace/issues/62) | Cross-cutting |

## Native GitHub Project/Milestone status and target

**Not yet created/verified:** available GitHub connector supports Issue/PR/repo writes but **not native Projects v2 or
Milestone creation**. [#59](https://github.com/faenazi/ef-ai-workspace/issues/59) is the tracked owner/tool-enabled action.
Do not mark them created from release prefixes in titles.

Expected **Project**: `Baseer — Product Delivery`, fields `Status` (Backlog/Ready/In Progress/In Review/Blocked/Done),
`Type` (Epic/Feature/Task/Bug/Decision), `Priority` (P0/P1/P2), `Product Release` (R0.1..R1.0),
`Engineering Milestone` (M0..M8), `Owner`, `Verification Level`, `Risk/Blocker`.
Views: Product Roadmap, Delivery Board, Release Progress, Decisions & Risks.
Native Milestones: R0.1, R0.2, R0.3, R0.4, R0.5, R0.6, R1.0; **no invented deadlines**.

Rules: Epic → linked child issues, PR → issue; historical decisions #5/#7/#15/#16/#17 never duplicate;
`R0.x` is **not** SemVer `v0.x.y` and status must come from GitHub.
