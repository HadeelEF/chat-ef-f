#!/usr/bin/env python3
"""UI test stack (#221, toward #194): the synthetic mock-chat Compose stack of tests/integration, with the Arabic web
client of a LibreChat image built from infrastructure/railway/librechat.Dockerfile mounted over the upstream client,
two synthetic accounts (the first account is ADMIN, deployment.md section 3; the second a USER) and synthetic chats for each.

    tests/ui/ui_stack.py up --image <tag>   # prints the path of a JSON state file (base URL, accounts, project)
    tests/ui/ui_stack.py down <state.json>  # removes the stack, its volumes and its work directory

TEST-ONLY: throwaway secrets, synthetic data, the deterministic mock model, loopback port only. Standard library only;
it reuses tests/integration/mockchat (configuration, env file, accounts, chat calls). The browser checks run against it
with tests/ui/sidebar_v5.cjs (sidebar, #221) and tests/ui/chat_design.cjs (chat page, #224).
"""

from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "integration"))
from mockchat import client as c  # noqa: E402  (after the path)
from mockchat import harness as h  # noqa: E402

# Synthetic chats, titled as employees title them: Arabic and English, so the RTL/LTR fading is exercised.
CHATS = {
    "admin": ["ترجمة رسمية للمراسلات الحكومية", "Business Requirements Document", "خطة منصة الخدمات الإلكترونية",
              "Design Login Page", "مراجعة متطلبات الأمن السيبراني"],
    "employee": ["تلخيص محضر الاجتماع الأسبوعي", "Environmental Fund BRD", "صياغة خطاب رسمي للجهات",
                 "Employee Performance System Requirements", "أهداف قابلة للقياس للربع القادم", "مرحبا"],
}
ACCOUNTS = {
    "admin": ("synthetic.ui.admin@example.invalid", "Synthetic UI Admin", "synthuiadmin"),
    "employee": ("synthetic.ui.employee@example.invalid", "نورة الاصطناعية", "synthuiemployee"),
}


def overlay_dc(overlay: Path):
    """harness.dc with the client overlay: the harness helpers (ctr, wait_healthy, cleanup) call it by name."""
    def dc(*cmd: str):
        return h.run("docker", "compose", "-p", h.PROJECT, "-f", str(h.STACK / "compose.yaml"),
                     "-f", str(h.STACK / "compose.local.yaml"), "-f", str(h.HERE / "compose.mock-llm.yaml"),
                     "-f", str(overlay), "--env-file", str(h.env_file), *cmd)
    return dc


def extract_client(image: str, dest: Path) -> None:
    cid = h.run("docker", "create", image).stdout.strip()
    if not cid:
        raise SystemExit(f"docker create {image} failed")
    try:
        out = h.run("docker", "cp", f"{cid}:/app/client/dist", str(dest))
        if out.returncode != 0 or not (dest / "index.html").is_file():
            raise SystemExit(f"no client in {image}: {out.stderr}")
    finally:
        h.run("docker", "rm", cid)


def seed(role: str, token: str) -> None:
    for title in CHATS[role]:
        status, job = c.start_chat(token, f"{title} — رسالة اختبار اصطناعية")
        if status != 200 or not isinstance(job, dict):
            raise SystemExit(f"seed {role}: HTTP {status} {str(job)[:200]}")
        _, events = c.read_stream(token, job)
        final = c.final_of(events)
        convo = (final.get("conversation") or {}).get("conversationId") or \
            (final.get("responseMessage") or {}).get("conversationId")
        if not convo:
            raise SystemExit(f"seed {role}: no conversation id")
        status, _ = c.api("POST", "/api/convos/update", token, {"arg": {"conversationId": convo, "title": title}})
        if status != 201 and status != 200:
            raise SystemExit(f"seed {role}: rename HTTP {status}")


def up(image: str) -> None:
    h.configure([])
    h.setup()
    dist = h.work / "dist"
    extract_client(image, dist)
    overlay = h.work / "compose.ui.yaml"
    overlay.write_text(
        "services:\n  librechat:\n    volumes:\n      - type: bind\n"
        f"        source: {dist}\n        target: /app/client/dist\n        read_only: true\n", encoding="utf-8")
    h.dc = overlay_dc(overlay)
    if h.dc("up", "-d", "--quiet-pull").returncode != 0:
        raise SystemExit("docker compose up failed")
    ok, detail = h.wait_healthy()
    if not ok:
        raise SystemExit(detail)
    state = {"base": h.BASE, "project": h.PROJECT, "work": str(h.work), "image": image, "accounts": {}}
    for role in ("admin", "employee"):  # in this order: the first account of a fresh database becomes ADMIN
        email, name, username = ACCOUNTS[role]
        password = secrets.token_hex(12)
        out = c.create_user(email, name, username, password)
        if out.returncode != 0:
            raise SystemExit(f"create-user {role}: {out.stderr}")
        status, body = c.login(email, password)
        expected = "ADMIN" if role == "admin" else "USER"
        if status != 200 or body.get("user", {}).get("role") != expected:
            raise SystemExit(f"login {role}: HTTP {status}, role {body.get('user', {}).get('role')}")
        seed(role, body["token"])
        state["accounts"][role] = {"email": email, "password": password}
    path = h.work / "state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    path.chmod(0o600)
    print(path)


def down(state_file: str) -> None:
    state = json.loads(Path(state_file).read_text(encoding="utf-8"))
    h.PROJECT, h.work, h.KEEP = state["project"], Path(state["work"]), False
    h.env_file = h.work / ".env"
    h.dc = overlay_dc(h.work / "compose.ui.yaml")
    h.cleanup()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["up"] and len(args) == 3 and args[1] == "--image":
        up(args[2])
    elif args[:1] == ["down"] and len(args) == 2:
        down(args[1])
    else:
        raise SystemExit(__doc__)
