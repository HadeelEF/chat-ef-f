"""LibreChat HTTP/SSE client used by the checks: the same calls the v0.8.8 web client makes."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from . import harness
from .harness import ADMIN_MCP, ALLOWED, BASE, DENIED, ENDPOINT, MODELS, PUBLISH, ZERO, ctr, dc, run


def api(method: str, path: str, token: str | None = None, body: dict | None = None) -> tuple[int, str]:
    req = urllib.request.Request(BASE + path, method=method,
                                 data=None if body is None else json.dumps(body).encode("utf-8"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with harness.opener.open(req, timeout=30) as resp:
            status, text = resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        status, text = err.code, err.read().decode("utf-8", "replace")
    harness.responses.append(text)
    return status, text


def login(email: str, password: str) -> tuple[int, dict]:
    status, text = api("POST", "/api/auth/login", body={"email": email, "password": password})
    try:
        return status, json.loads(text)
    except ValueError:
        return status, {}


def create_user(email: str, name: str, username: str, password: str) -> subprocess.CompletedProcess:
    return run("docker", "exec", "-i", ctr("librechat"), "npm", "run", "--silent", "create-user", "--",
               email, name, username, "--email-verified=true", inp=password + "\n")


def expected_reply(user_texts: list[str]) -> str:
    """Mirror of replyFor() in mock-llm/mock-llm.mjs."""
    last = user_texts[-1]
    digest = hashlib.sha256(last.encode("utf-8")).hexdigest()[:8]
    if re.search("[؀-ۿ]", last):
        return f"رد اختباري ثابت من النموذج الوهمي. الدور {len(user_texts)}. المعرّف {digest}."
    return f"Deterministic mock reply. Turn {len(user_texts)}. ID {digest}."


def text_of(message: dict) -> str:
    parts = message.get("content") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text")
    return text or message.get("text") or ""


def start_chat(token: str, text: str, model: str = MODELS[0], endpoint: str = ENDPOINT,
               convo: str | None = None, parent: str = ZERO, extra: dict | None = None) -> tuple[int, dict | str]:
    """POST the turn exactly as the web client does (captured from the v0.8.8 UI); `extra` adds raw body fields."""
    body = {"text": text, "sender": "User", "isCreatedByUser": True, "parentMessageId": parent,
            "messageId": str(uuid.uuid4()), "endpoint": endpoint, "endpointType": "custom", "model": model,
            "isTemporary": False, "isRegenerate": False, "isContinued": False,
            "clientRequestId": str(uuid.uuid4()), "generationProtocolVersion": 2, **(extra or {})}
    if convo:
        body["conversationId"] = convo
    status, raw = api("POST", f"/api/agents/chat/{urllib.parse.quote(endpoint)}", token, body)
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw  # an SSE error frame instead of the start acknowledgement


def read_stream(token: str, job: dict, on_delta=None, timeout: int = 60) -> tuple[int, list[dict]]:
    """Subscribe to the job's SSE stream; returns (HTTP status, events) up to the final/error event, or up to
    `on_pending_action` when the run pauses for the user (a clarifying question, #129: the stream stays open)."""
    url = (f"{BASE}/api/agents/chat/stream/{job['streamId']}"
           f"?generationCreatedAt={job['generationCreatedAt']}&generationProtocolVersion=2")
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        resp = harness.opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as err:
        harness.responses.append(err.read().decode("utf-8", "replace"))
        return err.code, []
    events, name, data, raw = [], "message", "", []
    with resp:
        for line_bytes in resp:
            line = line_bytes.decode("utf-8").rstrip("\n")
            raw.append(line)
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data += line[5:].strip()
            elif line == "" and data:
                event = {"_name": name, "_t": time.monotonic(), **json.loads(data)}
                events.append(event)
                if on_delta and event.get("event") == "on_message_delta":
                    on_delta(events)
                if event.get("final") or name == "error" or event.get("event") == "on_pending_action":
                    break
                name, data = "message", ""
    harness.responses.append("\n".join(raw))
    return resp.status, events


def deltas(events: list[dict]) -> list[str]:
    out = []
    for e in events:
        if e.get("event") == "on_message_delta":
            out += [p.get("text", "") for p in e["data"]["delta"].get("content", []) if p.get("type") == "text"]
    return out


def final_of(events: list[dict]) -> dict:
    return next((e for e in reversed(events) if e.get("final")), {})


def messages(token: str, convo: str) -> tuple[int, list[dict]]:
    status, text = api("GET", f"/api/messages/{convo}", token)
    try:
        return status, json.loads(text)
    except ValueError:
        return status, []


def mock_requests() -> list[dict]:
    lines = dc("logs", "--no-log-prefix", "mock-llm").stdout.splitlines()
    return [json.loads(line) for line in lines if line.startswith("{")]


def sha8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def requests_for(prompt: str) -> list[dict]:
    """Mock requests whose last user message is `prompt` (one per provider attempt)."""
    return [r for r in mock_requests() if r.get("event") == "chat.completions"
            and [d for d in r.get("digests", []) if d.startswith("user:")][-1:] == [f"user:{sha8(prompt)}"]]


def error_of(token: str, convo: str) -> tuple[str, str]:
    """(stored error text of the conversation's reply, raw /api/messages body)."""
    status, raw = api("GET", f"/api/messages/{convo}", token)
    saved = json.loads(raw) if status == 200 else []
    reply = next((m for m in saved if not m.get("isCreatedByUser")), {})
    return " ".join(p.get("error", "") for p in reply.get("content") or [] if p.get("type") == "error"), raw


def role(token: str, name: str) -> dict:
    status, raw = api("GET", f"/api/roles/{name}", token)
    return json.loads(raw).get("permissions", {}) if status == 200 else {}


def _joined(*maps: dict) -> dict:
    """Permission maps {type: [permission]} -> one map, the lists of a type shared by several maps joined."""
    out: dict = {}
    for m in maps:
        for t, ps in m.items():
            out[t] = out.get(t, []) + ps
    return out


def policy_violations(perms: dict, admin: bool = False) -> list[str]:
    denied, allowed = ((DENIED, _joined(ALLOWED, PUBLISH, ADMIN_MCP)) if admin
                       else (_joined(DENIED, PUBLISH, ADMIN_MCP), ALLOWED))
    bad = [f"{t}.{p}" for t, ps in denied.items() for p in ps if perms.get(t, {}).get(p) is not False]
    return bad + [f"{t}.{p}!" for t, ps in allowed.items() for p in ps if perms.get(t, {}).get(p) is not True]


def turn(token: str, prompt: str, history: list[str], **kw) -> tuple[dict, list[dict], str]:
    """Start a turn, read its stream and return (job, events, expected reply text)."""
    status, job = start_chat(token, prompt, **kw)
    if status != 200 or not isinstance(job, dict) or job.get("status") != "started":
        raise AssertionError(f"start HTTP {status}: {str(job)[:200]}")
    _, events = read_stream(token, job)
    return job, events, expected_reply(history + [prompt])
