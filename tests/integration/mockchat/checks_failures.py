"""Provider-failure checks (#39): HTTP 5xx/429/401/404 and timeouts end quickly with a stored, generic error
(M28–M32), a reply that stops streaming ends after the configured idle limit (M86), the conversation continues
afterwards (M33) and Stop during the retry backoff is immediate (M34)."""

from __future__ import annotations

import json
import re
import threading
import time

from .client import api, error_of, final_of, messages, read_stream, requests_for, start_chat, text_of, turn
from .harness import CANARY, ENDPOINT, RETRY, ROOT, check, log

# Stream idle limit of every model call (librechat.yaml `endpoints.agents.modelResponseBodyTimeoutMs`, #39).
BODY_TIMEOUT_S = int(re.search(r"^    modelResponseBodyTimeoutMs: (\d+)$", (ROOT / "infrastructure/common/librechat.yaml")
                               .read_text(encoding="utf-8"), re.M).group(1)) / 1000


def provider_failures(st: dict) -> None:
    def failure(model, kind, attempts, max_s, endpoint=ENDPOINT, min_s=0.0):
        def run_check():
            prompt = f"Synthetic failure probe: {model}."
            t0 = time.monotonic()
            status, job = start_chat(st["a"], prompt, model=model, endpoint=endpoint)
            if status != 200 or not isinstance(job, dict):
                return False, f"start HTTP {status}: {str(job)[:200]}"
            _, events = read_stream(st["a"], job, timeout=max(120, max_s + 30))
            took = time.monotonic() - t0
            convo = job["conversationId"]
            err, raw = error_of(st["a"], convo)
            st.setdefault("failed", {})[model] = {"convo": convo, "prompt": prompt,
                                                  "reply": final_of(events).get("responseMessage", {}).get("messageId")}
            stream = json.dumps(events, ensure_ascii=False)
            n = len(requests_for(prompt))
            ok = (kind in err and CANARY not in err + raw + stream and n == attempts and min_s <= took <= max_s
                  and api("GET", "/health")[1] == "OK")
            log(f"#     {model}: {took:.1f} s, {n} provider attempt(s), stored error: {err[:160]!r}")
            return ok, f"took={took:.1f}s attempts={n} error={err[:200]!r} canary_leaked={CANARY in err + raw + stream}"
        return run_check
    check("M28", "HTTP 503: retried once, stored as upstream error with status in seconds; no provider text shown",
          failure("baseer-mock-5xx", '"status":503', 2, 15))
    check("M29", "HTTP 429 (no Retry-After): not retried, stored as rate-limit error",
          failure("baseer-mock-429", "model_rate_limit", 1, 10))
    check("M30", "HTTP 401 from the provider: not retried, stored as upstream error with status; key not shown",
          failure("baseer-mock-401", '"status":401', 1, 10))
    check("M31", "HTTP 404 model_not_found: stored as model-not-found error", failure("baseer-mock-gone", "model_not_found",
                                                                                         1, 10))
    check("M32", "provider never answers: each attempt times out after 8 s, 2 attempts, then a stored error",
          failure("baseer-mock-hang", "upstream_model_error", 2, 30, min_s=16))
    check("M86", f"a reply that stops streaming ends after the {BODY_TIMEOUT_S:.0f} s idle limit of librechat.yaml (not "
          "the 15 min default), once, stored as a stalled-stream error (#39)",
          failure("baseer-mock-stall", "model_stream_stalled", 1, BODY_TIMEOUT_S + 15, min_s=BODY_TIMEOUT_S))

    def continue_after_error():
        f = st["failed"]["baseer-mock-5xx"]
        prompt = "Synthetic follow-up after a provider error."
        _, events, _ = turn(st["a"], prompt, [], convo=f["convo"], parent=f["reply"])
        got = text_of(final_of(events).get("responseMessage", {}))
        status, saved = messages(st["a"], f["convo"])
        kinds = ["user" if m.get("isCreatedByUser") else ("error" if any(p.get("type") == "error" for p in
                 m.get("content") or []) else "reply") for m in saved]
        return (got.startswith("Deterministic mock reply.") and kinds == ["user", "error", "user", "reply"],
                f"got={got!r} stored={kinds}")
    check("M33", "after an error the conversation keeps the failed turn and continues with the next message",
          continue_after_error)

    def stop_during_retry():
        prompt = "Synthetic Stop while the client waits between retries."
        t0 = time.monotonic()
        status, job = start_chat(st["a"], prompt, model="baseer-mock-5xx", endpoint=RETRY)
        if status != 200 or not isinstance(job, dict):
            return False, f"start HTTP {status}"
        out: dict = {}
        reader = threading.Thread(target=lambda: out.update(events=read_stream(st["a"], job, timeout=90)[1]))
        reader.start()
        while not requests_for(prompt) and time.monotonic() - t0 < 20:
            time.sleep(0.2)
        time.sleep(0.3)  # inside the first backoff window (1–2 s)
        at_stop = len(requests_for(prompt))
        stop = api("POST", "/api/agents/chat/abort", st["a"], {"streamId": job["streamId"],
                   "conversationId": job["conversationId"], "generationCreatedAt": job["generationCreatedAt"]})[0]
        reader.join(30)
        stopped_after = time.monotonic() - t0
        time.sleep(12)  # without the Stop, attempts 2 and 3 would arrive within ~6 s
        later = len(requests_for(prompt))
        fin = final_of(out.get("events", []))
        log(f"#     Stop during retry: final after {stopped_after:.1f} s, provider attempts {at_stop} -> {later}")
        return (stop == 200 and fin.get("aborted") is True and at_stop == 1 and later == at_stop and stopped_after < 10,
                f"stop={stop} aborted={fin.get('aborted')} after={stopped_after:.1f}s attempts {at_stop}->{later}")
    check("M34", "Stop while waiting between retries ends the turn at once and no further provider request is made",
          stop_during_retry)
