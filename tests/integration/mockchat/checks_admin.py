"""Admin Panel (ADR-0016, #141): the panel container on loopback, LibreChat's admin-only API, the admins' Settings link,
custom roles and groups that persist, the file policy winning for USER after a restart, and the drift check (M76–M82)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from . import harness
from .client import api, create_user, login, role
from .harness import ADMIN_BASE, ROOT, check, ctr, dc, run

# Every admin mount of LibreChat v0.8.8 (api/server/index.js) must refuse a USER.
ADMIN_ROUTES = ["/api/admin/verify", "/api/admin/users", "/api/admin/groups", "/api/admin/roles",
                "/api/admin/grants", "/api/admin/config", "/api/admin/audit-log"]
ROLE, GROUP = "EF_SYNTH_REVIEWER", "EF Synthetic Pilot"
# A member of its own: a role assignment replaces the user's role, so the chat users a/b must never be used here.
MEMBER = "synthetic.chat.panel@example.invalid"


def panel(path: str) -> tuple[int, str]:
    try:
        with harness.opener.open(ADMIN_BASE + path, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, ""


def admin_login(email: str, password: str, origin: str | None = None) -> int:
    req = urllib.request.Request(harness.BASE + "/api/admin/login/local", method="POST",
                                 data=json.dumps({"email": email, "password": password}).encode("utf-8"))
    req.add_header("Content-Type", "application/json")
    if origin:  # a browser on another site: the same-origin guard must refuse it
        req.add_header("Origin", origin)
        req.add_header("Sec-Fetch-Site", "cross-site")
    try:
        with harness.opener.open(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as err:
        return err.code


def drift() -> tuple[int, str]:
    out = run(str(ROOT / "scripts/operations/admin-config-drift.sh"), ctr("mongodb"))
    return out.returncode, (out.stdout + out.stderr).strip()


def admin_panel(st: dict) -> None:
    def panel_up():
        health, page = panel("/health"), panel("/login")
        published = dc("port", "admin-panel", "3000").stdout.strip()
        return (health[0] == 200 and page[0] == 200 and "<title>LibreChat Admin Panel</title>" in page[1]
                and published.startswith("127.0.0.1:"), f"health={health[0]} login={page[0]} published={published}")
    check("M76", "admin-panel is healthy and serves its sign-in page on loopback only", panel_up)

    def user_refused():
        codes = {path: api("GET", path, st["a"])[0] for path in ADMIN_ROUTES}
        return all(c == 403 for c in codes.values()), codes
    check("M77", "every /api/admin/* mount answers 403 to a USER", user_refused)

    def logins():
        pw, users = st["pw"], st["users"]
        codes = (admin_login("synthetic.chat.admin@example.invalid", pw["admin"]), admin_login(users["a"], pw["a"]),
                 admin_login("synthetic.chat.admin@example.invalid", pw["admin"], origin="https://evil.example.invalid"))
        return codes == (200, 403, 403), f"admin, USER, cross-site = {codes} (expected 200, 403, 403)"
    check("M78", "admin login: 200 for the administrator, 403 for a USER and for a cross-site origin", logins)

    def settings_link():
        admin = json.loads(api("GET", "/api/config", st["admin"])[1]).get("adminPanelURL")
        user = json.loads(api("GET", "/api/config", st["a"])[1]).get("adminPanelURL")
        return admin == harness.env_value("ADMIN_PANEL_URL") and user is None, f"admin={admin} user={user}"
    check("M79", "Settings link: /api/config gives adminPanelURL to the administrator only", settings_link)

    def roles_and_groups():
        st["pw"]["panel"] = harness.secrets.token_hex(12)
        create_user(MEMBER, "Synthetic Panel Member", "synthpanel", st["pw"]["panel"])
        uid = login(MEMBER, st["pw"]["panel"])[1]["user"]["id"]
        r = api("POST", "/api/admin/roles", st["admin"], {"name": ROLE, "description": "synthetic"})
        g = api("POST", "/api/admin/groups", st["admin"], {"name": GROUP, "description": "synthetic"})
        gid = (json.loads(g[1]).get("group") or {}).get("_id") if g[0] in (200, 201) else None
        m = api("POST", f"/api/admin/groups/{gid}/members", st["admin"], {"userId": uid}) if gid else (0, "")
        rm = api("POST", f"/api/admin/roles/{ROLE}/members", st["admin"], {"userId": uid})
        # The panel's role editor on a built-in role: allowed now, reset by roles-policy.js on the next start (M82, #218).
        u = api("PATCH", "/api/admin/roles/USER/permissions", st["admin"], {"permissions": {"MCP_SERVERS": {"USE": True}}})
        st["panel_group"] = gid
        codes = (r[0], g[0], m[0], rm[0], u[0])
        return all(c in (200, 201) for c in codes), f"role, group, group member, role member, USER edit = {codes}"
    check("M80", "the admin API creates a custom role and a group and adds a member (as the panel does)",
          roles_and_groups)

    def drift_detected():
        clean = drift()
        # interface permission fields are stripped from overrides (they live on roles); a UI field is a real override.
        o = api("PUT", f"/api/admin/config/role/{ROLE}", st["admin"],
                {"overrides": {"interface": {"customWelcome": "synthetic override"}}})
        p = api("PATCH", f"/api/admin/roles/{ROLE}/permissions", st["admin"], {"permissions": {"RUN_CODE": {"USE": True}}})
        dirty = drift()
        api("DELETE", f"/api/admin/config/role/{ROLE}", st["admin"])
        api("PATCH", f"/api/admin/roles/{ROLE}/permissions", st["admin"], {"permissions": {"RUN_CODE": {"USE": False}}})
        again = drift()
        found = "configs: 1" in dirty[1] and f"role {ROLE}: RUN_CODE.USE" in dirty[1]
        return (clean[0] == 0 and o[0] in (200, 201) and p[0] == 200 and dirty[0] == 1 and found and again[0] == 0,
                f"clean={clean[0]} override={o[0]} role={p[0]} dirty={dirty} after={again[0]}")
    check("M81", "drift check: passes clean, flags a config override and a custom role above USER, passes again",
          drift_detected)


def admin_after_restart(st: dict) -> None:
    def persisted():
        roles = [r["name"] for r in json.loads(api("GET", "/api/admin/roles", st["admin"])[1]).get("roles", [])]
        group = api("GET", f"/api/admin/groups/{st.get('panel_group')}", st["admin"])[0]
        mcp = role(st["a"], "USER").get("MCP_SERVERS", {}).get("USE")
        return ROLE in roles and group == 200 and mcp is False, f"roles={roles} group={group} USER MCP_SERVERS.USE={mcp}"
    check("M82", "after restart: the custom role and group persist; the panel's USER MCP edit is reset (roles-policy.js)",
          persisted)
