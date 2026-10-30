"""Role policy checks (#39, #43, #108, #218): stored role policy and backend enforcement (M22–M27, M37), MCP servers for
admins only (M92, M93), an agent created and used by a user (M46), the memory agent (M47), the ADMIN role editor (M35)
and the policy winning again after a restart (M36)."""

from __future__ import annotations

import json
import time

from .checks_brand import always_apply_texts
from .client import (api, expected_reply, final_of, mock_requests, policy_violations, read_stream, requests_for, role,
                     start_chat, text_of, turn)
from .harness import CAPABILITIES, GUARDED, LINEUP, MCP_GUARDED, MCP_PRIVATE_URLS, OPEN, ROOT, check, log


def policy(st: dict) -> None:
    def policy_applied():
        user, admin = role(st["a"], "USER"), role(st["admin"], "ADMIN")
        bad = {"USER": policy_violations(user), "ADMIN": policy_violations(admin, admin=True)}
        return (bool(user) and bool(admin) and not any(bad.values()), f"violations={bad}")
    check("M22", "role policy is stored for both roles: agents/skills/memories/prompts on, published to everyone by ADMIN "
          "only (#189), shared links and compare on (#125); MCP use and add for ADMIN only, never shared (#218); web "
          "search, code, file search, schedules off", policy_applied)

    def endpoints_restricted():
        _, raw = api("GET", "/api/endpoints", st["a"])
        eps = json.loads(raw)
        agents = eps.get("agents", {})
        builtin = sorted(set(eps) & {"openAI", "azureOpenAI", "google", "anthropic", "bedrock", "assistants",
                                     "azureAssistants"})
        return (set(agents.get("capabilities") or []) == CAPABILITIES and agents.get("disableBuilder") is not True
                and not builtin, f"agents={agents} builtin={builtin}")
    check("M23", "/api/endpoints: only the approved agent capabilities (no code, file search, web search, actions), "
          "builder on; no unconfigured built-in provider", endpoints_restricted)

    def no_upstream_branding():
        anon, auth = api("GET", "/api/config")[1], api("GET", "/api/config", st["a"])[1]
        a, u = json.loads(anon), json.loads(auth)
        # The footer is the EF trust notice of the shared policy (#100), never upstream's "LibreChat vX" line.
        policy = dict(line.split("=", 1) for line in (ROOT / "infrastructure/common/librechat.env")
                      .read_text(encoding="utf-8").splitlines() if line and not line.startswith("#") and "=" in line)
        notice, help_url = policy.get("CUSTOM_FOOTER", ""), policy.get("HELP_AND_FAQ_URL", "")
        ok = ("buildInfo" not in a and "buildInfo" not in u and help_url.startswith("/")
              and u.get("helpAndFaqURL") == help_url and notice != "" and u.get("customFooter") == notice
              and "librechat.ai" not in anon + auth)
        return ok, f"buildInfo={'buildInfo' in a}/{'buildInfo' in u} help={u.get('helpAndFaqURL')!r} " \
                   f"footer={u.get('customFooter')!r}"
    check("M37", "/api/config: no build info (also unauthenticated), EF notice and help page, no librechat.ai link (#43, #100, #103)",
          no_upstream_branding)

    def denied_for(who):
        def run_checks():
            routes = GUARDED + (MCP_GUARDED if who != "admin" else [])
            got = {f"{m} {path}": api(m, path, st[who], body)[0] for m, path, body in routes}
            # The code-execution route looks the message up first (404 otherwise): call it with the caller's own reply.
            job, events, _ = turn(st[who], "Synthetic message to attach a code run to.", [])
            own = final_of(events).get("responseMessage", {}).get("messageId")
            got["POST /api/agents/tools/execute_code/call"] = api(
                "POST", "/api/agents/tools/execute_code/call", st[who],
                {"messageId": own, "conversationId": job["conversationId"], "code": "print(1)", "lang": "py"})[0]
            opened = {f"{m} {path}": api(m, path, st[who], body)[0] for m, path, body in OPEN}
            return (all(v == 403 for v in got.values()) and all(v == 200 for v in opened.values()),
                    f"denied={got} open={opened}")
        return run_checks
    check("M24", "USER: 403 on MCP, API keys, schedules and code; agents, skills and memories open (200)",
          denied_for("a"))
    check("M25", "ADMIN: the same, except MCP (#218, M92): 403 on API keys, schedules and code", denied_for("admin"))

    def mcp_for_admin():
        servers, tools = api("GET", "/api/mcp/servers", st["admin"]), api("GET", "/api/mcp/tools", st["admin"])
        # Servers added in the UI are remote only: a local command and a `${VAR}` URL are refused (input schema).
        stdio = api("POST", "/api/mcp/servers", st["admin"],
                    {"config": {"title": "synthetic", "type": "stdio", "command": "node", "args": ["-v"]}})[0]
        env_url = api("POST", "/api/mcp/servers", st["admin"],
                      {"config": {"title": "synthetic", "type": "streamable-http", "url": "https://${MONGO_URI}/mcp"}})[0]
        return (servers[0] == 200 and tools[0] == 200 and stdio == 400 and env_url == 400,
                f"servers={servers[0]} {servers[1][:120]} tools={tools[0]} stdio={stdio} env_url={env_url}")
    check("M92", "MCP for admins only (#218): ADMIN lists MCP servers and tools (200); a local (stdio) server and a "
          "${VAR} URL are refused (400)", mcp_for_admin)

    def mcp_private_refused():
        got = {url: api("POST", "/api/mcp/servers", st["admin"],
                        {"config": {"title": "synthetic", "type": "streamable-http", "url": url}}) for url in MCP_PRIVATE_URLS}
        status, raw = api("GET", "/api/mcp/servers", st["admin"])
        listed = json.loads(raw) if status == 200 else None
        detail = {url: (code, body[:80]) for url, (code, body) in got.items()}
        return all(400 <= code < 500 for code, _ in got.values()) and listed in ({}, []), f"{detail} listed={listed}"
    check("M93", "SSRF protection (#218): an ADMIN cannot add a server on a private, loopback, link-local or internal "
          "service address (4xx), and none is stored", mcp_private_refused)

    def agent_round_trip():
        status, raw = api("POST", "/api/agents", st["a"], {"name": "Synthetic agent", "provider": "Baseer Mock",
                                                          "model": "baseer-mock-echo",
                                                          "instructions": "Synthetic instructions."})
        agent = json.loads(raw) if status in (200, 201) else {}
        if not agent.get("id"):
            return False, f"create HTTP {status}: {raw[:200]}"
        prompt = "Synthetic question for a user-made agent."
        status, job = start_chat(st["a"], prompt, endpoint="agents", extra={"endpointType": None, "agent_id": agent["id"]})
        if status != 200 or not isinstance(job, dict):
            return False, f"chat HTTP {status}: {str(job)[:200]}"
        got = text_of(final_of(read_stream(st["a"], job)[1]).get("responseMessage", {}))
        seen = requests_for(prompt)
        other = api("GET", f"/api/agents/{agent['id']}", st["b"])[0]
        return (got == expected_reply([prompt]) and len(seen) >= 1 and other in (403, 404),
                f"got={got!r} mock={len(seen)} other_user={other}")
    check("M46", "a user creates an agent on an approved endpoint and chats with it; another user cannot open it (#108)",
          agent_round_trip)

    def memory_agent_runs():
        prompt = "Synthetic fact to keep: I prefer a formal tone."
        before = len(mock_requests())
        _, endpoint, model, _ = next(item for item in LINEUP if item[0] == "baseer-pro")
        status, job = start_chat(st["a"], prompt, endpoint=endpoint, model=model)
        if status != 200 or not isinstance(job, dict):
            return False, f"chat HTTP {status}: {str(job)[:200]}"
        got = text_of(final_of(read_stream(st["a"], job)[1]).get("responseMessage", {}))
        memory = []
        for _ in range(20):  # the memory agent runs beside the reply; give it a few seconds
            memory = [r for r in mock_requests()[before:] if "set_memory" in r.get("toolNames", [])]
            if memory:
                break
            time.sleep(0.5)
        models = sorted({r.get("model") for r in memory})
        return (got == expected_reply([prompt]) and bool(memory) and models == ["qwen3.8-flash"],
                f"reply ok={got == expected_reply([prompt])} memory requests={len(memory)} models={models}")
    check("M47", "memories (#108): after a reply the memory agent runs on qwen3.8-flash with the memory tools, and the "
          "reply itself is unchanged", memory_agent_runs)

    def no_tool_smuggling():
        prompt = "Synthetic request that asks for every tool."
        smuggled = {"ephemeralAgent": {"web_search": True, "execute_code": True, "file_search": True, "skills": True,
                                       "artifacts": "default"}}
        status, job = start_chat(st["a"], prompt, extra=smuggled)
        if status != 200 or not isinstance(job, dict):
            return False, f"start HTTP {status}: {str(job)[:200]}"
        _, events = read_stream(st["a"], job)
        got = text_of(final_of(events).get("responseMessage", {}))
        seen = requests_for(prompt)
        offered = sorted({n for r in seen for n in r.get("toolNames", [])})
        log(f"#     tools offered to the model for a plain chat with every flag set: {offered}")
        forbidden = [n for n in offered if any(k in n for k in ("web_search", "execute_code", "file_search"))]
        mcp_prompt = "Synthetic request that asks for an MCP server."
        status, mcp_job = start_chat(st["a"], mcp_prompt, extra={"ephemeralAgent": {"mcp": ["synthetic-server"]}})
        mcp_events = read_stream(st["a"], mcp_job)[1] if status == 200 and isinstance(mcp_job, dict) else []
        mcp_refused = any(e.get("_name") == "error" for e in mcp_events) and not requests_for(mcp_prompt)
        # Skills are allowed (#108): the always-apply platform Skills (ADR-0017) join the turn, one message each.
        want = expected_reply(always_apply_texts() + [prompt])
        return (got == want and len(seen) >= 1 and not forbidden and mcp_refused,
                f"got={got!r} want={want!r} forbidden={forbidden} mcp_refused={mcp_refused}")
    check("M26", "tool smuggling: web search, code and file search flags are dropped (none of their tools reaches the "
          "model; the allowed skills flag primes the platform Skills); an MCP request is refused before any provider "
          "call", no_tool_smuggling)

    def unlisted_model():
        prompt = "Synthetic request for a model that is not configured."
        status, ack = start_chat(st["a"], prompt, model="gpt-4o")
        events = read_stream(st["a"], ack)[1] if status == 200 and isinstance(ack, dict) and "streamId" in ack else []
        outcome = json.dumps(final_of(events) or events[-1:], ensure_ascii=False) if events else str(ack)
        return not requests_for(prompt), f"start HTTP {status}: {outcome[:200]}"
    check("M27", "a model outside the endpoint's configured list never reaches the provider", unlisted_model)


def editor_override(st: dict) -> None:
    def override():
        status, _ = api("PUT", "/api/roles/USER/mcp-servers", st["admin"], {"USE": True})
        shared, _ = api("PUT", "/api/roles/ADMIN/mcp-servers", st["admin"], {"SHARE": True})
        admin = role(st["admin"], "ADMIN").get("MCP_SERVERS", {})
        return (status == 200 and api("GET", "/api/mcp/servers", st["a"])[0] == 200 and shared == 200
                and admin.get("SHARE") is True, f"PUT USER HTTP {status} PUT ADMIN HTTP {shared} ADMIN={admin}")
    check("M35", "ADMIN can still manage roles: granting USER MCP use and ADMIN MCP sharing in the role editor takes "
          "effect", override)


def policy_reapplied(st: dict) -> None:
    def reapplied():
        user, admin = role(st["a"], "USER"), role(st["admin"], "ADMIN")
        bad = {"USER": policy_violations(user), "ADMIN": policy_violations(admin, admin=True)}
        return (not any(bad.values()) and api("GET", "/api/mcp/servers", st["a"])[0] == 403
                and api("GET", "/api/mcp/servers", st["admin"])[0] == 200, f"violations={bad}")
    check("M36", "after restart the policy wins again (librechat.yaml, roles-policy.js #218): the role-editor grants are "
          "reset (USER MCP 403, ADMIN MCP not shared, still 200)", reapplied)
