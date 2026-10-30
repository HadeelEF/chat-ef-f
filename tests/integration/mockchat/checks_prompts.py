"""EF ready commands (#189, ADR-0018): the templates of ai/prompts/ created once for everyone (M87), usable but not
editable by a USER (M88), publishing to everyone for ADMIN only (M89) and no duplicate after a restart (M90)."""

from __future__ import annotations

import json
import time

from .client import api
from .harness import ROOT, check

TEMPLATES = json.loads((ROOT / "ai/prompts/ef-templates.json").read_text(encoding="utf-8"))


def ef_groups(token: str) -> list[dict]:
    """The EF ready commands among the prompt groups the account can use (the composer's «/» list), each with its
    `command` from the group itself: v0.8.8 leaves `command` out of the lists (upstream fixed it after v0.8.8)."""
    status, raw = api("GET", "/api/prompts/all", token)
    groups = json.loads(raw) if status == 200 else []
    names = {t["name"] for t in TEMPLATES["templates"]}
    rows = []
    for group in (g for g in groups if g.get("name") in names and g.get("authorName") == TEMPLATES["authorName"]):
        status, raw = api("GET", f"/api/prompts/groups/{group['_id']}", token)
        rows.append({**group, "command": json.loads(raw).get("command") if status == 200 else None})
    return rows


def publish(token: str, group_id: str) -> int:
    """HTTP status of publishing a prompt group to everyone (the sharing dialog's «everyone» switch)."""
    return api("PUT", f"/api/permissions/promptGroup/{group_id}", token,
               {"updated": [], "removed": [], "public": True, "publicAccessRoleId": "promptGroup_viewer"})[0]


def prompts(st: dict) -> None:
    def created():
        want = {t["command"]: t for t in TEMPLATES["templates"]}
        for _ in range(9):  # the seed checks every 20 s for the ADMIN account bootstrapped at the start of the run
            seen = {who: ef_groups(st[who]) for who in ("a", "b")}
            if all(len(g) == len(want) for g in seen.values()):
                break
            time.sleep(10)
        rows = {g["command"]: g for g in seen["a"]}
        same = all(rows.get(c, {}).get("name") == t["name"] and rows[c].get("oneliner") == t["oneliner"]
                   and rows[c].get("category") == t["category"]
                   and (rows[c].get("productionPrompt") or {}).get("prompt") == t["prompt"] for c, t in want.items())
        st["ef_prompt"] = next(iter(rows.values()), {}).get("_id")
        good = same and len(seen["b"]) == len(want) and all(g.get("isPublic") for g in seen["a"])
        return good, f"USER a={sorted(rows)} USER b={len(seen['b'])} same_text={same}"
    check("M87", "the EF ready commands of ai/prompts/ are created once for everyone: every USER lists each /command "
          "with the repository's name, line, category and text, published by the platform", created)

    def read_only():
        gid = st.get("ef_prompt")
        if not gid:
            return False, "no EF command id (M87)"
        patched = api("PATCH", f"/api/prompts/groups/{gid}", st["a"], {"name": "Synthetic edit attempt"})[0]
        deleted = api("DELETE", f"/api/prompts/groups/{gid}", st["a"])[0]
        still = gid in {g.get("_id") for g in ef_groups(st["a"])}
        return patched == 403 and deleted == 403 and still, f"patch={patched} delete={deleted} still_listed={still}"
    check("M88", "a USER uses an EF command but cannot edit or delete it", read_only)

    def admin_publishes_only():
        codes = {}
        for who in ("a", "admin"):
            status, raw = api("POST", "/api/prompts", st[who],
                              {"prompt": {"prompt": f"Synthetic prompt of {who}.", "type": "text"},
                               "group": {"name": f"Synthetic prompt {who}", "category": "misc"}})
            gid = (json.loads(raw).get("prompt") or {}).get("groupId") if status == 200 else None
            codes[who] = (status, publish(st[who], gid) if gid else None)
            if gid:
                api("DELETE", f"/api/prompts/groups/{gid}", st[who])
        return codes["a"][1] == 403 and codes["admin"][1] == 200, f"(create, publish)={codes}"
    check("M89", "only ADMIN publishes a ready command to everyone: a USER's own prompt cannot be made public (403)",
          admin_publishes_only)


def prompts_after_restart(st: dict) -> None:
    def once():
        groups = ef_groups(st["a"])
        commands = [g.get("command") for g in groups]
        return len(commands) == len(set(commands)) == len(TEMPLATES["templates"]), f"commands={sorted(commands)}"
    check("M90", "the EF ready commands are not created again after a restart (one group per command)", once)
