#!/usr/bin/env python3
"""Deterministic synthetic chat regression test against a mock LLM (#38, #39, R0.2).

Starts the real Compose stack (compose.yaml + compose.local.yaml) plus the test-only overlay
tests/integration/compose.mock-llm.yaml: the pinned LibreChat v0.8.8 + MongoDB images and a deterministic
OpenAI-compatible mock model (mock-llm/mock-llm.mjs) reachable only on the internal backend network. Then it drives
the same HTTP API the LibreChat web client uses (POST /api/agents/chat/<endpoint> -> SSE /api/agents/chat/stream/<id>)
with synthetic accounts and checks: registration closed, login, model listing/selection, streamed Arabic and English
replies, determinism, history, persistence and reopening after a restart, cancellation, provider and network errors,
per-user isolation, and that no secret reaches logs, API responses or the database.
#39 safe defaults (same run): the shared librechat.yaml policy is applied to both roles and enforced by the backend
(agents, MCP, skills, memories, schedules, code execution, tool smuggling), the role editor cannot outlive a restart,
and provider failures (HTTP 5xx/429/401/404, timeout, Stop during retry backoff) end quickly with a stored, generic
error that leaks no provider text, after which the conversation continues.
#125 (same run): conversation search on the private Meilisearch service (Arabic/English, per user, outage, rebuild of a
lost index), shared links behind the login, and one message answered by two models side by side.
#129 (same run): clarifying questions (tool offered by the specs, answer, skip, refused answer), the sensitive-data
filter, PDF/Word/Excel read as text with upload limits, and long-chat summaries on the fast model.
#131 (same run): the trial lineup (thinking and its depth per spec, set by the server whatever the parameters panel
sends; the model's reasoning sent back with the answer to its question; the previous lineup's models refused).
#135 (same run): Qwen Cloud's web search on every chat endpoint and never in an unstreamed call, set by the server;
a chat written while Meilisearch was down is indexed on the next start.
#146 (same run): the platform brand Skill (ai/skills/, ADR-0017) listed for every user and read-only, its text reaching
the model when skills are on, and the brand block of the specs' instructions in every chat.
#211 (same run): the usage and cost report (scripts/operations/usage-report.sh) per mode, model and user.

The mock is NOT a provider: this test proves LibreChat's chat path, not a live model (OD-01, #5; live: #37).
Everything is throwaway (secrets, users, volumes) and removed at the end. Results are cloud-session evidence.

The checks live in the `mockchat` package next to this file (harness, client, fixtures, checks_chat, checks_policy,
checks_features, checks_batch2, checks_brand, checks_failures); this entry point only puts that directory on sys.path (so
`python3 -I` works) and runs the suite.

Usage:  python3 tests/integration/mock_chat.py [results-file] [--keep]
Needs:  docker with compose >= 2.24, python3 (standard library only), openssl. Exit 0 when every check passes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mockchat.harness import run_suite  # noqa: E402

if __name__ == "__main__":
    sys.exit(run_suite(sys.argv[1:]))
