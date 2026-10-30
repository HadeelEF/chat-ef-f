"""EF brand checks (#146, ADR-0017): the platform Skill `ef-brand-guidelines` is installed for every user from the
repository, read-only (M83, M84); its text reaches the model in every turn where skills are on, and the brand block of
the specs' instructions in every chat, with or without internet (M85)."""

from __future__ import annotations

import json

from .checks_batch2 import spec_instructions
from .client import api, expected_reply, final_of, login, requests_for, sha8, text_of, turn
from .harness import LINEUP, NOWEB, ROOT, check

SKILL = "ef-brand-guidelines"
BRAND_HEAD = "هوية صندوق البيئة البصرية:"


def skill_text(name: str = SKILL) -> str:
    """The whole SKILL.md: LibreChat v0.8.8 keeps a deployment Skill's file as its body, frontmatter included
    (packages/api/src/skills/deployment.ts), and primes that text."""
    return (ROOT / "ai/skills" / name / "SKILL.md").read_text(encoding="utf-8")


def always_apply_texts() -> list[str]:
    """Texts of the platform Skills marked always-apply: with skills on, LibreChat primes each as a user message of its
    own before the user's message, so the mock model counts one more turn per Skill."""
    return [skill_text(d.name) for d in sorted((ROOT / "ai/skills").iterdir())
            if (d / "SKILL.md").is_file() and "\nalways-apply: true\n" in skill_text(d.name).split("\n---", 1)[0]]


def body_lines() -> set[str]:
    return {sha8(line.strip()) for line in skill_text().splitlines() if line.strip()}


def brand_lines(anchor: str) -> set[str]:
    """Digests of the brand block of the specs' instructions (from its heading to the end of the block)."""
    lines = spec_instructions(anchor).splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == BRAND_HEAD)
    block = []
    for line in lines[start:]:
        if not line.strip() and block:
            break
        block.append(line)
    return {sha8(line.strip()) for line in block if line.strip()}


def skills_of(token: str) -> list[dict]:
    status, raw = api("GET", "/api/skills", token)
    if status != 200:
        return []
    data = json.loads(raw)
    return data if isinstance(data, list) else data.get("skills") or data.get("data") or []


def brand(st: dict) -> None:
    for who, email in (("a", st["users"]["a"]), ("admin", "synthetic.chat.admin@example.invalid")):
        status, body = login(email, st["pw"][who])
        if status == 200:
            st[who] = body["token"]

    def installed():
        listed = {s.get("name"): s for s in skills_of(st["a"])}
        row = listed.get(SKILL)
        if not row:
            return False, f"not listed for USER: {sorted(listed)}"
        status, raw = api("GET", f"/api/skills/{row['_id']}", st["a"])
        detail = json.loads(raw) if status == 200 else {}
        same = (detail.get("body") or "").strip() == skill_text().strip()
        st["brand_skill_id"] = row["_id"]
        good = (status == 200 and same and detail.get("alwaysApply") is True and detail.get("source") == "deployment"
                and SKILL in {s.get("name") for s in skills_of(st["admin"])})
        return good, (f"detail HTTP {status} same_body={same} alwaysApply={detail.get('alwaysApply')} "
                      f"source={detail.get('source')}")
    check("M83", "the platform Skill ef-brand-guidelines (ai/skills/, ADR-0017) is listed for USER and ADMIN, with "
          "the repository's text, always applied, from the deployment directory", installed)

    def read_only():
        sid = st.get("brand_skill_id")
        if not sid:
            return False, "no skill id (M83)"
        results = []
        for who in ("a", "admin"):
            patched = api("PATCH", f"/api/skills/{sid}", st[who], {"description": "Synthetic edit attempt."})[0]
            deleted = api("DELETE", f"/api/skills/{sid}", st[who])[0]
            results.append((who, patched, deleted))
        still = SKILL in {s.get("name") for s in skills_of(st["a"])}
        good = still and all(not 200 <= p < 300 and not 200 <= d < 300 for _, p, d in results)
        return good, f"patch/delete statuses={results} still_listed={still}"
    check("M84", "the platform Skill is read-only: neither USER nor ADMIN can edit or delete it from the API", read_only)

    def reaches_model():
        skill, results, ok = body_lines(), [], True
        cases = [(LINEUP[0][0], LINEUP[0][1], LINEUP[0][2], "instructions"),
                 (NOWEB[0][0], NOWEB[0][1], LINEUP[0][2], "instructions_noweb")]
        for spec, endpoint, model, anchor in cases:
            block = brand_lines(anchor)
            for skills_on in (True, False):
                prompt = f"Synthetic brand check {spec} skills={skills_on}."
                _, events, want = turn(st["a"], prompt, [], model=model, endpoint=endpoint,
                                       extra={"spec": spec, "ephemeralAgent": {"skills": skills_on,
                                                                               "artifacts": "custom"}})
                reqs = requests_for(prompt)
                lines = {d for r in reqs for d in r.get("allLines", [])}
                system = {d for r in reqs for d in r.get("systemLines", [])}
                has_skill, has_block = skill <= lines, block <= system
                if skills_on:
                    want = expected_reply(always_apply_texts() + [prompt])
                reply_ok = text_of(final_of(events).get("responseMessage", {})) == want
                good = bool(reqs) and reply_ok and has_block and has_skill == skills_on
                ok &= good
                results.append(f"{spec} skills={skills_on}: requests={len(reqs)} reply={reply_ok} "
                               f"skill_text={has_skill} brand_block={has_block}")
        return ok, "; ".join(results)
    check("M85", "the brand block of the instructions reaches the model in every chat, with or without internet; the "
          "Skill's whole text joins it when skills are on, and stays out when they are off", reaches_model)
