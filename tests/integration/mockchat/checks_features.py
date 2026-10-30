"""LibreChat batch 1 checks (#125): conversation search on the private Meilisearch service (M49–M51, M54–M56),
shared links behind the login (M52) and one message answered by two models side by side (M53)."""

from __future__ import annotations

import json
import time
import urllib.parse

from .client import api, final_of, login, messages, read_stream, requests_for, start_chat, text_of, turn
from .harness import MARKDOWN, MODELS, PROJECT, ROOT, check, ctr, dc, run, wait_healthy

# Synthetic words that appear nowhere else in the suite: one Arabic, one English (FR-003 AC-1).
WORD_AR, WORD_EN = "الزعفرانة", "Quokkaville"
# #135: a word only the chat written while Meilisearch is down contains.
WORD_GAP = "Wombatfjord"


def search(token: str, term: str) -> list[dict]:
    """Messages found by the web client's search box (GET /api/messages?search=...)."""
    status, raw = api("GET", "/api/messages?search=" + urllib.parse.quote(term), token)
    return json.loads(raw).get("messages", []) if status == 200 else []


def found(token: str, term: str, convo: str, timeout: float = 20) -> bool:
    """Indexing is asynchronous (save hook, then Meilisearch's task queue): poll until the chat shows up."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if any(m.get("conversationId") == convo for m in search(token, term)):
            return True
        time.sleep(1)
    return False


def search_enabled(token: str) -> str:
    return api("GET", "/api/search/enable", token)[1].strip()


def meili_status(path: str, key: str | None) -> str:
    """HTTP status of a Meilisearch call made from the librechat container (with or without the master key)."""
    js = ("const [p, k] = process.argv.slice(1); fetch(process.env.MEILI_HOST + p, k ? { headers: "
          "{ Authorization: 'Bearer ' + k } } : {}).then(r => console.log(r.status)).catch(e => console.log(e.message))")
    args = ["docker", "exec", ctr("librechat"), "node", "-e", js, path] + ([key] if key else [])
    return run(*args).stdout.strip()


def features(st: dict) -> None:
    # Fresh tokens: the suite has run for a while and M55 restarts LibreChat.
    for who, email in (("a", st["users"]["a"]), ("b", st["users"]["b"]), ("admin", "synthetic.chat.admin@example.invalid")):
        status, body = login(email, st["pw"][who])
        if status == 200:
            st[who] = body["token"]

    def search_private():
        ports = run("docker", "port", ctr("meilisearch")).stdout.strip()
        nets = run("docker", "inspect", "-f", "{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}",
                   ctr("meilisearch")).stdout.split()
        key = run("docker", "exec", ctr("librechat"), "printenv", "MEILI_MASTER_KEY").stdout.strip()
        statuses = (meili_status("/indexes", None), meili_status("/indexes", key))
        enabled = search_enabled(st["a"])
        return (not ports and nets == [f"{PROJECT}_backend"] and statuses == ("401", "200") and enabled == "true",
                f"ports={ports} nets={nets} without/with key={statuses} enable={enabled}")
    check("M49", "conversation search is on: /api/search/enable = true; Meilisearch publishes no port, sits on the "
          "internal network only and answers 401 without its key", search_private)

    def finds_own_chat():
        prompt = f"سؤال اصطناعي عن مشروع {WORD_AR} في مدينة {WORD_EN} للتجربة."
        job, events, want = turn(st["a"], prompt, [])
        st["search"] = {"convo": job["conversationId"], "prompt": prompt}
        got = text_of(final_of(events).get("responseMessage", {}))
        ar, en = found(st["a"], WORD_AR, job["conversationId"]), found(st["a"], WORD_EN, job["conversationId"])
        return got == want and ar and en, f"reply_ok={got == want} arabic={ar} english={en}"
    check("M50", "search finds the user's own chat by an Arabic and by an English word (FR-003 AC-1)", finds_own_chat)

    def others_see_nothing():
        theirs = search(st["b"], WORD_AR) + search(st["b"], WORD_EN)
        admin = search(st["admin"], WORD_AR)
        leaked = [m.get("conversationId") for m in theirs + admin]
        return not leaked, f"other users' hits={leaked}"
    check("M51", "another user and the administrator searching the same words see none of it (FR-003 AC-2)",
          others_see_nothing)

    def shared_link_behind_login():
        convo = st["search"]["convo"]
        _, saved = messages(st["a"], convo)
        last = saved[-1]["messageId"] if saved else None
        status, raw = api("POST", f"/api/share/{convo}", st["a"], {"targetMessageId": last})
        share = json.loads(raw).get("shareId") if status == 200 else None
        if not share:
            return False, f"create HTTP {status}: {raw[:200]}"
        colleague, raw_b = api("GET", f"/api/share/{share}", st["b"])
        texts = [m.get("text", "") or text_of(m) for m in json.loads(raw_b).get("messages", [])] if colleague == 200 else []
        anonymous = api("GET", f"/api/share/{share}")[0]
        removed = api("DELETE", f"/api/share/{share}", st["a"])[0]
        after = api("GET", f"/api/share/{share}", st["b"])[0]
        return (colleague == 200 and st["search"]["prompt"] in texts and anonymous == 401 and removed == 200
                and after == 404, f"colleague={colleague} sees_prompt={st['search']['prompt'] in texts} "
                f"anonymous={anonymous} delete={removed} after_delete={after}")
    check("M52", "shared link: a signed-in colleague opens it, an anonymous visitor gets 401, the owner deletes it (404)",
          shared_link_behind_login)

    def side_by_side():
        prompt = "Synthetic question for two models side by side."
        added = {"endpoint": "Baseer Mock", "endpointType": "custom", "model": MODELS[-1]}
        status, job = start_chat(st["a"], prompt, extra={"addedConvo": added})
        if status != 200 or not isinstance(job, dict):
            return False, f"start HTTP {status}: {str(job)[:200]}"
        _, events = read_stream(st["a"], job)
        reply = text_of(final_of(events).get("responseMessage", {}))
        models = sorted(r.get("model") for r in requests_for(prompt))
        both = sorted([MODELS[0], MODELS[-1]])
        return (models == both and MARKDOWN.splitlines()[0] in reply,
                f"models asked={models} markdown_in_reply={MARKDOWN.splitlines()[0] in reply}")
    check("M53", "side-by-side compare: one message is answered by two models in the same turn (#125)", side_by_side)

    def outage_keeps_chat():
        dc("stop", "meilisearch")
        try:
            off = search_enabled(st["a"])
            _, events, want = turn(st["a"], "Synthetic question while search is down.", [])
            chat_ok = text_of(final_of(events).get("responseMessage", {})) == want
        finally:
            dc("start", "meilisearch")
        back = wait_healthy(("meilisearch",), timeout=120)[0] and search_enabled(st["a"]) == "true"
        return off == "false" and chat_ok and back, f"enable_while_down={off} chat_ok={chat_ok} back={back}"
    check("M54", "Meilisearch down: chats still work and the search box is hidden (enable=false); back up: search "
          "returns", outage_keeps_chat)

    def unindexed_caught_up():
        # Railway dev, 2026-10-22 (#135): LibreChat ran before Meilisearch was reachable, so most chats were saved
        # without reaching the index (MongoDB marks them `_meiliIndex: false`), while later ones were indexed. Upstream
        # skips the start-up sync below 1000 unindexed messages once anything is indexed: search found nothing.
        # Recreate exactly that state for one chat: in MongoDB unmarked, in Meilisearch absent; other chats indexed.
        job, _, _ = turn(st["a"], f"Synthetic chat about {WORD_GAP} saved before the index.", [])
        convo = job["conversationId"]
        indexed = found(st["a"], WORD_GAP, convo, timeout=30)
        _, saved = messages(st["a"], convo)
        key = run("docker", "exec", ctr("librechat"), "printenv", "MEILI_MASTER_KEY").stdout.strip()
        js = ("const [k, c, ids] = process.argv.slice(1); const h = { Authorization: 'Bearer ' + k, "
              "'Content-Type': 'application/json' }; const u = process.env.MEILI_HOST + '/indexes/';"
              "Promise.all([fetch(u + 'messages/documents/delete-batch', { method: 'POST', headers: h, body: ids }),"
              "fetch(u + 'convos/documents/delete-batch', { method: 'POST', headers: h, body: JSON.stringify([c]) })])"
              ".then(r => console.log(r.map(x => x.status).join(' '))).catch(e => console.log(e.message))")
        deleted = run("docker", "exec", ctr("librechat"), "node", "-e", js, key, convo,
                      json.dumps([m["messageId"] for m in saved])).stdout.strip()
        unmark = (f"for (const n of ['messages', 'conversations']) {{ const r = db.getCollection(n).updateMany("
                  f"{{ conversationId: {json.dumps(convo)} }}, {{ $set: {{ _meiliIndex: false }} }});"
                  f" print(n + '=' + r.modifiedCount); }}")
        marked = run("docker", "exec", ctr("mongodb"), "sh", "-c",
                     'mongosh --quiet --norc "mongodb://127.0.0.1:27017/${MONGO_APP_DATABASE:-LibreChat}" '
                     '-u "$MONGO_APP_USERNAME" -p "$MONGO_APP_PASSWORD" --authenticationDatabase '
                     '"${MONGO_APP_DATABASE:-LibreChat}" --eval "$0"', unmark).stdout.split()
        time.sleep(3)
        missing = not found(st["a"], WORD_GAP, convo, timeout=5)
        dc("restart", "librechat")
        again = wait_healthy()[0] and found(st["a"], WORD_GAP, convo, timeout=60)
        return (indexed and deleted == "202 202" and missing and again and not search(st["b"], WORD_GAP),
                f"indexed_first={indexed} delete={deleted} unmarked={marked} missing_before_restart={missing} "
                f"found_after_restart={again}")
    check("M70", "a chat that never reached the index (MongoDB unmarked, as on Railway dev on 2026-10-22) is found "
          "after LibreChat's next start, although other chats are indexed (MEILI_SYNC_THRESHOLD=0, #135)",
          unindexed_caught_up)

    def rebuild_after_lost_index():
        convo = st["search"]["convo"]
        dc("rm", "-sfv", "meilisearch")
        run("docker", "volume", "rm", f"{PROJECT}_meilisearch-data")
        dc("up", "-d", "meilisearch")
        if not wait_healthy(("meilisearch",), timeout=120)[0]:
            return False, "meilisearch not healthy on an empty volume"
        dc("restart", "librechat")
        again = wait_healthy()[0] and found(st["a"], WORD_AR, convo, timeout=60)
        return again and not search(st["b"], WORD_AR), f"found_again={again}"
    check("M55", "lost Meilisearch volume: on its next start LibreChat rebuilds the index from MongoDB; still per user",
          rebuild_after_lost_index)

    def reindex_script():
        # The gap search-reindex.sh closes (e.g. after a database restore): MongoDB marks a chat as indexed, the index
        # does not hold it. Recreate that state by deleting the chat's documents from the index only.
        convo = st["search"]["convo"]
        _, saved = messages(st["a"], convo)
        key = run("docker", "exec", ctr("librechat"), "printenv", "MEILI_MASTER_KEY").stdout.strip()
        js = ("const [k, c, ids] = process.argv.slice(1); const h = { Authorization: 'Bearer ' + k, "
              "'Content-Type': 'application/json' }; const u = process.env.MEILI_HOST + '/indexes/';"
              "Promise.all([fetch(u + 'messages/documents/delete-batch', { method: 'POST', headers: h, body: ids }),"
              "fetch(u + 'convos/documents/delete-batch', { method: 'POST', headers: h, body: JSON.stringify([c]) })])"
              ".then(r => console.log(r.map(x => x.status).join(' '))).catch(e => console.log(e.message))")
        ids = json.dumps([m["messageId"] for m in saved])
        deleted = run("docker", "exec", ctr("librechat"), "node", "-e", js, key, convo, ids).stdout.strip()
        time.sleep(3)
        gone = not found(st["a"], WORD_AR, convo, timeout=5)
        dc("restart", "librechat")
        still_gone = wait_healthy()[0] and not found(st["a"], WORD_AR, convo, timeout=5)
        out = run(str(ROOT / "scripts/operations/search-reindex.sh"), ctr("mongodb"), ctr("librechat"))
        again = wait_healthy()[0] and found(st["a"], WORD_AR, convo, timeout=60)
        return (deleted == "202 202" and gone and still_gone and out.returncode == 0 and again
                and not search(st["b"], WORD_AR),
                f"delete={deleted} gone={gone} gone_after_restart={still_gone} reindex_exit={out.returncode} "
                f"found_again={again} {out.stderr[-200:]}")
    check("M56", "index missing chats MongoDB marks as indexed (as after a restore): a restart alone does not help, "
          "search-reindex.sh does; still per user", reindex_script)
