#!/usr/bin/env bash
# Model usage and estimated token cost (FinOps), read-only, from LibreChat's own records.
#
# Usage: scripts/operations/usage-report.sh <mongodb-container> [--month YYYY-MM] [--by-user] [--json]
#        scripts/operations/usage-report.sh --railway [--environment dev] [--month YYYY-MM] [--by-user] [--json]
#
# Source: every model call LibreChat bills is a pair of `transactions` documents (prompt and completion tokens, model,
# context `message`/`title`/...). The chat mode comes from the reply's `messages.endpoint` (joined on messageId; only
# that field is read, never message text). Reported per month, per mode (سريع / متأنٍّ / عميق, with or without
# internet), per model, per background context and, with --by-user, per user (email).
# Cost: an ESTIMATE from the list prices in qwen-list-prices.json (input and output tokens; cached-input discounts and
# idle-hour prices ignored, so an upper bound). The Qwen Cloud bill is the authoritative cost.
# Not measurable here (measured 2026-10-25, docs/architecture/ai-safe-defaults.md §4.2): the number of web searches (LibreChat
# keeps none and Qwen's OpenAI-compatible stream returns no count; searches are on the bill only), reasoning tokens
# apart from output tokens (included in completion), and the memory agent's calls (LibreChat records none).
# Read-only: it never changes data. Railway needs `railway ssh` (owner's SSH key, #141).
set -euo pipefail

usage() { sed -n '4,5p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
mode=""; ctr=""; env_args=(); month=""; by_user=false; as_json=false
case "${1:-}" in
  --railway) mode=railway; shift ;;
  ""|-*) usage ;;
  *) mode=docker; ctr="$1"; shift ;;
esac
while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment) [[ "$mode" == railway && -n "${2:-}" ]] || usage; env_args=(--environment "$2"); shift 2 ;;
    --month) [[ "${2:-}" =~ ^[0-9]{4}-(0[1-9]|1[0-2])$ ]] || usage; month="$2"; shift 2 ;;
    --by-user) by_user=true; shift ;;
    --json) as_json=true; shift ;;
    *) usage ;;
  esac
done

# Runs inside the mongodb container as the least-privilege application user (its credentials are that container's env).
# shellcheck disable=SC2016 # $MONGO_* expand inside the container, not here
shell='mongosh --quiet --norc "mongodb://127.0.0.1:27017/${MONGO_APP_DATABASE:-LibreChat}" -u "$MONGO_APP_USERNAME" \
  -p "$MONGO_APP_PASSWORD" --authenticationDatabase "${MONGO_APP_DATABASE:-LibreChat}" --eval "$0"'
js='const month = "'"$month"'";
const match = {};
if (month) {
  const start = new Date(month + "-01T00:00:00Z");
  const end = new Date(start); end.setUTCMonth(end.getUTCMonth() + 1);
  match.createdAt = { $gte: start, $lt: end };
}
const rows = db.transactions.aggregate([
  { $match: match },
  { $lookup: { from: "messages", let: { mid: "$messageId" }, as: "m", pipeline: [
    { $match: { $expr: { $eq: ["$messageId", "$$mid"] } } }, { $project: { _id: 0, endpoint: 1 } }, { $limit: 1 }] } },
  { $group: {
    _id: { month: { $dateToString: { format: "%Y-%m", date: "$createdAt" } }, user: "$user", model: "$model",
           context: "$context", endpoint: { $arrayElemAt: ["$m.endpoint", 0] }, tokenType: "$tokenType" },
    records: { $sum: 1 }, tokens: { $sum: { $abs: "$rawAmount" } } } },
]).toArray();
const users = {};
db.users.find({ _id: { $in: [...new Set(rows.map((r) => String(r._id.user)))].map((id) => ObjectId(id)) } },
              { email: 1 }).forEach((u) => { users[String(u._id)] = u.email; });
print(JSON.stringify(rows.map((r) => ({ ...r._id, user: users[String(r._id.user)] || String(r._id.user),
                                        records: r.records, tokens: r.tokens }))));'

if [[ "$mode" == docker ]]; then
  out="$(docker exec "$ctr" sh -c "$shell" "$js")"
else
  command -v "${RAILWAY_BIN:-railway}" >/dev/null || { echo "Railway CLI not found (https://docs.railway.com/cli)" >&2; exit 1; }
  out="$("${RAILWAY_BIN:-railway}" ssh --service mongodb "${env_args[@]}" -- sh -c "$shell" "$js")"
fi

python3 -I - "$out" "$(dirname "$0")/qwen-list-prices.json" "$by_user" "$as_json" <<'PY'
import json, sys
from collections import defaultdict
raw, prices_file, by_user, as_json = sys.argv[1], sys.argv[2], sys.argv[3] == "true", sys.argv[4] == "true"
rows = json.loads(raw.strip().splitlines()[-1])
prices = json.load(open(prices_file, encoding="utf-8"))
# Endpoints of infrastructure/common/librechat.yaml -> the composer's mode (patch 0022) and internet setting.
MODES = {"Qwen": "سريع / Fast · internet", "Qwen NoWeb": "سريع / Fast · no internet",
         "Qwen Thinking": "متأنٍّ / Careful · internet", "Qwen Thinking NoWeb": "متأنٍّ / Careful · no internet",
         "DeepSeek": "عميق / Deep · internet", "DeepSeek NoWeb": "عميق / Deep · no internet"}

def cost(model, prompt, completion):
    p = prices["models"].get(model)
    if p is None:
        return None
    return (prompt * p["input"] + completion * p["output"]) / prices["tokens_per_price"]

def bucket(r):
    if r["context"] != "message":
        return f"background: {r['context']}"
    return MODES.get(r.get("endpoint") or "", f"other: {r.get('endpoint') or 'unknown'}")

def table(key):
    acc = defaultdict(lambda: {"calls": 0, "prompt": 0, "completion": 0, "cost": 0.0, "priced": True})
    for r in rows:
        a = acc[key(r)]
        if r["tokenType"] == "prompt":
            a["calls"] += r["records"]; a["prompt"] += r["tokens"]
        elif r["tokenType"] == "completion":
            a["completion"] += r["tokens"]
        c = cost(r["model"], r["tokens"] if r["tokenType"] == "prompt" else 0,
                 r["tokens"] if r["tokenType"] == "completion" else 0)
        if c is None:
            a["priced"] = False
        else:
            a["cost"] += c
    return dict(sorted(acc.items()))

report = {"months": table(lambda r: r["month"]), "modes": table(lambda r: (r["month"], bucket(r))),
          "models": table(lambda r: (r["month"], r["model"]))}
if by_user:
    report["users"] = table(lambda r: (r["month"], r["user"]))
notes = [f"Estimated cost = list prices ({prices['region']}, {prices['retrieved']}), input and output tokens only; "
         "the Qwen Cloud bill is authoritative.",
         "Web searches: not counted here (no record in LibreChat, no count in Qwen's stream); read them from the bill "
         f"(list price {prices['search_per_1000_calls']} {prices['currency']} per 1000).",
         "Reasoning tokens are part of output tokens. The memory agent's calls are not recorded by LibreChat."]
if as_json:
    print(json.dumps({"report": {k: {" | ".join(x) if isinstance(x, tuple) else x: v for x, v in t.items()}
                                 for k, t in report.items()}, "notes": notes}, ensure_ascii=False, indent=1))
    sys.exit(0)
titles = {"months": "Per month", "modes": "Per month and mode", "models": "Per month and model",
          "users": "Per month and user"}
for name, t in report.items():
    print(f"\n## {titles[name]}\n")
    print("| key | calls | input tokens | output tokens | est. cost (USD) |\n|---|---:|---:|---:|---:|")
    for k, v in t.items():
        label = " · ".join(k) if isinstance(k, tuple) else k
        est = f"{v['cost']:.4f}" if v["priced"] else f"≥ {v['cost']:.4f} (unpriced model)"
        print(f"| {label} | {v['calls']} | {v['prompt']} | {v['completion']} | {est} |")
print()
for n in notes:
    print(f"- {n}")
PY
