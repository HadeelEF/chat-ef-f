"""LibreChat batch 2 checks (#129): clarifying questions with options, answer and skip (M57–M60), reasoning replayed
with the answer on thinking specs (M68, #131), the sensitive-data filter (M61), file reading and upload limits
(M62–M64) and long-chat summaries (M65). Since #167 the specs offer no question tool (Qwen Cloud's built-in search
stops when a request offers any tool); the question cards are checked where they remain, on a chat that asks for the
tool (`ephemeralAgent.ask_user_question`, as an agent with the tool does)."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
import uuid

from . import fixtures, harness
from .client import (api, final_of, login, messages, mock_requests, read_stream, requests_for, sha8, start_chat,
                     text_of, turn)
from .harness import BASE, LINEUP, MODELS, ROOT, check, ctr, run

# Mirrors of mock-llm/mock-llm.mjs (#129).
ASK_BATCH, ASK_ONE = "اكتب لي خطاباً", "رتّب لي اجتماعاً"
ANSWERED = "شكراً، وصلتني إجابتك:"
SKIPPED = "تخطّيت السؤال، فسأكمل بافتراض عام: خطاب رسمي إلى جهة حكومية."
SUMMARY = "الهدف:\nملخص اصطناعي ثابت للمحادثة السابقة. SYNTH-SUMMARY"
DECLINED = "The user chose not to answer this question."  # what the web client's Skip sends (utils/approval.ts)
LABEL_ID = "رقم هوية وطنية أو إقامة"  # label of the sa_national_id pattern in librechat.yaml
# Synthetic only: numbers in the documented formats, made up for the test.
SENSITIVE = [("هذا رقم هوية اصطناعي للتجربة 1012345678 فقط", LABEL_ID),
             ("رقم إقامة بأرقام عربية ٢٠١٢٣٤٥٦٧٨ للتجربة", LABEL_ID),
             ("الآيبان الاصطناعي SA03 8000 0000 6080 1016 7519 للتجربة", "رقم آيبان سعودي"),
             ("مفتاحي sk-abcdefghijklmnopqrstuvwxyz123456 للتجربة", "مفتاح API"),
             ("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp", "رمز دخول (Bearer)")]
ORDINARY = ["To the bearer of this letter, greetings from the synthetic fund.",
            "كم يساوي 2026 × 12؟ والهاتف 0501234567 والمبلغ 1,500,000,000 ريال"]


def spec_instructions(anchor: str = "instructions", key: str = "promptPrefix") -> str:
    """The specs' `promptPrefix` (YAML literal block under `&instructions`, #135; `&instructions_noweb` for the
    no-search twins, #138), or another anchored literal block such as the endpoints' `titlePrompt` (#169), read
    without a YAML library."""
    lines = (ROOT / "infrastructure/common/librechat.yaml").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if f"{key}: &{anchor} |-" in line)
    indent = len(lines[start]) - len(lines[start].lstrip())
    block_indent = len(lines[start + 1]) - len(lines[start + 1].lstrip())
    body = []
    for line in lines[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line[block_indent:] if line.strip() else "")
    return "\n".join(body).rstrip("\n")


def instruction_lines(anchor: str) -> set[str]:
    """Digests of the instructions' lines, as the mock logs them (`systemLines`)."""
    return {sha8(line.strip()) for line in spec_instructions(anchor).splitlines() if line.strip()}


def instructions_head() -> str:
    """Digest of how the instructions start: the mock logs the first 64 characters of each system message."""
    return sha8(spec_instructions()[:64])


# A chat with the question tool (#167: no spec offers it; an agent with the tool does).
ASK_TOOL = {"ask_user_question": True}


def ask(token: str, prompt: str, spec: str = "baseer-lite") -> tuple[dict, list[dict], dict]:
    """Start a turn that the mock answers with a question; returns (job, events, the on_pending_action data)."""
    _, endpoint, model, _ = next(item for item in LINEUP if item[0] == spec)
    status, job = start_chat(token, prompt, model=model, endpoint=endpoint,
                             extra={"spec": spec, "ephemeralAgent": ASK_TOOL})
    if status != 200 or not isinstance(job, dict):
        raise AssertionError(f"start HTTP {status}: {str(job)[:200]}")
    _, events = read_stream(token, job)
    pending = next((e["data"] for e in events if e.get("event") == "on_pending_action"), {})
    return {**job, "spec": spec, "endpoint": endpoint, "model": model}, events, pending


def resume(token: str, job: dict, pending: dict, answers: dict) -> tuple[int, dict | str]:
    """POST the answers exactly as the web client does (captured from the v0.8.8 UI)."""
    body = {"conversationId": job["conversationId"], "generationCreatedAt": job["generationCreatedAt"],
            "endpoint": job["endpoint"], "endpointType": "custom", "model": job["model"], "spec": job["spec"],
            "ephemeralAgent": {"mcp": [], "web_search": False, "file_search": False, "execute_code": False,
                               "memory": False, "artifacts": "custom", **ASK_TOOL},
            "actionId": pending.get("actionId"), "answers": answers, "generationProtocolVersion": 2}
    status, raw = api("POST", "/api/agents/chat/resume", token, body)
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw


def questions_of(pending: dict) -> list[str]:
    payload = pending.get("payload") or {}
    items = payload.get("questions") or ([payload] if payload.get("question") else [])
    return [q.get("question", "") for q in items]


def upload(token: str, name: str, data: bytes, mime: str) -> tuple[int, dict]:
    """Upload a file with the fields the web client's paperclip sends for a chat (useFileHandling.ts)."""
    boundary = uuid.uuid4().hex
    fields = {"endpoint": "Qwen", "endpointType": "custom", "file_id": str(uuid.uuid4()), "message_file": "true"}
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in
             fields.items()]
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                 f"Content-Type: {mime}\r\n\r\n".encode() + data + b"\r\n")
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(BASE + "/api/files", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with harness.opener.open(req, timeout=60) as resp:
            status, text = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status, text = err.code, err.read().decode("utf-8", "replace")
    harness.responses.append(text)
    try:
        return status, json.loads(text)
    except ValueError:
        return status, {"raw": text[:200]}


def mongo_count(js: str) -> str:
    return run("docker", "exec", ctr("mongodb"), "sh", "-c",
               'mongosh --quiet --norc "mongodb://127.0.0.1:27017/$MONGO_APP_DATABASE" -u "$MONGO_APP_USERNAME" '
               '-p "$MONGO_APP_PASSWORD" --authenticationDatabase "$MONGO_APP_DATABASE" --eval "$0"', js).stdout.strip()


def batch2(st: dict) -> None:
    for who, email in (("a", st["users"]["a"]), ("b", st["users"]["b"])):
        status, body = login(email, st["pw"][who])
        if status == 200:
            st[who] = body["token"]

    def tool_offered():
        results, ok = [], True
        for spec, endpoint, model, _ in LINEUP:
            prompt = f"Synthetic question-tool check for {spec}."
            turn(st["a"], prompt, [], model=model, endpoint=endpoint,
                 extra={"spec": spec, "ephemeralAgent": {"artifacts": "custom"}})
            names = sorted({n for r in requests_for(prompt) for n in r.get("toolNames", [])})
            ok &= names == []
            results.append(f"{spec}={names}")
        asked = "Synthetic question-tool check with the tool."
        turn(st["a"], asked, [], extra={"ephemeralAgent": ASK_TOOL})
        asked_names = sorted({n for r in requests_for(asked) for n in r.get("toolNames", [])})
        return ok and "ask_user_question" in asked_names, "; ".join(results) + f"; with the tool={asked_names}"
    check("M57", "the three specs offer the model no tool at all, so Qwen Cloud's built-in search stays on (owner "
          "decision #167); a chat that asks for the question tool still gets it", tool_offered)

    def artifacts_and_instructions():
        status, raw = api("GET", "/api/config", st["a"])
        listed = (json.loads(raw).get("modelSpecs") or {}).get("list", []) if status == 200 else []
        modes = {s.get("name"): s.get("artifacts") for s in listed}
        results = [f"modes={sorted(set(modes.values()))}"]
        ok = set(modes.values()) == {"custom"} and len(modes) == len(LINEUP)
        for spec, endpoint, model, _ in LINEUP:
            prompt = f"Synthetic artifacts-mode check for {spec}."
            # The web client sends the spec's artifacts mode with every turn (useApplyModelSpecAgents, patch 0029:
            # the spec alone decides it); the API test sends what the client sends.
            turn(st["a"], prompt, [], model=model, endpoint=endpoint,
                 extra={"spec": spec, "ephemeralAgent": {"artifacts": modes.get(spec, "custom")}})
            reqs = requests_for(prompt)
            heads = [instructions_head() in r.get("systemHeads", []) for r in reqs]
            arts = [r.get("artifactPrompt") for r in reqs]
            upstream = [r.get("upstreamArtifactPrompt") for r in reqs]
            ok &= heads == [True] and arts == [True] and upstream == [False]
            results.append(f"{spec}: instructions_first={heads} artifact_format={arts} upstream_english={upstream}")
        return ok, "; ".join(results)
    check("M72", "every spec runs in `custom` artifacts mode: its system message starts with the EF instructions "
          "(format, internet sources, artifacts with their format, questions) and LibreChat's English artifact "
          "instructions are not added (#135, #167)", artifacts_and_instructions)

    def answer_resumes():
        job, _, pending = ask(st["a"], f"{ASK_BATCH} للتجربة الآلية", spec="baseer-plus")
        asked = questions_of(pending)
        answers = {"recipient": "جهة حكومية", "tone": "نبرة ودّية ومختصرة"}
        status, ack = resume(st["a"], job, pending, answers)
        if status != 200 or not isinstance(ack, dict):
            return False, f"questions={asked} resume HTTP {status}: {str(ack)[:200]}"
        _, events = read_stream(st["a"], {"streamId": ack["streamId"], "generationCreatedAt": job["generationCreatedAt"]})
        reply = text_of(final_of(events).get("responseMessage", {}))
        want = f"{ANSWERED} {json.dumps({'answers': answers}, ensure_ascii=False, separators=(',', ':'))}"
        tool_turns = [r for r in mock_requests() if any(d.startswith("tool:") for d in r.get("digests", []))]
        instructed = instructions_head() in (tool_turns[-1].get("systemHeads", []) if tool_turns else [])
        _, saved = messages(st["a"], job["conversationId"])
        stored = json.dumps(saved, ensure_ascii=False)
        return (asked == ["لمن الخطاب؟", "ما نبرة الخطاب؟"] and reply == want and instructed
                and "نبرة ودّية ومختصرة" in stored,
                f"questions={asked} reply_ok={reply == want} instructions_sent={instructed} "
                f"answer_stored={'نبرة ودّية ومختصرة' in stored} reply={reply[:120]!r}")
    check("M58", "a two-question card pauses the reply (on_pending_action); an option plus a typed answer resume it, "
          "the model receives both answers and the specs' instructions, and the chat keeps them", answer_resumes)

    def skip_resumes():
        job, _, pending = ask(st["a"], f"{ASK_ONE} للتجربة الآلية")
        status, ack = resume(st["a"], job, pending, {"topics": DECLINED})
        if status != 200 or not isinstance(ack, dict):
            return False, f"resume HTTP {status}: {str(ack)[:200]}"
        _, events = read_stream(st["a"], {"streamId": ack["streamId"], "generationCreatedAt": job["generationCreatedAt"]})
        reply = text_of(final_of(events).get("responseMessage", {}))
        return reply == SKIPPED, f"questions={questions_of(pending)} reply={reply[:120]!r}"
    check("M59", "Skip: the model receives LibreChat's decline notice and goes on with an assumption", skip_resumes)

    def sensitive_answer():
        job, _, pending = ask(st["a"], f"{ASK_ONE} لاختبار الإجابة الحساسة")
        bad = "رقم هويتي الاصطناعي 1012345678"
        status, body = resume(st["a"], job, pending, {"topics": bad})
        refused = status == 400 and isinstance(body, dict) and body.get("error") == "content_filter_block"
        refused_result = json.dumps({"answers": {"topics": bad}}, ensure_ascii=False, separators=(",", ":"))
        reached = any(f"tool:{sha8(refused_result)}" in r.get("digests", []) for r in mock_requests())
        status2, ack = resume(st["a"], job, pending, {"topics": "الميزانية, المخاطر"})
        events = read_stream(st["a"], {"streamId": ack["streamId"], "generationCreatedAt": job["generationCreatedAt"]})[1] \
            if status2 == 200 and isinstance(ack, dict) else []
        reply = text_of(final_of(events).get("responseMessage", {}))
        return (refused and not reached and reply.startswith(ANSWERED) and "الميزانية, المخاطر" in reply,
                f"first HTTP {status} {str(body)[:120]} reached_model={reached} second HTTP {status2} reply={reply[:80]!r}")
    check("M60", "an answer with a synthetic ID number is refused (400 content_filter_block) before the model; the "
          "question stays open and a clean answer resumes it", sensitive_answer)

    def reasoning_replayed():
        results, ok = [], True
        for spec, _, _, thinking in LINEUP:
            prompt = f"{ASK_ONE} لاختبار إعادة خطوات التفكير ({spec})"
            job, _, pending = ask(st["a"], prompt, spec=spec)
            status, ack = resume(st["a"], job, pending, {"topics": "الميزانية"})
            if status != 200 or not isinstance(ack, dict):
                ok = False
                results.append(f"{spec}: resume HTTP {status}: {str(ack)[:120]}")
                continue
            _, events = read_stream(st["a"], {"streamId": ack["streamId"],
                                              "generationCreatedAt": job["generationCreatedAt"]})
            reply = text_of(final_of(events).get("responseMessage", {}))
            replayed = [r.get("replayedReasoning") for r in requests_for(prompt)
                        if any(d.startswith("tool:") for d in r.get("digests", []))]
            good = (reply.startswith(ANSWERED) and len(replayed) == 1
                    and (replayed[0] >= 1 if thinking else replayed[0] == 0))
            ok &= good
            results.append(f"{spec}: reply_ok={reply.startswith(ANSWERED)} reasoning_sent_back={replayed}")
        return ok, "; ".join(results)
    check("M68", "with thinking on (Plus, Pro), the model's reasoning goes back with the answer to its question, as Qwen "
          "Cloud asks for tool turns; Lite sends none (#131)", reasoning_replayed)

    def sensitive_messages():
        results, ok = [], True
        for text, label in SENSITIVE:
            status, body = start_chat(st["a"], text)
            message = body.get("message", "") if isinstance(body, dict) else str(body)
            good = status == 400 and f"contains a {label}." in message and not requests_for(text)
            ok &= good
            results.append(f"{label}:{status}{'' if good else ' BAD'}")
        for text in ORDINARY:
            _, events, want = turn(st["a"], text, [])
            good = text_of(final_of(events).get("responseMessage", {})) == want
            ok &= good
            results.append(f"ordinary:{'ok' if good else 'BAD'}")
        digits = "|".join(re.escape(x) for x in ("1012345678", "٢٠١٢٣٤٥٦٧٨", "SA03 8000", "sk-abcdefghij", "eyJhbGci"))
        stored = mongo_count(f"print(db.messages.countDocuments({{text: /{digits}/}}))")
        return ok and stored == "0", "; ".join(results) + f"; stored={stored}"
    check("M61", "sensitive data: a national ID / iqama number (Western or Arabic-Indic digits), a Saudi IBAN, an API "
          "key and a bearer token are refused before the model and not stored, naming what to remove; «bearer of "
          "this letter», a phone number and 1,500,000,000 pass", sensitive_messages)

    docs = [("synthetic.pdf", "application/pdf", fixtures.pdf(["تقرير اصطناعي عن مشروع تشجير.", "SYNTH-DOC-PDF"]),
             "SYNTH-DOC-PDF"),
            ("synthetic.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
             fixtures.docx(["مذكرة اصطناعية عن خطة الاستدامة.", "SYNTH-DOC-DOCX"]), "SYNTH-DOC-DOCX"),
            ("synthetic.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             fixtures.xlsx([["البند", "القيمة"], ["تكلفة اصطناعية", "1,250"], ["SYNTH-DOC-XLSX", "نعم"]]),
             "SYNTH-DOC-XLSX")]

    def files_read():
        results, ok = [], True
        for name, mime, data, marker in docs:
            status, file = upload(st["a"], name, data, mime)
            if status != 200:
                ok = False
                results.append(f"{name}: upload HTTP {status} {str(file)[:120]}")
                continue
            prompt = f"لخّص الملف المرفق {name} في سطرين."
            ref = {k: file.get(k) for k in ("file_id", "filepath", "filename", "type", "llmDeliveryPath")}
            before = len(mock_requests())
            turn(st["a"], prompt, [], model="qwen3.8-flash", endpoint="Qwen",
                 extra={"spec": "baseer-lite", "files": [ref]})
            # The file's text joins the user message, so the request is found by its marker, not by the prompt.
            markers = sorted({m for r in mock_requests()[before:] if r.get("stream") for m in r.get("markers", [])})
            good = file.get("llmDeliveryPath") == "text" and marker in markers
            ok &= good
            results.append(f"{name}: path={file.get('llmDeliveryPath')} markers={markers}")
        return ok, "; ".join(results)
    check("M62", "files: a synthetic PDF, Word and Excel file with Arabic text are sent as text (PDF too, not as a "
          "base64 file) and their text reaches the model", files_read)

    def files_refused():
        cases = [("sensitive.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                  fixtures.docx(["مذكرة فيها رقم هوية اصطناعي 1012345678.", "SYNTH-DOC-PII"])),
                 ("sensitive.pdf", "application/pdf", fixtures.pdf(["رقم إقامة اصطناعي 2012345678", "SYNTH-DOC-PIIPDF"])),
                 ("scan.pdf", "application/pdf", fixtures.image_only_pdf()),
                 ("big.pdf", "application/pdf", fixtures.pdf(["SYNTH-DOC-BIG"]) + b"%" + b"0" * (21 * 1024 * 1024))]
        got, since = {}, int(time.time() * 1000)
        for name, mime, data in cases:
            status, body = upload(st["a"], name, data, mime)
            got[name] = (status, body.get("error") or body.get("message") or body.get("raw", ""))
        filtered = all(got[n][0] == 400 and got[n][1] == "content_filter_block" for n in ("sensitive.docx", "sensitive.pdf"))
        scan = got["scan.pdf"][0] >= 400 and "No text found" in str(got["scan.pdf"][1])
        big = got["big.pdf"][0] >= 400
        markers = {m for r in mock_requests() for m in r.get("markers", [])}
        leaked = sorted(markers & {"SYNTH-DOC-PII", "SYNTH-DOC-PIIPDF", "SYNTH-DOC-BIG"})
        stored = mongo_count("print(db.files.countDocuments({filename: {$in: ['sensitive.docx', 'sensitive.pdf', "
                             f"'scan.pdf', 'big.pdf']}}, createdAt: {{$gte: new Date({since})}}}}))")
        return (filtered and scan and big and not leaked and stored == "0",
                f"{json.dumps(got, ensure_ascii=False)[:300]} leaked={leaked} stored={stored}")
    check("M63", "files refused before the model and not stored: Word and PDF with a synthetic ID number "
          "(content_filter_block), a scan with no text layer, a file over 20 MB", files_refused)

    def upload_limits():
        status, raw = api("GET", "/api/files/config", st["a"])
        cfg = json.loads(raw) if status == 200 else {}
        eps = cfg.get("endpoints", {})
        want = {"fileLimit": 10, "fileSizeLimit": 20, "totalSizeLimit": 50}
        limits = {k: {f: eps.get(k, {}).get(f) for f in want} for k in ("default", "agents")}
        pdf = cfg.get("defaultLLMDeliveryPath", {}).get("overrides", {}).get("application/pdf")
        return (all(v == want for v in limits.values()) and cfg.get("serverFileSizeLimit") == 20 and pdf == "text",
                f"limits={limits} server={cfg.get('serverFileSizeLimit')} pdf={pdf}")
    check("M64", "/api/files/config: 20 MB per file, 50 MB per message, 10 files, for `default` and for `agents` (the "
          "entry the Qwen endpoints take), PDFs as text (FR-007 AC-1)", upload_limits)

    def summaries():
        filler = " ".join(["فقرة اصطناعية طويلة لاختبار تلخيص المحادثات الطويلة."] * 45)
        convo, parent, before, final = None, harness.ZERO, len(mock_requests()), {}
        _, pro_endpoint, pro_model, _ = next(item for item in LINEUP if item[0] == "baseer-pro")
        for i in range(1, 4):
            status, job = start_chat(st["a"], f"سؤال {i}: {filler}", model=pro_model, endpoint=pro_endpoint,
                                     convo=convo, parent=parent, extra={"spec": "baseer-pro", "maxContextTokens": 3000})
            # 3,000 (was 2,000 until the live QA, #41): the instructions now take most of 2,000 tokens, leaving no room
            # for the summary itself; 3,000 still overflows on these turns, so the summary is written and carried.
            if status != 200 or not isinstance(job, dict):
                return False, f"turn {i}: start HTTP {status}: {str(job)[:200]}"
            final = final_of(read_stream(st["a"], job)[1])
            convo, parent = job["conversationId"], final.get("responseMessage", {}).get("messageId", parent)
        seen = mock_requests()[before:]
        # The summarizer's request is the only streamed one that does not open with the system message.
        writers = [(r.get("model"), r.get("enableThinking")) for r in seen
                   if r.get("stream") and not r.get("digests", ["system:"])[0].startswith("system:")]
        carried = [r.get("model") for r in seen if "SYNTH-SUMMARY" in r.get("markers", [])]
        _, saved = messages(st["a"], convo)
        parts = [p for m in saved for p in (m.get("content") or []) if isinstance(p, dict) and p.get("type") == "summary"]
        stored = json.dumps(parts, ensure_ascii=False)
        return (("qwen3.8-flash", False) in writers and pro_model in carried and "SYNTH-SUMMARY" in stored,
                f"summary writers={sorted(set(writers))} carried_by={sorted(set(carried))} stored_parts={len(parts)}")
    check("M65", "long chat («بصير برو», 3,000-token window): the overflow is summarized by qwen3.8-flash without "
          "thinking, using the Arabic prompt; the next request to the Pro model carries the summary, which is stored",
          summaries)

    def search_only_streamed():
        lineup = [r for r in mock_requests() if r.get("event") == "chat.completions"
                  and str(r.get("model", "")).startswith(("qwen", "deepseek"))]
        unstreamed = [r for r in lineup if not r.get("stream")]
        searching_unstreamed = [r for r in unstreamed if r.get("enableSearch")]
        streamed_search = [r for r in lineup if r.get("stream") and r.get("enableSearch")]
        return (not searching_unstreamed and len(unstreamed) > 0 and len(streamed_search) > 0,
                f"lineup calls={len(lineup)} unstreamed={len(unstreamed)} unstreamed_with_search="
                f"{len(searching_unstreamed)} streamed_with_search={len(streamed_search)}")
    check("M71", "Qwen Cloud searches only in streamed calls (#135): after the whole suite (chats, titles, memories, "
          "summaries), no unstreamed call asks for search, and streamed chat calls do", search_only_streamed)
