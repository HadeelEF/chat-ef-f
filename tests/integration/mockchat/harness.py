"""Constants, shared state and stack helpers of the mock-chat regression suite; `run_suite` drives the checks."""

from __future__ import annotations

import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                           check=True).stdout.strip())
STACK = ROOT / "infrastructure/compose"
HERE = ROOT / "tests/integration"
PORT = int(os.environ.get("MOCK_CHAT_HTTP_PORT", "3397"))
BASE = f"http://127.0.0.1:{PORT}"
ADMIN_PORT = int(os.environ.get("MOCK_CHAT_ADMIN_PORT", "3396"))  # Admin Panel on loopback (ADR-0016)
ADMIN_BASE = f"http://127.0.0.1:{ADMIN_PORT}"
PROJECT = f"efaiw-mockchat-{os.getpid()}"
ENDPOINT, OFFLINE, RETRY = "Baseer Mock", "Baseer Mock Offline", "Baseer Mock Retry"
MODELS = ["baseer-mock-echo", "baseer-mock-slow", "baseer-mock-error", "baseer-mock-5xx", "baseer-mock-429",
          "baseer-mock-401", "baseer-mock-gone", "baseer-mock-hang", "baseer-mock-stall", "baseer-mock-markdown"]
# Mirror of MARKDOWN in mock-llm/mock-llm.mjs: mixed Arabic/English Markdown for RTL/bidi round trips (#44).
MARKDOWN = "\n".join([
    "## ملخص اصطناعي — Synthetic summary", "",
    "هذا رد **ثابت** يجمع العربية و English في فقرة واحدة، مع التاريخ 2026-10-19 والنموذج `baseer-mock-markdown`.", "",
    "- البند الأول: الإعداد في `librechat.yaml` (version 1.3.17).",
    "- Second item: an English line inside an Arabic list.",
    "- الرابط: https://example.invalid/docs?lang=ar", "",
    "```python", "def greet(name: str) -> str:", '    return f"مرحباً {name}"  # تعليق عربي داخل الكود', "```", "",
    "| الحقل | Value |", "|---|---|", "| الحالة | Tested |"])
CANARY = "internal-gateway.corp.invalid"  # in every mock failure body (mock-llm.mjs); must never reach a user
# Employee model lineup of infrastructure/common/librechat.yaml (#37, #131): (spec, endpoint, model, enable_thinking
# sent). The test points every Qwen Cloud endpoint at the mock (merged_config), so the real specs, lists and params are
# exercised. EFFORT: the `reasoning_effort` each spec's endpoint sends; LABELS: the reply label each spec stores.
LINEUP = [("baseer-lite", "Qwen", "qwen3.8-flash", False), ("baseer-plus", "Qwen Thinking", "qwen3.8-flash", True),
          ("baseer-pro", "DeepSeek", "deepseek-v4.1-flash-1017", True)]
EFFORT = {"baseer-lite": None, "baseer-plus": "medium", "baseer-pro": "high"}
LABELS = {"baseer-lite": "بصير لايت", "baseer-plus": "بصير بلس", "baseer-pro": "بصير برو"}
# Qwen Cloud's built-in web search (#135, ADR-0015): every chat endpoint of the lineup searches with this strategy; the
# background endpoint (titles, memories, summaries; not all of its calls are streamed) never searches.
SEARCH_STRATEGY = "turbo"
TASKS_ENDPOINT = "Qwen Tasks"
# No-search twins (#138): the composer's «الإنترنت» switch moves a chat to its spec's hidden twin (twin spec, its
# endpoint without search, the visible spec whose model, thinking, depth and label it keeps).
NOWEB = [("baseer-lite-noweb", "Qwen NoWeb", "baseer-lite"), ("baseer-plus-noweb", "Qwen Thinking NoWeb", "baseer-plus"),
         ("baseer-pro-noweb", "DeepSeek NoWeb", "baseer-pro")]
# Models of the previous lineup (#112), retired in #131: the server must refuse them.
RETIRED = [("Qwen", "qwen3.7-plus"), ("Qwen Max", "qwen3.8-max")]
QWEN_URL = "https://maas.qwencloudapi.com/compatible-mode/v1"
THINKING = "تفكير اصطناعي ثابت. Synthetic reasoning."  # mirror of THINKING in mock-llm/mock-llm.mjs
# UX phase 1 (#87): landing greeting, hidden controls and the notice every spec line must carry.
WELCOME = "كيف أساعدك اليوم؟"
HIDDEN_UI = ["presets"]  # the parameters panel is back (#108); compare and the context gauge are on (#125)
# Role permissions the shared policy (infrastructure/common/librechat.yaml `interface`) must leave false for USER and ADMIN.
# Role policy of librechat.yaml (#39, owner decisions #108, #125, #189): the side-menu workspace is on and shared inside
# the platform, only ADMIN publishes to everyone; shared links (behind the login) and side-by-side compare are on; web
# search, code, file search, schedules and the remote agents API stay off. MCP servers (#218, ADR-0021, set by
# infrastructure/common/roles-policy.js before every start): ADMIN uses and adds them, nobody shares one.
PUBLISH = {"AGENTS": ["SHARE_PUBLIC"], "SKILLS": ["SHARE_PUBLIC"], "PROMPTS": ["SHARE_PUBLIC"]}  # ADMIN only (#189)
ADMIN_MCP = {"MCP_SERVERS": ["USE", "CREATE"]}  # ADMIN only (#218)
DENIED = {"MCP_SERVERS": ["SHARE", "SHARE_PUBLIC", "CONFIGURE_OBO"],
          "REMOTE_AGENTS": ["USE", "CREATE", "SHARE", "SHARE_PUBLIC"],
          "WEB_SEARCH": ["USE"], "RUN_CODE": ["USE"], "FILE_SEARCH": ["USE"], "FILE_CITATIONS": ["USE"],
          "SCHEDULES": ["USE", "CREATE"]}
ALLOWED = {"PROMPTS": ["USE", "CREATE", "SHARE"], "BOOKMARKS": ["USE"], "AGENTS": ["USE", "CREATE", "SHARE"],
           "SKILLS": ["USE", "CREATE", "SHARE"], "MARKETPLACE": ["USE"], "MEMORIES": ["USE"],
           # #125: SHARE_PUBLIC = "anyone signed in" (ALLOW_SHARED_LINKS_PUBLIC=false keeps the login; M52).
           "SHARED_LINKS": ["CREATE", "SHARE", "SHARE_PUBLIC"], "MULTI_CONVO": ["USE"]}
# Agent capabilities of the deployment (#108); anything else (code, file search, web search, actions, OCR) stays off.
CAPABILITIES = {"artifacts", "context", "skills", "memory", "tools", "chain", "subagents", "deferred_tools",
                "ask_user_question"}
# Backend routes of the capabilities that stay off: each must answer 403 to USER and (by default) to ADMIN.
GUARDED = [("GET", "/api/api-keys", None), ("GET", "/api/schedules", None)]
# MCP routes (#218): 403 to USER; ADMIN lists servers and tools (M92).
MCP_GUARDED = [("GET", "/api/mcp/servers", None),
               ("POST", "/api/mcp/servers",
                {"config": {"title": "synthetic", "type": "streamable-http", "url": "https://mcp.example.invalid/mcp"}}),
               ("GET", "/api/mcp/tools", None)]
# Server URLs an ADMIN must not add (M93): private, loopback, link-local (cloud metadata) and Compose service addresses.
MCP_PRIVATE_URLS = ["http://10.0.0.1/mcp", "http://127.0.0.1:3080/mcp", "http://169.254.169.254/latest/meta-data/",
                    "http://mongodb:27017/mcp", "http://meilisearch:7700/mcp", "http://[::1]:3080/mcp"]
# Routes of the side-menu workspace (#108): each must answer 200 to USER and ADMIN.
OPEN = [("GET", "/api/agents", None), ("GET", "/api/skills", None), ("GET", "/api/memories", None)]
ZERO = "00000000-0000-0000-0000-000000000000"
# LibreChat rejects API calls without a browser-like User-Agent ("Illegal request", uaParser middleware).
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36 EFAIW-mock-chat"

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never via an HTTP(S)_PROXY
opener.addheaders = [("User-Agent", UA)]
responses: list[str] = []  # every API response body, scanned for secrets at the end
failures = total = 0

# Run configuration, set by configure() from the command line.
KEEP = False
RESULTS: Path | None = None
work: Path | None = None
env_file: Path | None = None


def configure(argv: list[str]) -> None:
    """[results-file] [--keep] -> module state (a throwaway work directory holds the env file and config)."""
    global KEEP, RESULTS, work, env_file
    args = [a for a in argv if not a.startswith("--")]
    KEEP = "--keep" in argv
    RESULTS = Path(args[0]) if args else None
    work = Path(tempfile.mkdtemp(prefix="efaiw-mockchat-"))
    env_file = work / ".env"


# ----------------------------------------------------------------------------------------------------- helpers
def log(line: str) -> None:
    print(line, flush=True)
    if RESULTS:
        with RESULTS.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def check(cid: str, desc: str, fn) -> None:
    global failures, total
    total += 1
    try:
        result = fn()
        ok, detail = (result, "") if isinstance(result, bool) else result
    except Exception as exc:  # a crashing check is a failing check
        ok, detail = False, f"{exc.__class__.__name__}: {exc}"
    if ok:
        log(f"PASS  {cid}  {desc}")
    else:
        failures += 1
        log(f"FAIL  {cid}  {desc} :: {str(detail)[:300]}")


def run(*cmd: str, inp: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, input=inp, capture_output=True, text=True, env=env)


def dc(*cmd: str) -> subprocess.CompletedProcess:
    return run("docker", "compose", "-p", PROJECT, "-f", str(STACK / "compose.yaml"), "-f", str(STACK / "compose.local.yaml"),
               "-f", str(HERE / "compose.mock-llm.yaml"), "--env-file", str(env_file), *cmd)


def ctr(service: str) -> str:
    return dc("ps", "-q", service).stdout.strip()


def env_value(key: str) -> str:
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1]
    return ""


def wait_healthy(services=("librechat", "mock-llm", "mongodb", "meilisearch", "admin-panel"), timeout=300) -> tuple[bool, str]:
    deadline, states = time.time() + timeout, ""
    while time.time() < deadline:
        states = dc("ps", "--format", "{{.Service}}={{.Health}}").stdout
        if all(f"{s}=healthy" in states.split() for s in services):
            return True, ""
        time.sleep(5)
    return False, f"not healthy: {states.split()}"


def anon_volumes() -> list[str]:
    names = []
    for cid in dc("ps", "-aq").stdout.split():
        out = run("docker", "inspect", "-f", '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{end}}{{end}}', cid).stdout
        names += [v for v in out.split() if re.fullmatch(r"[0-9a-f]{64}", v)]
    return names


def cleanup() -> None:
    if work is None:
        return
    if KEEP:
        log(f"# --keep: stack '{PROJECT}' left running; env and config in {work}")
        return
    vols = anon_volumes()
    dc("down", "-v", "--remove-orphans")
    if vols:
        run("docker", "volume", "rm", *vols)
    shutil.rmtree(work, ignore_errors=True)


# ----------------------------------------------------------------------------------------------------- setup
def merged_config() -> str:
    """Shared librechat.yaml with the fragment's mock endpoints appended to the shared `endpoints.custom` list and the
    Qwen endpoints pointed at the mock (same specs, model lists and params; test key instead of QWEN_API_KEY)."""
    base = (ROOT / "infrastructure/common/librechat.yaml").read_text(encoding="utf-8").rstrip("\n") + "\n"
    endpoints_n = len({e for _, e, _, _ in LINEUP} | {e for _, e, _ in NOWEB} | {TASKS_ENDPOINT})
    if base.count(f"baseURL: '{QWEN_URL}'") != endpoints_n or base.count("apiKey: '${QWEN_API_KEY}'") != endpoints_n:
        raise SystemExit("librechat.yaml: expected each Qwen endpoint to use QWEN_URL and ${QWEN_API_KEY} (#37)")
    base = (base.replace(f"baseURL: '{QWEN_URL}'", "baseURL: 'http://mock-llm:8080/v1'")
            .replace("apiKey: '${QWEN_API_KEY}'", "apiKey: '${MOCK_LLM_API_KEY}'"))
    frag = (HERE / "librechat.mock-endpoints.yaml").read_text(encoding="utf-8")
    top = [line.rstrip() for line in base.splitlines() if re.match(r"[A-Za-z_]", line)]
    endpoints = base[base.rindex("\nendpoints:\n") + 1:]
    children = [line.rstrip() for line in endpoints.splitlines() if re.match(r"  [A-Za-z_]+:", line)]
    marker = "\nendpoints:\n  custom:\n"
    if top[-1] != "endpoints:" or not children or children[-1] != "  custom:" or marker not in frag:
        raise SystemExit("librechat.yaml: `endpoints:` must stay the last top-level key and `custom:` its last child "
                         "(update merged_config() when the layout changes, #37)")
    return base + frag.split(marker, 1)[1]


def setup() -> None:
    out = run(str(ROOT / "scripts/setup/new-env.sh"), "local", "--port", str(PORT), "--admin-port", str(ADMIN_PORT),
              "--output", str(env_file))
    if out.returncode != 0:
        raise SystemExit(f"new-env.sh failed: {out.stderr}")
    text = re.sub(r"^DOMAIN_(CLIENT|SERVER)=.*$", lambda m: f"DOMAIN_{m.group(1)}={BASE}",
                  env_file.read_text(encoding="utf-8"), flags=re.M)
    text = re.sub(r"^ADMIN_PANEL_URL=.*$", f"ADMIN_PANEL_URL={ADMIN_BASE}", text, flags=re.M)
    config = work / "librechat.yaml"  # shared policy file + test-only mock endpoints
    config.write_text(merged_config(), encoding="utf-8")
    text += (f"MOCK_LLM_API_KEY={secrets.token_hex(24)}\nMOCK_LIBRECHAT_YAML={config}\n"
             f"MOCK_LLM_DIR={HERE / 'mock-llm'}\n")
    env_file.write_text(text, encoding="utf-8")
    env_file.chmod(0o600)


# ----------------------------------------------------------------------------------------------------- test run
def main() -> int:
    from . import (checks_admin, checks_batch2, checks_brand, checks_chat, checks_failures,  # late: they import us
                   checks_features, checks_policy, checks_prompts)

    setup()
    head = run("git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD").stdout.strip()
    docker_v = run("docker", "version", "--format", "{{.Server.Version}}").stdout.strip()
    compose_v = run("docker", "compose", "version", "--short").stdout.strip()
    log(f"# Mock chat regression (#38, #39)  commit={head}  date={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
        f"  docker={docker_v}  compose={compose_v}")

    # State shared between checks: synthetic accounts, tokens and the ids each check leaves for the next ones.
    st: dict = {"pw": {"a": secrets.token_hex(12), "b": secrets.token_hex(12), "admin": secrets.token_hex(12)},
                "users": {"a": "synthetic.chat.a@example.invalid", "b": "synthetic.chat.b@example.invalid"},
                "key": env_value("MOCK_LLM_API_KEY")}

    checks_chat.stack(st)              # M01–M09: stack, isolation of the mock, accounts, endpoints, models
    checks_chat.chat(st)               # M10–M15, M38, M16–M18: streaming, history, cancellation, errors, isolation
    checks_chat.lineup(st)             # M39–M45, M48, M66, M67, M69, M73–M75: employee model lineup (specs, lists,
                                       # thinking and its depth, search and its no-search twins, titles, dropped
                                       # OpenAI-only switches, retired models), shell
    checks_chat.usage(st)              # M91: usage and cost report per mode, model and user (#211)
    checks_policy.policy(st)           # M22, M23, M37, M24, M25, M46, M47, M26, M27: policy, enforcement, agents, memory
    checks_features.features(st)       # M49–M56, M70: conversation search, shared links, side-by-side compare
    checks_batch2.batch2(st)           # M57–M65, M68, M71, M72: clarifying questions, filter, files, summaries, artifacts
    checks_brand.brand(st)             # M83–M85: platform brand Skill for everyone, read-only, reaching the model
    checks_prompts.prompts(st)         # M87–M89: EF ready commands for everyone, read-only; ADMIN-only publishing
    checks_admin.admin_panel(st)       # M76–M81: Admin Panel, admin-only API, Settings link, roles/groups, drift check
    checks_failures.provider_failures(st)  # M28–M34, M86: fast, generic provider failures; stalled stream; Stop
    checks_policy.editor_override(st)  # M35
    checks_chat.restart(st)            # M19, M20: restart, reopen and continue
    checks_policy.policy_reapplied(st)  # M36
    checks_admin.admin_after_restart(st)  # M82
    checks_prompts.prompts_after_restart(st)  # M90
    checks_chat.leaks(st)              # M21: no secret anywhere

    log(f"# result: {total - failures}/{total} passed")
    return 1 if failures else 0


def run_suite(argv: list[str]) -> int:
    configure(argv)
    try:
        return main()
    finally:
        cleanup()
