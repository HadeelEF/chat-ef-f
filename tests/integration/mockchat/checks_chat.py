"""Chat-path checks (#38): stack and accounts (M01–M09), streaming/history/cancellation/errors/isolation
(M10–M18, M38), employee model lineup (M39–M44, M48, #37; M66–M67, #131; M69, #135; M73–M75, #138), simple shell
(M45, #87), usage and cost report (M91, #211), restart (M19–M20) and secret hygiene (M21)."""

from __future__ import annotations

import json
import os
import time

from . import harness
from .client import (api, create_user, deltas, expected_reply, final_of, login, messages, mock_requests, read_stream,
                     requests_for, sha8, start_chat, text_of, turn)
from .checks_batch2 import instruction_lines, spec_instructions
from .harness import (EFFORT, ENDPOINT, HIDDEN_UI, LABELS, LINEUP, MARKDOWN, MODELS, NOWEB, OFFLINE, PROJECT, RETIRED,
                      RETRY, SEARCH_STRATEGY, THINKING, WELCOME, check, ctr, dc, env_value, run, wait_healthy)


def stack(st: dict) -> None:
    pw, users = st["pw"], st["users"]
    key = st["key"]

    check("M01", "compose config renders with the mock overlay and a complete env file",
          lambda: (dc("config", "--quiet").returncode == 0, dc("config", "--quiet").stderr))
    dc("up", "-d", "--quiet-pull")
    check("M02", "librechat, mongodb, meilisearch, admin-panel and mock-llm become healthy", wait_healthy)

    def pinned():
        for svc in ("librechat", "mock-llm", "mongodb", "meilisearch", "admin-panel"):
            cfg = run("docker", "inspect", "-f", "{{.Config.Image}}", ctr(svc)).stdout.strip()
            img = run("docker", "inspect", "-f", "{{.Image}}", ctr(svc)).stdout.strip()
            if not cfg.endswith("@" + img):
                return False, f"{svc}: configured {cfg}, running {img}"
        return True
    check("M03", "all containers run the digest-pinned images (mock reuses the LibreChat image)", pinned)

    def mock_private():
        ports = run("docker", "port", ctr("mock-llm")).stdout.strip()
        nets = run("docker", "inspect", "-f", "{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}",
                   ctr("mock-llm")).stdout.split()
        internal = run("docker", "network", "inspect", "-f", "{{.Internal}}", f"{PROJECT}_backend").stdout.strip()
        return (not ports and nets == [f"{PROJECT}_backend"] and internal == "true", f"ports={ports} nets={nets}")
    check("M04", "mock-llm publishes no port and is attached only to the internal backend network", mock_private)

    def mock_needs_key():
        js = "fetch('http://mock-llm:8080/v1/models').then(r=>{console.log(r.status)}).catch(e=>console.log(e.message))"
        out = run("docker", "exec", ctr("librechat"), "node", "-e", js).stdout.strip()
        return out == "401", out
    check("M05", "mock-llm refuses requests without the configured API key (401)", mock_needs_key)

    def accounts():
        # The first account of a fresh database becomes ADMIN (v0.8.8 AuthService); bootstrap it so A and B are USERs.
        out = create_user("synthetic.chat.admin@example.invalid", "Synthetic Chat Admin", "synthchatadmin", pw["admin"])
        if out.returncode != 0:
            return False, out.stderr
        status, body = login("synthetic.chat.admin@example.invalid", pw["admin"])
        if status != 200 or body.get("user", {}).get("role") != "ADMIN":
            return False, f"login admin: HTTP {status}"
        st["admin"] = body["token"]
        for u, name in (("a", "Synthetic Chat A"), ("b", "Synthetic Chat B")):
            out = create_user(users[u], name, f"synthchat{u}", pw[u])
            if out.returncode != 0:
                return False, out.stderr
            status, body = login(users[u], pw[u])
            if status != 200 or body.get("user", {}).get("role") != "USER":
                return False, f"login {u}: HTTP {status}"
            st[u] = body["token"]
        # v0.8.8 answers a failed local login with 404 + message, no token (api/server/middleware/requireLocalAuth.js).
        status, body = login(users["a"], "wrong-" + pw["a"])
        return status in (401, 404, 422) and "token" not in body, f"wrong password HTTP {status}"
    check("M07", "synthetic ADMIN and two USERs log in with their roles; a wrong password is rejected", accounts)

    def registration_closed():
        # ADR-0024: LibreChat's registration form is off; the register route refuses and no account is created.
        _, cfg = api("GET", "/api/config")
        pw_reg = "Aa1!" + pw["a"]
        code, _ = api("POST", "/api/auth/register", body={"name": "Synthetic Reg", "username": "synthreg",
                      "email": "synthetic.reg@example.invalid", "password": pw_reg, "confirm_password": pw_reg})
        status, _ = login("synthetic.reg@example.invalid", pw_reg)
        ok = json.loads(cfg).get("registrationEnabled") is False and code == 403 and status != 200
        return ok, f"register HTTP {code}, login HTTP {status}"
    check("M06", "self-registration is off: the register route refuses and no account signs in", registration_closed)

    def endpoints_listed():
        status, raw = api("GET", "/api/endpoints", st["a"])
        eps = json.loads(raw)
        ok = status == 200 and eps.get(ENDPOINT, {}).get("type") == "custom" and OFFLINE in eps and RETRY in eps
        leak = key in raw or "mock-llm:" in raw
        return ok and not leak, f"HTTP {status} endpoints={sorted(eps)} leak={leak}"
    check("M08", "/api/endpoints lists the mock endpoints without exposing key or internal URL", endpoints_listed)

    def models_listed():
        status, raw = api("GET", "/api/models", st["a"])
        return (status == 200 and json.loads(raw).get(ENDPOINT) == MODELS, json.loads(raw).get(ENDPOINT))
    check("M09", "model selection: /api/models offers exactly the configured mock models", models_listed)


def chat(st: dict) -> None:
    def english():
        job, events, want = turn(st["a"], "Hello from a synthetic tester. Summarise nothing.", [])
        fin, parts = final_of(events), deltas(events)
        st["en"] = {"convo": job["conversationId"], "events": events, "want": want,
                    "assistant": fin.get("responseMessage", {}).get("messageId")}
        got = text_of(fin.get("responseMessage", {}))
        conv = fin.get("conversation", {})
        ok = (len(parts) >= 3 and "".join(parts) == want and got == want
              and conv.get("endpoint") == ENDPOINT and conv.get("model") == MODELS[0])
        return ok, f"deltas={len(parts)} got={got!r} want={want!r} model={conv.get('model')}"
    check("M10", "English prompt: reply streams in >= 3 deltas and equals the deterministic text", english)

    def arabic():
        prompt = "مرحباً، هذا اختبار اصطناعي للمحادثة باللغة العربية."
        job, events, want = turn(st["a"], prompt, [])
        fin, parts = final_of(events), deltas(events)
        st["ar"] = {"convo": job["conversationId"], "prompt": prompt}
        _, saved = messages(st["a"], job["conversationId"])
        stored = [m.get("text") for m in saved if m.get("isCreatedByUser")]
        got = text_of(fin.get("responseMessage", {}))
        return (len(parts) >= 3 and "".join(parts) == want and got == want and stored == [prompt],
                f"deltas={len(parts)} got={got!r} stored={stored!r}")
    check("M11", "Arabic prompt: streamed Arabic reply is exact and the Arabic prompt is stored unchanged", arabic)

    def deterministic():
        _, events, want = turn(st["a"], "Hello from a synthetic tester. Summarise nothing.", [])
        got = text_of(final_of(events).get("responseMessage", {}))
        return got == want == st["en"]["want"], f"{got!r} vs {st['en']['want']!r}"
    check("M12", "determinism: the same prompt in a new conversation yields a byte-identical reply", deterministic)

    def follow_up():
        first = "Hello from a synthetic tester. Summarise nothing."
        prompt = "Second synthetic question in the same conversation."
        _, events, want = turn(st["a"], prompt, [first], convo=st["en"]["convo"], parent=st["en"]["assistant"])
        got = text_of(final_of(events).get("responseMessage", {}))
        st["en"]["assistant"] = final_of(events).get("responseMessage", {}).get("messageId")
        st["en"]["user_texts"] = [first, prompt]
        last = [r for r in mock_requests() if r.get("event") == "chat.completions"][-1]
        return (got == want and "Turn 2" in got and last.get("userTurns") == 2, f"got={got!r} mock={last}")
    check("M13", "follow-up: history is sent to the model (Turn 2) and answered in the same conversation", follow_up)

    def persisted():
        status, saved = messages(st["a"], st["en"]["convo"])
        texts = [m.get("text") if m.get("isCreatedByUser") else text_of(m) for m in saved]
        t1, t2 = st["en"]["user_texts"]
        want = [t1, expected_reply([t1]), t2, expected_reply([t1, t2])]
        _, convos = api("GET", "/api/convos?sortBy=updatedAt&sortDirection=desc", st["a"])
        ids = [c["conversationId"] for c in json.loads(convos)["conversations"]]
        st["a_convos"] = ids
        return (status == 200 and texts == want and st["en"]["convo"] in ids, f"texts={texts} convos={len(ids)}")
    check("M14", "conversation persisted: 4 messages in order, listed in the user's conversations", persisted)

    def cancel_and_isolation():
        status, job = start_chat(st["a"], "Please stream slowly for a cancellation test.", model="baseer-mock-slow")
        if status != 200 or not isinstance(job, dict):
            return False, f"start HTTP {status}"
        body = {"streamId": job["streamId"], "conversationId": job["conversationId"],
                "generationCreatedAt": job["generationCreatedAt"]}
        seen: dict = {}

        def on_delta(events):
            if len(deltas(events)) >= 3 and "abort" not in seen:
                seen["b_stream"], _ = read_stream(st["b"], job, timeout=10)
                seen["b_abort"], _ = api("POST", "/api/agents/chat/abort", st["b"], body)
                seen["abort"], seen["abort_body"] = api("POST", "/api/agents/chat/abort", st["a"], body)
        _, events = read_stream(st["a"], job, on_delta=on_delta)
        fin = final_of(events)
        st["cancel"] = {**seen, "aborted": fin.get("aborted"), "convo": job["conversationId"]}
        _, saved = messages(st["a"], job["conversationId"])
        reply = next((m for m in saved if not m.get("isCreatedByUser")), {})
        full = expected_reply(["Please stream slowly for a cancellation test."])
        ok = (seen.get("abort") == 200 and fin.get("aborted") is True and reply.get("unfinished") is True
              and 0 < len(text_of(reply)) and len(deltas(events)) < 150)
        return ok, f"abort={seen.get('abort')} final.aborted={fin.get('aborted')} saved={text_of(reply)!r} full={full!r}"
    check("M15", "cancellation: stop mid-stream -> final aborted, partial reply saved as unfinished", cancel_and_isolation)

    def markdown_round_trip():
        _, job = start_chat(st["a"], "اعرض ملخصاً اصطناعياً بتنسيق Markdown.", model="baseer-mock-markdown")
        _, events = read_stream(st["a"], job)
        fin = final_of(events)
        got = text_of(fin.get("responseMessage", {}))
        _, saved = messages(st["a"], fin.get("conversation", {}).get("conversationId", ""))
        stored = next((text_of(m) for m in saved if not m.get("isCreatedByUser")), "")
        return got == MARKDOWN == stored and len(deltas(events)) >= 3, f"got={got[:80]!r} stored_equal={stored == MARKDOWN}"
    check("M38", "mixed Arabic/English Markdown (list, URL, code block with Arabic, table) streams and is stored "
          "byte-identical (#44)", markdown_round_trip)

    def provider_error():
        t0 = time.monotonic()
        _, events, _ = turn(st["a"], "Trigger a synthetic provider error.", [], model="baseer-mock-error")
        _, saved = messages(st["a"], final_of(events).get("conversation", {}).get("conversationId", ""))
        reply = next((m for m in saved if not m.get("isCreatedByUser")), {})
        err = [p for p in reply.get("content") or [] if p.get("type") == "error"]
        healthy = api("GET", "/health")[1] == "OK"
        return (bool(err) and "upstream_model_error" in err[0].get("error", "") and healthy
                and time.monotonic() - t0 < 30, f"error={err} healthy={healthy}")
    check("M16", "provider error (HTTP 400): the turn ends quickly with a saved error message; app stays up", provider_error)

    def network_error():
        _, events, _ = turn(st["a"], "اختبار اصطناعي لخطأ الشبكة.", [], endpoint=OFFLINE)  # Arabic on the error path
        _, saved = messages(st["a"], final_of(events).get("conversation", {}).get("conversationId", ""))
        reply = next((m for m in saved if not m.get("isCreatedByUser")), {})
        err = [p for p in reply.get("content") or [] if p.get("type") == "error"]
        text = json.dumps(err)
        # endpoints.agents.maxProviderErrorChars: 0 (#39) stores only the error type, not the client's error text.
        return (bool(err) and "upstream_model_error" in text and "mock-llm" not in text
                and api("GET", "/health")[1] == "OK", f"error={err}")
    check("M17", "network error (closed port, Arabic prompt): saved generic provider error, no internal URL; app up",
          network_error)

    def isolation():
        c = st["cancel"]
        _, raw = api("GET", "/api/convos?sortBy=updatedAt&sortDirection=desc", st["b"])
        b_convos = json.loads(raw)["conversations"]
        msg_status, _ = messages(st["b"], st["en"]["convo"])
        before = len(messages(st["a"], st["en"]["convo"])[1])
        intrude = "Synthetic intrusion attempt into another user's conversation."
        status, ack = start_chat(st["b"], intrude, convo=st["en"]["convo"], parent=st["en"]["assistant"])
        after = len(messages(st["a"], st["en"]["convo"])[1])
        reached = any(f"user:{sha8(intrude)}" in r.get("digests", []) for r in mock_requests())
        ok = (b_convos == [] and msg_status == 404 and c.get("b_stream") == 403 and c.get("b_abort") == 403
              and "convo_access" in str(ack) and before == after and not reached)
        return ok, (f"b_convos={len(b_convos)} msgs={msg_status} stream={c.get('b_stream')} abort={c.get('b_abort')} "
                    f"post={status}:{str(ack)[:80]} a_msgs {before}->{after} reached_model={reached}")
    check("M18", "isolation: user B cannot list, read, stream, abort or write into user A's conversations", isolation)


def lineup(st: dict) -> None:
    """Employee model lineup of librechat.yaml (#37, #131), with every Qwen Cloud endpoint pointed at the mock
    (merged_config)."""
    def specs_offered():
        status, raw = api("GET", "/api/config", st["a"])
        cfg = json.loads(raw) if status == 200 else {}
        specs = [(s.get("name"), s.get("preset", {}).get("endpoint"), s.get("preset", {}).get("model"))
                 for s in cfg.get("modelSpecs", {}).get("list", [])]
        default = [s.get("name") for s in cfg.get("modelSpecs", {}).get("list", []) if s.get("default")]
        want = [(spec, endpoint, model) for spec, endpoint, model, _ in LINEUP]
        hidden = cfg.get("interface", {}).get("modelSelect") is False
        return (specs == want and default == ["baseer-lite"] and hidden,
                f"specs={specs} default={default} modelSelect={cfg.get('interface', {}).get('modelSelect')}")
    check("M39", "/api/config offers exactly the three named specs in order (not their hidden no-search twins, "
          "#138), «بصير لايت» by default, raw model list hidden", specs_offered)

    def lists_fixed():
        _, raw = api("GET", "/api/models", st["a"])
        models = json.loads(raw)
        want = {}
        for _, endpoint, model, _ in LINEUP:
            want.setdefault(endpoint, []).append(model)
        for _, endpoint, visible in NOWEB:
            want[endpoint] = [next(model for spec, _, model, _ in LINEUP if spec == visible)]
        got = {endpoint: models.get(endpoint) for endpoint in want}
        return got == want, f"got={got}"
    check("M40", "/api/models: each Qwen Cloud endpoint, no-search twins included, offers exactly its lineup model "
          "(fixed lists, no fetched extras)",
          lists_fixed)

    def spec_turns():
        results, ok = [], True
        st["lineup"] = []
        for spec, endpoint, model, thinking in LINEUP:
            prompt = f"Synthetic lineup check for {spec}."
            job, events, want = turn(st["a"], prompt, [], model=model, endpoint=endpoint, extra={"spec": spec})
            fin = final_of(events).get("responseMessage", {})
            thoughts = "".join(p.get("think", "") for p in fin.get("content") or []
                               if isinstance(p, dict) and p.get("type") == "think")
            reqs = requests_for(prompt)
            sent = [(r.get("model"), r.get("enableThinking"), r.get("reasoningEffort"), r.get("enableSearch"),
                     r.get("searchStrategy")) for r in reqs]
            good = (text_of(fin) == want and sent == [(model, thinking, EFFORT[spec], True, SEARCH_STRATEGY)]
                    and (THINKING in thoughts if thinking else not thoughts) and fin.get("sender") == LABELS[spec])
            ok &= good
            st["lineup"].append(prompt)
            results.append(f"{spec}: sent={sent} max_tokens={[r.get('maxTokens') for r in reqs]} "
                           f"reply_ok={text_of(fin) == want} thinking_shown={bool(thoughts)} sender={fin.get('sender')}")
        return ok, "; ".join(results)
    check("M41", "each spec reaches its model with its endpoint's thinking flag and depth (Lite none, Plus medium, Pro "
          "high) and with Qwen Cloud's web search (turbo, #135); Plus and Pro stream a thinking block, the reply text "
          "stays exact and is labelled with the spec name", spec_turns)

    def titles_on_fast_model():
        # A title call quotes its chat's first message as "User: <text>" (LibreChat's convo template).
        quoted = {sha8(f"User: {p}") for p in st.get("lineup", [])}
        deadline, titles = time.time() + 30, []
        while time.time() < deadline:
            titles = [r for r in mock_requests() if r.get("event") == "chat.completions"
                      and quoted & set(r.get("allLines", []))]
            if len(titles) >= len(LINEUP):
                break
            time.sleep(2)
        seen = sorted({(r.get("model"), r.get("enableThinking"), r.get("enableSearch")) for r in titles},
                      key=str)
        # #169: the title call carries the endpoints' title instruction (the user's language), not the English default.
        wanted = {sha8(line.strip()) for line in spec_instructions("title_prompt", "titlePrompt").splitlines()
                  if line.strip() and "{convo}" not in line}
        prompted = sum(wanted <= set(r.get("allLines", [])) for r in titles)
        return (len(titles) == len(LINEUP) and seen == [("qwen3.8-flash", False, None)] and prompted == len(titles),
                f"titles={len(titles)} sent={seen} with_title_prompt={prompted}")
    check("M42", "conversation titles of all three specs use qwen3.8-flash without thinking or search (titleEndpoint "
          "«Qwen Tasks», #135) and carry the title instruction in the user's language (#169)",
          titles_on_fast_model)

    def legacy_rejected():
        prompt = "Synthetic request for the legacy qwen-plus alias."
        status, ack = start_chat(st["a"], prompt, model="qwen-plus", endpoint="Qwen")
        events = read_stream(st["a"], ack)[1] if status == 200 and isinstance(ack, dict) and "streamId" in ack else []
        return not requests_for(prompt), f"start HTTP {status}; provider requests={len(requests_for(prompt))}"
    check("M43", "a model outside the lineup (legacy qwen-plus) never reaches the provider", legacy_rejected)

    def no_qwen_key_leak():
        _, raw = api("GET", "/api/endpoints", st["a"])
        eps = json.loads(raw)
        return (all(e in eps for _, e, _, _ in LINEUP) and "mock-llm:" not in raw and "QWEN_API_KEY" not in raw,
                f"endpoints={sorted(eps)}")
    check("M44", "/api/endpoints lists the three Qwen Cloud endpoints without base URL or key placeholder",
          no_qwen_key_leak)

    def retired_refused():
        results, ok = [], True
        for endpoint, model in RETIRED:
            prompt = f"Synthetic request for the retired {model}."
            status, ack = start_chat(st["a"], prompt, model=model, endpoint=endpoint)
            if status == 200 and isinstance(ack, dict) and "streamId" in ack:
                read_stream(st["a"], ack)
            reached = len(requests_for(prompt))
            ok &= reached == 0
            results.append(f"{endpoint}/{model}: start HTTP {status} {str(ack)[:90]}; provider requests={reached}")
        return ok, "; ".join(results)
    check("M66", "the models of the previous lineup (qwen3.7-plus, qwen3.8-max on the removed «Qwen Max» endpoint) "
          "never reach the provider (#131)", retired_refused)

    def effort_locked():
        results, ok = [], True
        for spec, endpoint, model, thinking in LINEUP:
            prompt = f"Synthetic reasoning-effort override for {spec}."
            _, events, want = turn(st["a"], prompt, [], model=model, endpoint=endpoint,
                                   extra={"spec": spec, "reasoning_effort": "low", "enable_thinking": not thinking})
            fin = final_of(events).get("responseMessage", {})
            sent = [(r.get("enableThinking"), r.get("reasoningEffort")) for r in requests_for(prompt)]
            ok &= text_of(fin) == want and sent == [(thinking, EFFORT[spec])]
            results.append(f"{spec}: sent={sent}")
        return ok, "; ".join(results)
    check("M67", "the parameters panel cannot change thinking: a request asking for another effort (and the opposite "
          "thinking flag) is still sent with the endpoint's values (#131)", effort_locked)

    def search_locked():
        results, ok = [], True
        for spec, endpoint, model, _ in LINEUP:
            prompt = f"Synthetic search override for {spec}."
            _, events, want = turn(st["a"], prompt, [], model=model, endpoint=endpoint,
                                   extra={"spec": spec, "enable_search": False,
                                          "search_options": {"search_strategy": "agent"}})
            fin = final_of(events).get("responseMessage", {})
            sent = [(r.get("enableSearch"), r.get("searchStrategy")) for r in requests_for(prompt)]
            ok &= text_of(fin) == want and sent == [(True, SEARCH_STRATEGY)]
            results.append(f"{spec}: sent={sent}")
        return ok, "; ".join(results)
    check("M69", "web search is set by the server: a request asking to switch it off or for another strategy is still "
          "sent with search on and the turbo strategy (#135)", search_locked)

    def openai_switches_dropped():
        results, ok = [], True
        for spec, endpoint, model, _ in LINEUP:
            prompt = f"Synthetic parameters-panel check for {spec}."
            _, events, want = turn(st["a"], prompt, [], model=model, endpoint=endpoint,
                                   extra={"spec": spec, "web_search": True, "useResponsesApi": True})
            fin = final_of(events).get("responseMessage", {})
            sent = [r.get("model") for r in requests_for(prompt)]
            ok &= text_of(fin) == want and sent == [model]
            results.append(f"{spec}: reply_ok={text_of(fin) == want} chat_completions={sent}")
        return ok, "; ".join(results)
    check("M48", "the parameters panel's OpenAI-only switches (web search, Responses API) are dropped on every Qwen "
          "Cloud endpoint: the turn still goes to chat completions and gets the exact reply (#120)",
          openai_switches_dropped)

    def twins_without_search():
        results, ok = [], True
        web, noweb = instruction_lines("instructions"), instruction_lines("instructions_noweb")
        for twin, endpoint, visible in NOWEB:
            _, _, model, thinking = next(item for item in LINEUP if item[0] == visible)
            prompt = f"Synthetic no-search check for {twin}."
            # A request asking for search anyway, in artifacts mode as the web client sends it.
            _, events, want = turn(st["a"], prompt, [], model=model, endpoint=endpoint,
                                   extra={"spec": twin, "enable_search": True,
                                          "search_options": {"search_strategy": "agent"},
                                          "ephemeralAgent": {"artifacts": "custom"}})
            fin = final_of(events).get("responseMessage", {})
            thoughts = "".join(p.get("think", "") for p in fin.get("content") or []
                               if isinstance(p, dict) and p.get("type") == "think")
            reqs = requests_for(prompt)
            sent = [(r.get("model"), r.get("enableThinking"), r.get("reasoningEffort"), r.get("enableSearch"),
                     r.get("searchStrategy")) for r in reqs]
            lines = {d for r in reqs for d in r.get("systemLines", [])}
            tools = all(r.get("toolNames") == [] and r.get("artifactPrompt") for r in reqs)
            good = (text_of(fin) == want and sent == [(model, thinking, EFFORT[visible], None, None)]
                    and (THINKING in thoughts if thinking else not thoughts) and fin.get("sender") == LABELS[visible]
                    and (noweb - web) <= lines and not (web - noweb) & lines and tools)
            ok &= good
            results.append(f"{twin}: sent={sent} noweb_instructions={(noweb - web) <= lines} "
                           f"web_lines={len((web - noweb) & lines)} tools_and_artifacts={tools} sender={fin.get('sender')}")
        return ok, "; ".join(results)
    check("M73", "each hidden no-search twin (#138) reaches its spec's model with the same thinking and depth, never "
          "with search (not even when the request asks for it), with the instructions that say search is off and "
          "the artifact format, no tool (#167), and is labelled with the spec name", twins_without_search)

    def switch_in_place():
        twin, twin_endpoint, visible = NOWEB[0]
        _, endpoint, model, _ = next(item for item in LINEUP if item[0] == visible)
        history, convos, kw, sent, replies = [], set(), {}, [], []
        for n, (spec, ep) in enumerate([(visible, endpoint), (twin, twin_endpoint), (visible, endpoint)], 1):
            prompt = f"Synthetic internet switch, turn {n}."
            job, events, want = turn(st["a"], prompt, history, model=model, endpoint=ep, extra={"spec": spec}, **kw)
            fin = final_of(events)
            replies.append(text_of(fin.get("responseMessage", {})) == want)
            convo = fin.get("conversation", {}).get("conversationId") or job.get("conversationId")
            convos.add(convo)
            kw = {"convo": convo, "parent": fin.get("responseMessage", {}).get("messageId")}
            history.append(prompt)
            sent += [(r.get("enableSearch"), r.get("userTurns")) for r in requests_for(prompt)]
        _, saved = messages(st["a"], kw["convo"])
        return (all(replies) and len(convos) == 1 and sent == [(True, 1), (None, 2), (True, 3)] and len(saved) == 6,
                f"replies={replies} convos={len(convos)} sent={sent} saved={len(saved)}")
    check("M74", "the internet switch works inside one chat: search on, off (twin), on again; each turn carries the "
          "whole history and the chat keeps all six messages (#138)", switch_in_place)

    def twins_bound():
        results, ok = [], True
        for spec, endpoint in [(NOWEB[0][0], LINEUP[0][1]), (LINEUP[0][0], NOWEB[0][1])]:
            prompt = f"Synthetic spec on another endpoint: {spec} on {endpoint}."
            status, ack = start_chat(st["a"], prompt, model=LINEUP[0][2], endpoint=endpoint, extra={"spec": spec})
            if status == 200 and isinstance(ack, dict) and "streamId" in ack:
                read_stream(st["a"], ack)
            reached = len(requests_for(prompt))
            ok &= reached == 0
            results.append(f"{spec}@{endpoint}: start HTTP {status} {str(ack)[:80]}; provider requests={reached}")
        return ok, "; ".join(results)
    check("M75", "a spec is bound to its own endpoint: a twin on the search endpoint, or a spec on its twin's endpoint, "
          "never reaches the provider (the server refuses the mismatch, #138)", twins_bound)

    def simple_shell():
        _, raw = api("GET", "/api/config", st["a"])
        cfg = json.loads(raw)
        ui, specs = cfg.get("interface", {}), cfg.get("modelSpecs", {}).get("list", [])
        bad = [f"interface.{k}={ui.get(k)!r}" for k in HIDDEN_UI if ui.get(k) is not False]
        if ui.get("customWelcome") != WELCOME:
            bad.append(f"customWelcome={ui.get('customWelcome')!r}")
        for s in specs:
            # Home page like ChatGPT/Claude (#108): only the greeting and the composer, no line or starter cards.
            if s.get("group") or s.get("conversation_starters") or s.get("preset", {}).get("greeting"):
                bad.append(f"{s.get('name')}: group={s.get('group')!r} starters={s.get('conversation_starters')!r} "
                           f"greeting={s.get('preset', {}).get('greeting')!r}")
        for k in ("parameters", "multiConvo", "contextUsage"):  # #108; compare and context gauge #125
            if ui.get(k) is not True:
                bad.append(f"interface.{k}={ui.get(k)!r}")
        return not bad and len(specs) == len(LINEUP), "; ".join(bad) or f"specs={len(specs)}"
    check("M45", "home page (#87, #108, #125): Arabic welcome, flat specs without starter cards or a line under the "
          "greeting, presets hidden; parameters panel, compare and context gauge on", simple_shell)


def usage(st: dict) -> None:
    def report():
        # The lineup turns above (M41, M73) reached all six chat endpoints; the report must count each by mode, price
        # both models from the list-price file, list user A, and print no chat text (it reads messages.endpoint only).
        out = run(str(harness.ROOT / "scripts/operations/usage-report.sh"), ctr("mongodb"), "--by-user", "--json")
        if out.returncode != 0:
            return False, out.stderr[-300:]
        rep = json.loads(out.stdout)["report"]
        month = time.strftime("%Y-%m", time.gmtime())
        modes = {k.split(" | ", 1)[1]: v for k, v in rep["modes"].items() if k.startswith(month)}
        want = [f"{m} · {w}" for m in ("سريع / Fast", "متأنٍّ / Careful", "عميق / Deep")
                for w in ("internet", "no internet")]
        missing = [m for m in want if modes.get(m, {}).get("calls", 0) < 1 or not modes[m]["priced"]]
        listed = any(k.endswith(st["users"]["a"]) for k in rep["users"])
        leaked = [p for p in st.get("lineup", []) if p in out.stdout]
        return (not missing and listed and not leaked,
                f"missing_or_unpriced={missing} user_a_listed={listed} chat_text_printed={len(leaked)}")
    check("M91", "usage-report.sh (#211) counts the lineup's calls per mode with and without internet, prices both "
          "models from the list-price file, lists users, and prints no chat text", report)


def restart(st: dict) -> None:
    users, pw = st["users"], st["pw"]
    restarted = dc("restart", "librechat")
    check("M19", "LibreChat restarts and becomes healthy again (volumes kept)",
          lambda: (restarted.returncode == 0 and wait_healthy()[0], restarted.stderr))

    def reopen():
        status, body = login(users["a"], pw["a"])
        if status != 200:
            return False, f"login HTTP {status}"
        st["a"] = body["token"]
        # The first page holds 25 chats; user A has more by now (M48), so ask for the largest page.
        _, raw = api("GET", "/api/convos?sortBy=updatedAt&sortDirection=desc&limit=100", st["a"])
        ids = [c["conversationId"] for c in json.loads(raw)["conversations"]]
        _, saved = messages(st["a"], st["en"]["convo"])
        t1, t2 = st["en"]["user_texts"]
        prompt = "Third synthetic question after the restart."
        _, events, want = turn(st["a"], prompt, [t1, t2], convo=st["en"]["convo"], parent=st["en"]["assistant"])
        got = text_of(final_of(events).get("responseMessage", {}))
        return (set(st["a_convos"]) <= set(ids) and len(saved) == 4 and got == want and "Turn 3" in got,
                f"convos {len(st['a_convos'])}->{len(ids)} saved={len(saved)} got={got!r}")
    check("M20", "after restart: conversations reopen with full history and the chat continues (Turn 3)", reopen)


def leaks(st: dict) -> None:
    def no_leaks():
        values = [env_value(k) for k in ("CREDS_KEY", "CREDS_IV", "JWT_SECRET", "JWT_REFRESH_SECRET",
                                         "MONGO_ROOT_PASSWORD", "MONGO_APP_PASSWORD", "MEILI_MASTER_KEY",
                                         "MOCK_LLM_API_KEY")]
        values += list(st["pw"].values())
        logs = dc("logs").stdout + dc("logs").stderr
        in_logs = sum(v in logs for v in values)
        in_api = sum(v in body for body in harness.responses for v in values)
        js = ("const k = process.env.K; let n = 0; for (const c of db.getCollectionNames()) "
              "{ if (JSON.stringify(db.getCollection(c).find().toArray()).includes(k)) n++; } print(n)")
        mongo = run("docker", "exec", "-e", "K", ctr("mongodb"), "sh", "-c",
                    'mongosh --quiet --norc "mongodb://127.0.0.1:27017/$MONGO_APP_DATABASE" -u "$MONGO_APP_USERNAME" '
                    '-p "$MONGO_APP_PASSWORD" --authenticationDatabase "$MONGO_APP_DATABASE" --eval "$0"', js,
                    env={**os.environ, "K": st["key"]}).stdout.strip()
        prompt_in_mock_log = st["ar"]["prompt"] in dc("logs", "mock-llm").stdout
        return (in_logs == 0 and in_api == 0 and mongo == "0" and not prompt_in_mock_log,
                f"logs={in_logs} api={in_api} mongo_collections_with_key={mongo} prompt_in_mock_log={prompt_in_mock_log}")
    check("M21", "no secret (stack secrets, mock key, passwords) in logs, API responses or MongoDB", no_leaks)
