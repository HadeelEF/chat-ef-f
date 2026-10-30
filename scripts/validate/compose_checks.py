#!/usr/bin/env python3
"""Static security/policy checks for the Docker Compose stacks in infrastructure/compose (no containers started).

Enforces the deployment policy of ADR-0007/ADR-0008 for both Compose profiles (Windows local, Ubuntu on-prem):
digest-pinned images, no published ports in the base file, one entry point per profile (loopback locally for LibreChat
and the Admin Panel, the HTTPS proxy on-prem), private MongoDB and Meilisearch with authentication, an Admin Panel that
never reaches the internal network (ADR-0016), healthchecks, dropped capabilities,
required secrets, the shared application policy (infrastructure/common/librechat.env: registration as approved, ...),
config-version match and a placeholder-only .env.example. When the docker CLI is available it also renders both
profiles with throwaway values and proves rendering fails when required secrets are missing.

Usage: python3 scripts/validate/compose_checks.py      (exit 0 = pass, 1 = fail)
"""

from __future__ import annotations

import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "infrastructure/common"
STACK = ROOT / "infrastructure/compose"
COMPOSE = STACK / "compose.yaml"
LOCAL = STACK / "compose.local.yaml"
ONPREM = STACK / "compose.onprem.yaml"
ENV_EXAMPLE = STACK / ".env.example"
LIBRECHAT_YAML = COMMON / "librechat.yaml"
POLICY_ENV = COMMON / "librechat.env"

# librechat.yaml `version` expected by each pinned LibreChat release (packages/data-provider CONFIG_VERSION).
CONFIG_VERSION = {"v0.8.8": "1.3.17"}
PINNED_IMAGE = re.compile(r"^[a-z0-9./_-]+:[\w.-]+@sha256:[0-9a-f]{64}$")
REQUIRED_SECRETS = [
    "CREDS_KEY", "CREDS_IV", "JWT_SECRET", "JWT_REFRESH_SECRET",
    "MONGO_ROOT_USERNAME", "MONGO_ROOT_PASSWORD", "MONGO_APP_USERNAME", "MONGO_APP_PASSWORD", "MEILI_MASTER_KEY",
    "DOMAIN_CLIENT", "DOMAIN_SERVER", "ADMIN_PANEL_URL", "ADMIN_PANEL_SESSION_SECRET",
]
ONPREM_REQUIRED = ["EFAIW_HOSTNAME", "EFAIW_ADMIN_HOSTNAME", "EFAIW_TLS"]
SERVICES = {"librechat", "mongodb", "meilisearch", "admin-panel"}
# Services that may publish a loopback port in compose.local.yaml (the two user-facing entry points).
LOCAL_PUBLISHED = {"librechat", "admin-panel"}
# Security-relevant application policy that every environment must keep (ADR-0008; changing one needs a decision).
REQUIRED_POLICY = {
    "ALLOW_REGISTRATION": "false",  # LibreChat's registration form closed, owner decision (ADR-0024)
    "ALLOW_SOCIAL_LOGIN": "false",
    "ALLOW_SOCIAL_REGISTRATION": "false",
    "ALLOW_PASSWORD_RESET": "false",
    "ALLOW_UNVERIFIED_EMAIL_LOGIN": "false",
    "ALLOW_SHARED_LINKS_PUBLIC": "false",
    "DEBUG_LOGGING": "false",
    "CONFIG_PATH": "/app/librechat.yaml",
}
SECRET_NAME = re.compile(r"(SECRET|PASSWORD|TOKEN|_KEY|_IV|URI|URL)$")
# Fixed, environment-independent values allowed for keys that SECRET_NAME would otherwise reject (exact match only).
POLICY_SENTINELS = {"HELP_AND_FAQ_URL": "/assets/ef-help.html"}  # same-origin EF help page (#43, #103); any other URL is rejected

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line)
        if m:
            values[m.group(1)] = m.group(2).strip()
    return values


def check_hardening(name: str, svc: dict) -> None:
    image = svc.get("image", "")
    if not PINNED_IMAGE.match(image):
        fail(f"{name}: image must be pinned by tag and digest, got '{image}'")
    if "healthcheck" not in svc:
        fail(f"{name}: healthcheck missing")
    if "no-new-privileges:true" not in (svc.get("security_opt") or []):
        fail(f"{name}: security_opt no-new-privileges:true missing")
    if "ALL" not in (svc.get("cap_drop") or []):
        fail(f"{name}: cap_drop ALL missing")


def check_policy() -> dict[str, str]:
    policy = parse_env(POLICY_ENV)
    for key, expected in REQUIRED_POLICY.items():
        if policy.get(key) != expected:
            fail(f"librechat.env: {key} must be {expected!r}, got {policy.get(key)!r}")
    if policy.get("SCHEDULES_SINGLE_PROCESS") not in (None, "false", "true"):
        fail("librechat.env: SCHEDULES_SINGLE_PROCESS must be true or false")
    for key in policy:
        if SECRET_NAME.search(key) and POLICY_SENTINELS.get(key) != policy[key]:
            fail(f"librechat.env: {key} looks environment-specific or secret; it does not belong in the shared policy")
    return policy


def check_base(policy: dict[str, str]) -> None:
    compose = load(COMPOSE)
    services: dict = compose.get("services", {})
    networks: dict = compose.get("networks", {}) or {}
    raw = COMPOSE.read_text(encoding="utf-8")

    if set(services) != SERVICES:
        fail(f"compose.yaml must contain exactly {' + '.join(sorted(SERVICES))}, found {sorted(services)}")
    for name, svc in services.items():
        check_hardening(name, svc)
        if "ports" in svc:
            fail(f"{name}: compose.yaml must not publish ports (use compose.local.yaml or compose.onprem.yaml)")

    mongo = services.get("mongodb", {})
    if "--auth" not in (mongo.get("command") or []):
        fail("mongodb: must run with --auth")
    for net in mongo.get("networks", []):
        if not (networks.get(net) or {}).get("internal"):
            fail(f"mongodb: network '{net}' must be internal")

    # Conversation search (#125): the index holds chat text, so it is as private as MongoDB.
    meili = services.get("meilisearch", {})
    meili_env = meili.get("environment") or {}
    if meili_env.get("MEILI_ENV") != "production" or str(meili_env.get("MEILI_NO_ANALYTICS")).lower() != "true":
        fail("meilisearch: needs MEILI_ENV=production (master key mandatory) and MEILI_NO_ANALYTICS=true")
    if not meili.get("networks") or any(not (networks.get(n) or {}).get("internal") for n in meili.get("networks", [])):
        fail("meilisearch: must be attached to internal networks only")

    # Admin Panel (ADR-0016): talks to LibreChat only, on the frontend network; no data, no internal network.
    panel = services.get("admin-panel", {})
    panel_env = panel.get("environment") or {}
    if panel.get("networks") != ["frontend"]:
        fail("admin-panel: must be attached to the frontend network only (never to backend)")
    if panel_env.get("API_SERVER_URL") != "http://librechat:3080":
        fail("admin-panel: API_SERVER_URL must be the private service http://librechat:3080")
    if str(panel_env.get("SESSION_COOKIE_SECURE")).lower() != "true":
        fail("admin-panel: SESSION_COOKIE_SECURE must be true in compose.yaml (only compose.local.yaml may relax it)")
    if panel.get("volumes"):
        fail("admin-panel: holds no data and must not mount volumes")

    app = services.get("librechat", {})
    if (app.get("environment") or {}).get("MEILI_HOST") != "http://meilisearch:7700":
        fail("librechat: MEILI_HOST must be the private service http://meilisearch:7700")
    env_files = [e["path"] if isinstance(e, dict) else e for e in (app.get("env_file") or [])]
    if env_files != ["../common/librechat.env"]:
        fail(f"librechat: env_file must be exactly ../common/librechat.env, got {env_files}")
    overlap = set(app.get("environment") or {}) & set(policy)
    if overlap:
        fail(f"librechat: {sorted(overlap)} are set in compose.yaml and librechat.env; keep policy in librechat.env only")
    replicas = (app.get("deploy") or {}).get("replicas", 1)
    if policy.get("SCHEDULES_SINGLE_PROCESS") == "true" and int(replicas) != 1:
        fail("librechat: SCHEDULES_SINGLE_PROCESS=true asserts exactly one replica (set deploy.replicas to 1)")
    for var in REQUIRED_SECRETS:
        if not re.search(r"\$\{" + var + r":\?", raw):
            fail(f"required variable {var} must use ${{{var}:?...}} (no default)")

    tag = app.get("image", "").split("@")[0].rpartition(":")[2]
    expected = CONFIG_VERSION.get(tag)
    actual = str(load(LIBRECHAT_YAML).get("version"))
    if expected is None:
        fail(f"no known librechat.yaml config version for LibreChat {tag}; update CONFIG_VERSION")
    elif actual != expected:
        fail(f"librechat.yaml version {actual} != {expected} expected by LibreChat {tag}")


def check_local() -> None:
    services = load(LOCAL).get("services") or {}
    for name, svc in services.items():
        ports = svc.get("ports", [])
        if ports and name not in LOCAL_PUBLISHED:
            fail(f"compose.local.yaml {name}: only {' and '.join(sorted(LOCAL_PUBLISHED))} may publish a port locally")
        for port in ports:
            if not str(port).startswith("127.0.0.1:"):
                fail(f"compose.local.yaml {name}: port '{port}' must bind 127.0.0.1 only")


def check_onprem() -> None:
    data = load(ONPREM)
    services = data.get("services") or {}
    raw = ONPREM.read_text(encoding="utf-8")
    for name, svc in services.items():
        if name != "proxy" and "ports" in svc:
            fail(f"compose.onprem.yaml {name}: only the proxy may publish ports on-prem")
    proxy = services.get("proxy")
    if not proxy:
        fail("compose.onprem.yaml: proxy service missing")
        return
    check_hardening("proxy", proxy)
    targets = sorted(str(p).rsplit(":", 1)[-1] for p in proxy.get("ports", []))
    if targets != ["443", "80"]:
        fail(f"proxy: must publish exactly container ports 80 and 443, got {targets}")
    if proxy.get("networks") != ["frontend"]:
        fail("proxy: must be attached to the frontend network only (never to backend)")
    if set(proxy.get("cap_add") or []) - {"NET_BIND_SERVICE"}:
        fail("proxy: only NET_BIND_SERVICE may be added back")
    for var in ONPREM_REQUIRED:
        if not re.search(r"\$\{" + var + r":\?", raw):
            fail(f"compose.onprem.yaml: {var} must use ${{{var}:?...}} (no default)")


def check_env_example() -> None:
    for key, value in parse_env(ENV_EXAMPLE).items():
        if key in REQUIRED_SECRETS + ONPREM_REQUIRED and value:
            fail(f".env.example: {key} must be empty (placeholder only)")


def check_render() -> None:
    if not shutil.which("docker"):
        print("NOTE  docker CLI not found: rendering checks skipped", file=sys.stderr)
        return
    for override in (LOCAL, ONPREM):
        base = ["docker", "compose", "-f", str(COMPOSE), "-f", str(override)]
        with tempfile.NamedTemporaryFile("w", suffix=".env") as env:
            for var in REQUIRED_SECRETS + ONPREM_REQUIRED:
                value = "http://localhost:3080" if var.startswith(("DOMAIN_", "ADMIN_PANEL_URL")) else secrets.token_hex(16)
                env.write(f"{var}={value}\n")
            env.flush()
            ok = subprocess.run([*base, "--env-file", env.name, "config", "--quiet"], capture_output=True, text=True)
            if ok.returncode != 0:
                fail(f"{override.name}: docker compose config failed with a complete env file: {ok.stderr.strip()[:300]}")
        bad = subprocess.run([*base, "--env-file", str(ENV_EXAMPLE), "config", "--quiet"], capture_output=True, text=True)
        if bad.returncode == 0 or "required variable" not in bad.stderr:
            fail(f"{override.name}: docker compose config must refuse the unfilled .env.example")


def main() -> int:
    policy = check_policy()
    check_base(policy)
    check_local()
    check_onprem()
    check_env_example()
    check_render()
    if failures:
        print("FAIL  compose_checks", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("PASS  compose_checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
