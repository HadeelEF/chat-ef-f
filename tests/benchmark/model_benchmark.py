#!/usr/bin/env python3
"""Replayable model benchmark for the three chat modes (سريع / متأنٍّ / عميق) with and without internet.

Synthetic scenarios (scenarios.json) are sent to the provider with the request the platform sends for each mode: the
model, `addParams` (thinking, its depth, Qwen Cloud's built-in search) and the spec's instructions, all read from
infrastructure/common/librechat.yaml, so a config change is benchmarked as merged. The LibreChat path itself (specs,
twins, streaming, Stop, history, permissions) is covered by tests/integration/mock_chat.py against a mock model.

Modes:
  --offline (default)  no network, no key: validates the scenarios and builds every request (deterministic; usable
                       as a mock check by Claude Code or Codex in any session).
  --live               calls Qwen Cloud (synthetic data only, OD-01 #5) and measures per scenario: time to the first
                       token and the whole reply, input/output/reasoning tokens, an estimated cost (list prices in
                       scripts/operations/qwen-list-prices.json), whether the provider searched, and the checks below.
                       Key: --key-file PATH (never on the command line or in output) or QWEN_API_KEY.
Search detection (Qwen's stream returns no search count): the same messages are sent once more without the search
parameters, unstreamed, with max_tokens=1, to count the input tokens without search; a streamed call that read more
than SEARCH_MARGIN extra input tokens searched. The difference is the search's input tokens.

Usage:  python3 tests/benchmark/model_benchmark.py [--offline | --live [--key-file F]] [--only ID[,ID]] [--out DIR]
        python3 tests/benchmark/model_benchmark.py --rescore DIR/results.jsonl   (checks again, no network)
Needs:  python3 and PyYAML (the validation venv: scripts/validate/requirements.txt). Exit 1 when a scenario or request
        is invalid (offline) or when the provider fails a call (live); check results are reported, not fatal.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import struct
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML missing: python3 -m venv .venv && . .venv/bin/activate && "
                     "python -m pip install --require-hashes -r scripts/validate/requirements.txt")

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "infrastructure/common/librechat.yaml"
SCENARIOS = Path(__file__).with_name("scenarios.json")
PRICES = ROOT / "scripts/operations/qwen-list-prices.json"
# The composer's modes (patch 0022 composerModes.ts): the visible spec (internet on) and its hidden twin (off).
MODES = {"fast": ("baseer-lite", "baseer-lite-noweb"), "careful": ("baseer-plus", "baseer-plus-noweb"),
         "deep": ("baseer-pro", "baseer-pro-noweb")}
# What the owner approved for each mode (model, enable_thinking, reasoning_effort); --offline fails on any drift.
APPROVED = {"fast": ("qwen3.8-flash", False, None), "careful": ("qwen3.8-flash", True, "medium"),
            "deep": ("deepseek-v4.1-flash-1017", True, "high")}
# LibreChat client options in addParams: they shape the call, they are not sent to the provider.
CLIENT_ONLY = {"maxRetries", "timeout"}
CATEGORIES = {"letter", "email", "summary", "translation", "proofreading", "minutes", "report", "problem-analysis",
              "comparison", "reasoning", "file", "image", "web-recent", "no-search", "web-off", "web-toggle",
              "instructions", "deck"}
CHECKS = {"artifact", "include_any", "exclude", "max_words", "table", "bullets", "sources_if_searched"}
SEARCH_MARGIN = 60  # extra input tokens that mean a search happened (measured: searches add 150 to 17,000)
SEARCH_FRAMING = ["knowledge base", "provided information", "قاعدة المعرفة", "قاعدة البيانات المرفقة",
                  "المعلومات المرفقة", "المعلومات المقدمة"]


# ----------------------------------------------------------------------------------------------------- config
def lineup() -> dict[tuple[str, bool], dict]:
    """(mode, web) -> {spec, endpoint, model, params, instructions, url} from librechat.yaml."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    specs = {s["name"]: s for s in cfg["modelSpecs"]["list"]}
    endpoints = {e["name"]: e for e in cfg["endpoints"]["custom"]}
    out = {}
    for mode, names in MODES.items():
        for web, name in ((True, names[0]), (False, names[1])):
            spec = specs[name]
            ep = endpoints[spec["preset"]["endpoint"]]
            params = {k: v for k, v in (ep.get("addParams") or {}).items() if k not in CLIENT_ONLY}
            out[(mode, web)] = {"spec": name, "endpoint": ep["name"], "model": spec["preset"]["model"],
                                "models": ep["models"]["default"], "params": params,
                                "drop": ep.get("dropParams") or [], "instructions": spec["preset"]["promptPrefix"],
                                "url": ep["baseURL"].rstrip("/") + "/chat/completions"}
    return out


def image_png() -> str:
    """Synthetic 120x80 PNG: red, green and blue bars on white, left to right, the blue one tallest."""
    w, h, bars = 120, 80, [(10, 40, (220, 30, 30), 40), (45, 75, (30, 160, 60), 55), (80, 110, (30, 60, 220), 70)]
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            px = (255, 255, 255)
            for x0, x1, colour, height in bars:
                if x0 <= x < x1 and y >= h - height:
                    px = colour
            row += bytes(px)
        rows.append(bytes(row))
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode()


def user_content(sc: dict, prompt: str) -> str | list:
    if sc.get("image") == "three-bars":
        return [{"type": "image_url", "image_url": {"url": image_png()}}, {"type": "text", "text": prompt}]
    return prompt


def body_for(entry: dict, messages: list[dict], stream: bool = True) -> dict:
    body = {"model": entry["model"], "messages": [{"role": "system", "content": entry["instructions"]}, *messages],
            **entry["params"]}
    if stream:
        body.update(stream=True, stream_options={"include_usage": True})
    return body


# ----------------------------------------------------------------------------------------------------- offline
def validate(scenarios: list[dict], lu: dict) -> list[str]:
    errors = []
    ids = [s["id"] for s in scenarios]
    if len(scenarios) < 30:
        errors.append(f"{len(scenarios)} scenarios; at least 30 are required")
    if len(set(ids)) != len(ids):
        errors.append("duplicate scenario ids")
    missing = CATEGORIES - {s["category"] for s in scenarios}
    if missing:
        errors.append(f"categories without a scenario: {sorted(missing)}")
    for s in scenarios:
        bad = [m for m in s["modes"] if m not in MODES]
        unknown = set(s.get("checks", {})) - CHECKS
        if bad or unknown or s["category"] not in CATEGORIES or s["lang"] not in ("ar", "en"):
            errors.append(f"{s['id']}: modes={bad} checks={sorted(unknown)} category={s['category']} lang={s['lang']}")
        if not s.get("prompt") and not s.get("turns"):
            errors.append(f"{s['id']}: no prompt")
    for mode, (model, thinking, effort) in APPROVED.items():
        for web in (True, False):
            e = lu[(mode, web)]
            p = e["params"]
            got = (e["model"], p.get("enable_thinking"), p.get("reasoning_effort"))
            if got != (model, thinking, effort) or e["models"] != [model]:
                errors.append(f"{mode} web={web}: {got} models={e['models']}, approved {(model, thinking, effort)}")
            search = (p.get("enable_search"), (p.get("search_options") or {}).get("search_strategy"))
            if search != ((True, "turbo") if web else (None, None)):
                errors.append(f"{mode} web={web}: search params {search}")
            if not {"web_search", "useResponsesApi"} <= set(e["drop"]):
                errors.append(f"{mode} web={web}: dropParams {e['drop']} must drop web_search and useResponsesApi")
            if ("البحث في الإنترنت متوقف" in e["instructions"]) == web:
                errors.append(f"{mode} web={web}: instructions do not match the internet setting")
    return errors


# ----------------------------------------------------------------------------------------------------- live
def post(url: str, key: str, body: dict, stream: bool) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0, first, first_text, text, reasoning, usage = time.monotonic(), None, None, "", "", {}
    with urllib.request.urlopen(req, timeout=240) as resp:
        if not stream:
            return {"usage": json.load(resp).get("usage") or {}}
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            chunk = json.loads(line[5:])
            usage = chunk.get("usage") or usage
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                if (delta.get("content") or delta.get("reasoning_content")) and first is None:
                    first = time.monotonic() - t0
                if delta.get("content") and first_text is None:
                    first_text = time.monotonic() - t0
                text += delta.get("content") or ""
                reasoning += delta.get("reasoning_content") or ""
    return {"secs": round(time.monotonic() - t0, 2), "first_token": first and round(first, 2),
            "first_text": first_text and round(first_text, 2), "text": text, "reasoning_chars": len(reasoning),
            "usage": usage}


def norm(text: str) -> str:
    """Case, emphasis, digits (Arabic-Indic to ASCII) and thousands separators folded: «١٣٥ ٠٠٠» matches 135000."""
    text = text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫", "01234567890123456789."))
    text = text.replace("**", "").replace("__", "")  # emphasis inside a word: «**S**pecific»
    return re.sub(r"(?<=\d)[,\u066c\u202f\u00a0 ](?=\d{3})", "", text).lower()


def check(sc: dict, text: str, searched: bool | None) -> dict[str, bool]:
    c, out = sc.get("checks", {}), {}
    folded = norm(text)
    letters = re.findall(r"[A-Za-z؀-ۿ]", text)
    arabic = sum(1 for ch in letters if "؀" <= ch <= "ۿ")
    ratio = arabic / len(letters) if letters else 0
    out["language"] = ratio >= 0.5 if sc["lang"] == "ar" else ratio <= 0.3
    out["no_cjk"] = not re.search(r"[぀-ヿ㐀-鿿]", text)  # leaked Chinese/Japanese (seen live)
    words = len(text.split())
    if "max_words" in c:
        out["max_words"] = words <= c["max_words"]
    if "include_any" in c:
        out["include_any"] = all(any(norm(t) in folded for t in group) for group in c["include_any"])
    if "exclude" in c:
        out["exclude"] = not any(norm(t) in folded for t in c["exclude"])
    if "artifact" in c:
        out["artifact"] = (":::artifact" in text) == c["artifact"]
    if c.get("table"):
        out["table"] = bool(re.search(r"^\|.*\|\s*$", text, re.M))
    if "bullets" in c:
        out["bullets"] = len(re.findall(r"^\s*(?:[-*•]|\d+[.)]|[٠-٩]+[.)])\s+", text, re.M)) == c["bullets"]
    if c.get("sources_if_searched") and searched:
        out["sources_if_searched"] = "المصادر" in text or "المصدر" in text or "sources" in folded
    if searched:  # seen live: search results presented as material the user attached
        out["search_framing"] = not any(p in folded for p in SEARCH_FRAMING)
    return out


def run_live(scenarios: list[dict], lu: dict, key: str, out_dir: Path) -> int:
    prices = json.loads(PRICES.read_text(encoding="utf-8"))
    results, failures = [], 0
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = (out_dir / "results.jsonl").open("w", encoding="utf-8")
    for sc in scenarios:
        for mode in sc["modes"]:
            turns = sc.get("turns") or [{"web": sc["web"], "prompt": sc["prompt"]}]
            history: list[dict] = []
            for n, t in enumerate(turns, 1):
                entry = lu[(mode, t["web"])]
                messages = history + [{"role": "user", "content": user_content(sc, t["prompt"])}]
                rec = {"id": sc["id"], "turn": n, "category": sc["category"], "mode": mode, "web": t["web"],
                       "spec": entry["spec"], "model": entry["model"], "expect_search": sc.get("expect_search")}
                try:
                    r = post(entry["url"], key, body_for(entry, messages), stream=True)
                    base = None
                    if t["web"]:
                        count = {k: v for k, v in body_for(entry, messages, stream=False).items()
                                 if k not in ("enable_search", "search_options", "reasoning_effort")}
                        count.update(max_tokens=1, enable_thinking=False)
                        base = post(entry["url"], key, count, stream=False)["usage"].get("prompt_tokens")
                except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                    failures += 1
                    detail = exc.read().decode("utf-8", "replace")[:200] if isinstance(exc, urllib.error.HTTPError) else ""
                    rec.update(error=f"{exc.__class__.__name__}: {exc} {detail}")
                    results.append(rec)
                    raw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    break
                u = r["usage"]
                pt, ct = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
                extra = (pt - base) if base is not None else 0
                searched = extra > SEARCH_MARGIN if t["web"] else False
                p = prices["models"].get(entry["model"])
                rec.update(secs=r["secs"], first_token=r["first_token"], first_text=r["first_text"],
                           input_tokens=pt, output_tokens=ct,
                           reasoning_tokens=(u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                           search_input_tokens=extra if searched else 0, searched=searched,
                           token_cost=round((pt * p["input"] + ct * p["output"]) / prices["tokens_per_price"], 6),
                           checks=check(sc, r["text"], searched), words=len(r["text"].split()), text=r["text"])
                results.append(rec)
                raw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                raw.flush()
                print(f"{sc['id']}.{n} {mode:<7} web={'on ' if t['web'] else 'off'} {r['secs']:>6}s "
                      f"in={pt} out={ct} searched={searched} checks="
                      f"{sum(rec['checks'].values())}/{len(rec['checks'])}", flush=True)
                history = messages + [{"role": "assistant", "content": r["text"]}]
    raw.close()
    (out_dir / "summary.md").write_text(summary(results, prices), encoding="utf-8")
    print(f"# results: {out_dir / 'results.jsonl'}  summary: {out_dir / 'summary.md'}")
    return 1 if failures else 0


def summary(results: list[dict], prices: dict) -> str:
    ok = [r for r in results if "error" not in r]
    lines = [f"# Model benchmark — {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}", "",
             f"Calls: {len(results)} ({len(results) - len(ok)} failed). Token cost estimate from list prices "
             f"({prices['region']}, {prices['retrieved']}); searches not priced (see the bill).", "",
             "| mode | internet | calls | checks passed | median s | max s | input tok | output tok | reasoning tok "
             "| searched | est. token cost USD |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for mode in MODES:
        for web in (True, False):
            rs = [r for r in ok if r["mode"] == mode and r["web"] == web]
            if not rs:
                continue
            secs = sorted(r["secs"] for r in rs)
            passed = sum(sum(r["checks"].values()) for r in rs)
            total = sum(len(r["checks"]) for r in rs)
            lines.append(f"| {mode} | {'on' if web else 'off'} | {len(rs)} | {passed}/{total} | {secs[len(secs) // 2]} "
                         f"| {secs[-1]} | {sum(r['input_tokens'] for r in rs)} | {sum(r['output_tokens'] for r in rs)} "
                         f"| {sum(r['reasoning_tokens'] or 0 for r in rs)} | {sum(r['searched'] for r in rs)}/{len(rs)} "
                         f"| {sum(r['token_cost'] for r in rs):.4f} |")
    web_rs = [r for r in ok if r["web"] and r["expect_search"] is not None]
    for expect in (True, False):
        rs = [r for r in web_rs if r["expect_search"] is expect]
        if rs:
            lines += ["", f"- Search on {'time-sensitive' if expect else 'timeless'} questions (internet on): "
                          f"{sum(r['searched'] for r in rs)}/{len(rs)} — "
                          + ", ".join(f"{r['id']}/{r['mode']}={'yes' if r['searched'] else 'no'}" for r in rs)]
    lines += ["", "| id | turn | mode | internet | s | in | out | searched | failed checks |",
              "|---|---:|---|---|---:|---:|---:|---|---|"]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['id']} | {r['turn']} | {r['mode']} | {'on' if r['web'] else 'off'} | — | — | — | — "
                         f"| ERROR {r['error'][:80]} |")
            continue
        failed = ", ".join(k for k, v in r["checks"].items() if not v) or "—"
        lines.append(f"| {r['id']} | {r['turn']} | {r['mode']} | {'on' if r['web'] else 'off'} | {r['secs']} "
                     f"| {r['input_tokens']} | {r['output_tokens']} | {'yes' if r['searched'] else 'no'} | {failed} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--key-file")
    ap.add_argument("--only")
    ap.add_argument("--out")
    ap.add_argument("--rescore", metavar="RESULTS_JSONL", help="re-apply the checks to saved results (no network)")
    args = ap.parse_args()
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]
    lu = lineup()
    errors = validate(scenarios, lu)
    if args.only:
        wanted = set(args.only.split(","))
        scenarios = [s for s in scenarios if s["id"] in wanted]
    calls = sum(len(s["modes"]) * len(s.get("turns") or [None]) for s in scenarios)
    print(f"# {len(scenarios)} scenarios, {calls} chat calls; config {CONFIG.relative_to(ROOT)}")
    for (mode, web), e in lu.items():
        print(f"#   {mode:<7} web={'on ' if web else 'off'} {e['spec']:<18} {e['endpoint']:<20} {e['model']} "
              f"{json.dumps(e['params'], ensure_ascii=False)}")
    for s in scenarios:  # every request must build (image included)
        for mode in s["modes"]:
            for t in s.get("turns") or [{"web": s["web"], "prompt": s["prompt"]}]:
                json.dumps(body_for(lu[(mode, t["web"])], [{"role": "user", "content": user_content(s, t["prompt"])}]))
    for e in errors:
        print(f"FAIL  {e}")
    if errors:
        return 1
    if args.rescore:
        by_id = {s["id"]: s for s in json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]}
        rows = [json.loads(line) for line in Path(args.rescore).read_text(encoding="utf-8").splitlines() if line]
        for r in rows:
            if "error" not in r:
                r["checks"] = check(by_id[r["id"]], r["text"], r["searched"])
        print(summary(rows, json.loads(PRICES.read_text(encoding="utf-8"))))
        return 0
    if not args.live:
        print("PASS  offline: scenarios valid, every request builds, modes match the approved lineup")
        return 0
    key = Path(args.key_file).read_text(encoding="utf-8").strip() if args.key_file else os.environ.get("QWEN_API_KEY")
    if not key:
        raise SystemExit("--live needs --key-file or QWEN_API_KEY")
    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="efaiw-benchmark-"))
    return run_live(scenarios, lu, key, out)


if __name__ == "__main__":
    sys.exit(main())
