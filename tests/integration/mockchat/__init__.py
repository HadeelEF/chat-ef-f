"""Mock-LLM chat regression suite (#37, #38, #39, #43, #44). Entry point: tests/integration/mock_chat.py.

Modules: harness (constants, shared state, Compose/stack helpers, run loop), client (LibreChat HTTP/SSE client),
fixtures (synthetic PDF/Word/Excel files), checks_chat (M01–M21, M38, M39–M45, M48, M66–M67, M69, M73–M75, M91), checks_policy
(M22–M27, M35–M37, M46–M47), checks_features (M49–M56, M70), checks_batch2 (M57–M65, M68, M71, M72),
checks_failures (M28–M34).
"""
