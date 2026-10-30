#!/usr/bin/env python3
"""Offline policy checks for the Railway environment (.railway/railway.ts + infrastructure/railway/).

No Railway account, token or network access is used: `railway config plan` needs authentication, so this is the
static layer only (ADR-0008). Checks:
  - Config as Code files (railway.json / railway.toml) are absent: deprecated by Railway (hard cutoff 2026-12-01);
  - the SDK is pinned exactly and locked (.railway/package.json + package-lock.json);
  - the derived Dockerfiles build FROM the exact digests pinned in infrastructure/compose/compose.yaml (final stage;
    earlier build stages, such as the Arabic web client of ADR-0013, are named and pinned by version and digest),
    COPY only from infrastructure/common, infrastructure/railway, ai/skills and ai/prompts (ADR-0017, ADR-0018), and
    map LibreChat's persistent paths into /app/storage;
    the Admin Panel image keeps its ADR-0016 exit guard and runs as the upstream `bun` user;
  - railway.ts, evaluated offline exactly like the Railway CLI does (node --experimental-strip-types, pinned SDK):
    four services, one volume each for the three data services at the expected paths and none for the Admin Panel,
    one replica, and the owner-approved targets (#16 D3: region europe-west4-drams3a, 5 GB volumes, 2 vCPU/2 GB
    librechat, 1 vCPU/1 GB mongodb and meilisearch, #125; 1 vCPU/512 MB admin-panel, #141),
    private MongoDB and Meilisearch (no domain, no TCP proxy), Admin Panel URLs built from Railway references only,
    /health healthcheck, Dockerfile builds, deployment source = exactly this repository's `main` branch with Wait for
    CI off and watch paths equal to the Dockerfile + its COPY sources (autodeploy, ADR-0010), cost guardrails, application
    policy identical to infrastructure/common/librechat.env, secrets only as preserve(), MONGO_URI and MEILI_HOST
    built from Railway references to the private domains only, MEILI_MASTER_KEY only as a reference;
  - TypeScript type-check of railway.ts against the pinned SDK types (tsc --noEmit).
The evaluation and type-check need Node >= 22.6 and `npm ci --prefix .railway`; without them they are reported
as SKIPPED (never as passed) and the script exits 1 unless --allow-skip is given.

Usage: python3 scripts/validate/railway_checks.py [--allow-skip]
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IAC_DIR = ROOT / ".railway"
IAC_FILE = IAC_DIR / "railway.ts"
RAILWAY_DIR = ROOT / "infrastructure/railway"
AI_ASSETS = ("ai/skills", "ai/prompts")  # runtime AI assets baked into the image (ADR-0017, ADR-0018)
COMPOSE = ROOT / "infrastructure/compose/compose.yaml"
POLICY_ENV = ROOT / "infrastructure/common/librechat.env"
EVALUATOR = ROOT / "scripts/validate/railway_eval.mjs"
SDK_VERSION = "3.16.0"
# ADR-0010: the only deployment source allowed — this repository, branch main, no Wait for CI (no GitHub Actions).
APPROVED_SOURCE = {"type": "github", "repo": "faenazi/ef-ai-workspace", "branch": "main", "checkSuites": False}
# Owner-approved Railway target configuration (#16 D3, 2026-10-18). Changing any value needs a new owner decision.
APPROVED_REGION = "europe-west4-drams3a"
APPROVED_VOLUME_MB = 5_000
APPROVED_LIMITS = {  # service -> (vCPU, memory bytes)
    "librechat": (2, 2_000_000_000),
    "mongodb": (1, 1_000_000_000),
    "meilisearch": (1, 1_000_000_000),  # conversation search, same envelope as mongodb (owner approval of batch 1, #125)
    "admin-panel": (1, 512_000_000),  # LibreChat Admin Panel (owner authorisation 2026-10-23, #141; ADR-0016)
}

SECRETS = {
    "mongodb": {"MONGO_INITDB_ROOT_USERNAME", "MONGO_INITDB_ROOT_PASSWORD", "MONGO_APP_PASSWORD"},
    "meilisearch": {"MEILI_MASTER_KEY"},
    "librechat": {"CREDS_KEY", "CREDS_IV", "JWT_SECRET", "JWT_REFRESH_SECRET", "QWEN_API_KEY"},
    "admin-panel": {"SESSION_SECRET"},
}
EXPECTED = {  # service -> (dockerfile, volume name, mount path); no volume = None
    "mongodb": ("infrastructure/railway/mongodb.Dockerfile", "mongodb-data", "/data/db"),
    "meilisearch": ("infrastructure/railway/meilisearch.Dockerfile", "meilisearch-data", "/meili_data"),
    "librechat": ("infrastructure/railway/librechat.Dockerfile", "librechat-storage", "/app/storage"),
    "admin-panel": ("infrastructure/railway/admin-panel.Dockerfile", None, None),
}
# compose.yaml image repository -> Railway service (exact repository names: librechat-admin-panel contains "librechat").
COMPOSE_REPOSITORIES = {
    "ghcr.io/librechat-ai/librechat": "librechat",
    "ghcr.io/librechat-ai/librechat-admin-panel": "admin-panel",
    "mongo": "mongodb",
    "getmeili/meilisearch": "meilisearch",
}
MONGO_URI = (
    "mongodb://${{mongodb.MONGO_APP_USERNAME}}:${{mongodb.MONGO_APP_PASSWORD}}@${{mongodb.RAILWAY_PRIVATE_DOMAIN}}"
    ":27017/${{mongodb.MONGO_APP_DATABASE}}?authSource=${{mongodb.MONGO_APP_DATABASE}}"
)
PUBLIC_URL = "https://${{RAILWAY_PUBLIC_DOMAIN}}"
# Conversation search (#125): the private domain and a reference to the key the meilisearch service holds (never a copy).
MEILI = {"MEILI_HOST": "http://${{meilisearch.RAILWAY_PRIVATE_DOMAIN}}:7700",
         "MEILI_MASTER_KEY": "${{meilisearch.MEILI_MASTER_KEY}}"}
# Admin Panel (ADR-0016): every URL is a Railway reference; the panel reaches LibreChat over the private network.
ADMIN_PANEL_URL = "https://${{admin-panel.RAILWAY_PUBLIC_DOMAIN}}"
ADMIN_PANEL_ENV = {"PORT": "3000",
                   "API_SERVER_URL": "http://${{librechat.RAILWAY_PRIVATE_DOMAIN}}:3080",
                   "VITE_API_BASE_URL": "https://${{librechat.RAILWAY_PUBLIC_DOMAIN}}"}

failures: list[str] = []
skipped: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def compose_images() -> dict[str, str]:
    images: dict[str, str] = {}
    for line in COMPOSE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s+image:\s+(\S+)$", line)
        if m:
            key = COMPOSE_REPOSITORIES.get(m.group(1).split("@")[0].rpartition(":")[0])
            if key:
                images[key] = m.group(1)
    return images


def check_no_config_as_code() -> None:
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                             check=True, capture_output=True, text=True).stdout.splitlines()
    for rel in tracked:
        if Path(rel).name in ("railway.json", "railway.toml"):
            fail(f"{rel}: Railway Config as Code is deprecated; use .railway/railway.ts (ADR-0008)")


def check_sdk_pin() -> None:
    pkg = json.loads((IAC_DIR / "package.json").read_text(encoding="utf-8"))
    if pkg.get("dependencies", {}).get("railway") != SDK_VERSION:
        fail(f".railway/package.json: railway SDK must be pinned exactly to {SDK_VERSION}")
    for section in ("dependencies", "devDependencies"):
        for name, spec in pkg.get(section, {}).items():
            if not re.match(r"^\d+\.\d+\.\d+$", spec):
                fail(f".railway/package.json: {name} must be an exact version, got {spec!r}")
    lock = IAC_DIR / "package-lock.json"
    if not lock.is_file():
        fail(".railway/package-lock.json missing (needed for reproducible `npm ci`)")
        return
    packages = json.loads(lock.read_text(encoding="utf-8")).get("packages", {})
    for path, meta in packages.items():
        if path and not meta.get("integrity"):
            fail(f".railway/package-lock.json: {path} has no integrity hash")


def copy_sources(text: str) -> list[str]:
    """Build-context sources of COPY instructions (copies between stages, COPY --from=..., are not inputs)."""
    return re.findall(r"^COPY\s+(?:(?!--from=)--\S+\s+)*(?!--)(\S+)\s+\S+$", text, re.M)


def watch_paths(dockerfile: str) -> set[str]:
    """Expected watch paths: the Dockerfile itself plus every COPY source (directories as dir/**), rooted at /."""
    text = (ROOT / dockerfile).read_text(encoding="utf-8")
    paths = {"/" + dockerfile}
    for src in copy_sources(text):
        paths.add("/" + src.rstrip("/") + "/**" if (ROOT / src).is_dir() else "/" + src)
    return paths


def check_dockerfiles() -> None:
    images = compose_images()
    for service, (dockerfile, _, _) in EXPECTED.items():
        text = (ROOT / dockerfile).read_text(encoding="utf-8")
        stages = re.findall(r"^FROM\s+(\S+)(?:\s+AS\s+(\S+))?\s*$", text, re.M)
        if not stages or stages[-1] != (images.get(service), ""):
            fail(f"{dockerfile}: the final stage must be exactly FROM the compose.yaml image {images.get(service)}, "
                 f"got {stages[-1][0] if stages else None}")
        for image, name in stages[:-1]:
            if not name or not re.fullmatch(r"[^\s:@]+:[^\s@]+@sha256:[0-9a-f]{64}", image):
                fail(f"{dockerfile}: build stage {image} must be named (AS ...) and pinned by version and digest")
        for src in copy_sources(text):
            if not src.startswith(("infrastructure/common/", "infrastructure/railway/")) and src not in AI_ASSETS:
                fail(f"{dockerfile}: COPY source {src} outside infrastructure/common, infrastructure/railway or "
                     f"{', '.join(AI_ASSETS)}")
            elif not (ROOT / src).exists():
                fail(f"{dockerfile}: COPY source {src} does not exist")
        if not re.search(r"^ENTRYPOINT \[\"/usr/local/bin/efaiw-", text, re.M):
            fail(f"{dockerfile}: must start through its efaiw start guard (missing-secret protection)")
    app = (ROOT / EXPECTED["librechat"][0]).read_text(encoding="utf-8")
    for link, target in (("/app/uploads", "uploads"), ("/app/client/public/images", "images"), ("/app/data", "data")):
        if f"ln -s /app/storage/{target} {link}" not in app:
            fail(f"librechat.Dockerfile: {link} must be a symlink to /app/storage/{target} (single Railway volume)")
    if "COPY --chmod=0444 infrastructure/common/librechat.yaml /app/librechat.yaml" not in app:
        fail("librechat.Dockerfile: must bake infrastructure/common/librechat.yaml read-only at /app/librechat.yaml")
    start = (RAILWAY_DIR / "librechat-start.sh").read_text(encoding="utf-8")
    if "exec su -s /bin/sh node" not in start:
        fail("librechat-start.sh: LibreChat must be started as the node user (privilege drop)")
    if "unset ADMIN_PANEL_URL" not in start:
        fail("librechat-start.sh: must drop ADMIN_PANEL_URL while the panel has no domain (ADR-0016)")
    panel = (ROOT / EXPECTED["admin-panel"][0]).read_text(encoding="utf-8")
    if "want @tanstack/react-start" not in panel:
        fail("admin-panel.Dockerfile: the ADR-0016 exit guard on the base image's react-start version is missing")
    if re.findall(r"^USER\s+(\S+)", panel, re.M)[-1:] != ["bun"]:
        fail("admin-panel.Dockerfile: the panel must run as the upstream bun user (last USER instruction)")


def node_ready() -> str | None:
    node = shutil.which("node")
    if not node:
        return "node not found"
    major, minor = (int(x) for x in subprocess.run([node, "-p", "process.versions.node"], capture_output=True,
                                                   text=True).stdout.strip().split(".")[:2])
    if (major, minor) < (22, 6):
        return f"node {major}.{minor} < 22.6 (needs --experimental-strip-types)"
    if not (IAC_DIR / "node_modules/railway/package.json").is_file():
        return "SDK not installed (run: npm ci --prefix .railway)"
    return None


def evaluate() -> dict | None:
    proc = subprocess.run(
        ["node", "--experimental-strip-types", "--disable-warning=ExperimentalWarning", str(EVALUATOR), "dev"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        fail(f"railway.ts evaluation failed: {proc.stderr.strip()[:500]}")
        return None
    return json.loads(proc.stdout)


def total_replicas(deploy: dict) -> int:
    regions = deploy.get("multiRegionConfig") or {}
    if regions:
        return sum(int((cfg or {}).get("numReplicas") or 0) for cfg in regions.values())
    return int(deploy.get("numReplicas") or 1)


def check_graph(project: dict) -> None:
    resources = project.get("resources", [])
    services = {r["name"]: r for r in resources if r.get("type") == "service"}
    volumes = {r["name"]: r for r in resources if r.get("type") == "volume"}
    if any(r.get("type") in ("database", "bucket") for r in resources):
        fail("railway.ts: managed database/bucket helpers are not used (MongoDB is built from the pinned image)")
    if set(services) != set(EXPECTED):
        fail(f"railway.ts: services must be exactly {sorted(EXPECTED)}, got {sorted(services)}")
    expected_volumes = {v for _, v, _ in EXPECTED.values() if v}
    if set(volumes) != expected_volumes:
        fail(f"railway.ts: volumes must be exactly {sorted(expected_volumes)}, got {sorted(volumes)}")
    for name, vol in volumes.items():
        config = vol.get("config") or {}
        if config.get("sizeMB") != APPROVED_VOLUME_MB:
            fail(f"volume {name}: sizeMB must be the approved {APPROVED_VOLUME_MB} (#16 D3; Railway Pro default is 50 GB)")
        if config.get("region") != APPROVED_REGION:
            fail(f"volume {name}: region must be the approved {APPROVED_REGION} (#16 D3)")
    policy = parse_env(POLICY_ENV)

    for name, (dockerfile, volume_name, mount) in EXPECTED.items():
        svc = services.get(name)
        if not svc:
            continue
        source, build, deploy = svc.get("source", {}), svc.get("build", {}), svc.get("deploy", {})
        if source != APPROVED_SOURCE:
            fail(f"{name}: deployment source must be exactly {APPROVED_SOURCE} (autodeploy from main, ADR-0010), "
                 f"got {source}")
        if set(build.get("watchPatterns") or []) != watch_paths(dockerfile):
            fail(f"{name}: watch paths must be exactly {sorted(watch_paths(dockerfile))} (the Dockerfile and its COPY "
                 "sources) so a push to main redeploys only when the image changes (ADR-0010)")
        if build.get("builder") != "DOCKERFILE" or build.get("dockerfilePath") != dockerfile:
            fail(f"{name}: must build {dockerfile} with the DOCKERFILE builder")
        if deploy.get("startCommand"):
            fail(f"{name}: no startCommand (it would bypass the image's start guard)")
        attachments = svc.get("volumeAttachments") or {}
        if volume_name is None:
            if svc.get("volumeMounts") or attachments:
                fail(f"{name}: holds no data and must not mount a volume")
        elif svc.get("volumeMounts") or list(attachments) != [volume_name] or attachments[volume_name]["mountPath"] != mount:
            fail(f"{name}: must mount exactly volume {volume_name} at {mount} (Railway: one volume per service)")
        if total_replicas(deploy) != 1:
            fail(f"{name}: exactly one replica (volumes forbid replicas; SCHEDULES_SINGLE_PROCESS=true)")
        if list((deploy.get("multiRegionConfig") or {})) != [APPROVED_REGION]:
            fail(f"{name}: must run in the approved region {APPROVED_REGION} (#16 D3)")
        limits = ((deploy.get("limitOverride") or {}).get("containers") or {})
        if (limits.get("cpu"), limits.get("memoryBytes")) != APPROVED_LIMITS[name]:
            fail(f"{name}: resource caps must be the approved {APPROVED_LIMITS[name]} (vCPU, bytes) — #16 D3")
        networking = svc.get("networking") or {}
        if networking.get("tcpProxies"):
            fail(f"{name}: TCP proxies are not allowed (no public database or raw TCP exposure)")
        if networking.get("customDomains"):
            fail(f"{name}: custom domains are an owner decision outside IaC (Railway rejects new ones in config)")
        if networking.get("serviceDomains"):
            fail(f"{name}: no public Railway domain in IaC (SC-18/D5 gate: generated by hand only after security "
                 "clearance and authorisation on #15)")

        variables = svc.get("variables") or {}
        for key in SECRETS[name]:
            if (variables.get(key) or {}).get("type") != "preserve":
                fail(f"{name}.{key}: secrets must be declared as preserve(), never as values in Git")
        for key, var in variables.items():
            if var.get("type") == "raw" and (var.get("value") or {}).get("value"):
                fail(f"{name}.{key}: raw variable values are not allowed")
            if var.get("type") == "literal" and key not in SECRETS[name]:
                value = str(var.get("value", ""))
                if name == "librechat" and MEILI.get(key) == value:
                    continue  # a Railway reference to the meilisearch service, checked below
                if re.search(r"(SECRET|PASSWORD|TOKEN|_KEY|_IV)$", key):
                    fail(f"{name}.{key}: secret-like variable must be preserve()")
                if re.fullmatch(r"[0-9a-f]{32,}", value):
                    fail(f"{name}.{key}: literal looks like a generated secret")

    mongo = services.get("mongodb", {})
    if (mongo.get("deploy") or {}).get("healthcheckPath"):
        fail("mongodb: no HTTP healthcheck (it is not an HTTP service)")
    if ((services.get("meilisearch") or {}).get("variables") or {}).keys() != SECRETS["meilisearch"]:
        fail("meilisearch: its only variable is MEILI_MASTER_KEY (preserve()); the rest is baked into the image")
    app = services.get("librechat", {})
    deploy, variables = app.get("deploy") or {}, app.get("variables") or {}
    if deploy.get("healthcheckPath") != "/health":
        fail("librechat: healthcheck must be /health")
    literals = {k: v.get("value") for k, v in variables.items() if v.get("type") == "literal"}
    for key, value in policy.items():
        if literals.get(key) != value:
            fail(f"librechat.{key}: {literals.get(key)!r} differs from infrastructure/common/librechat.env ({value!r})")
    extra = set(literals) - set(policy) - {"HOST", "PORT", "DOMAIN_CLIENT", "DOMAIN_SERVER", "MONGO_URI", "ADMIN_PANEL_URL",
                                           *MEILI}
    if extra:
        fail(f"librechat: application settings {sorted(extra)} belong in infrastructure/common/librechat.env")
    if literals.get("MONGO_URI") != MONGO_URI:
        fail("librechat.MONGO_URI must be built only from mongodb references over the private domain")
    for key, value in MEILI.items():
        if literals.get(key) != value:
            fail(f"librechat.{key} must be exactly {value} (private domain / reference to the meilisearch service)")
    for key in ("DOMAIN_CLIENT", "DOMAIN_SERVER"):
        if literals.get(key) != PUBLIC_URL:
            fail(f"librechat.{key} must be {PUBLIC_URL}")
    if literals.get("PORT") != "3080":
        fail("librechat.PORT must be 3080 (the public domain targets it)")
    if literals.get("ADMIN_PANEL_URL") != ADMIN_PANEL_URL:
        fail(f"librechat.ADMIN_PANEL_URL must be exactly {ADMIN_PANEL_URL} (the panel's generated domain)")

    panel = services.get("admin-panel", {})
    panel_vars = panel.get("variables") or {}
    if (panel.get("deploy") or {}).get("healthcheckPath") != "/health":
        fail("admin-panel: healthcheck must be /health")
    if set(panel_vars) != set(ADMIN_PANEL_ENV) | SECRETS["admin-panel"]:
        fail(f"admin-panel: variables must be exactly {sorted(set(ADMIN_PANEL_ENV) | SECRETS['admin-panel'])}, "
             f"got {sorted(panel_vars)}")
    for key, value in ADMIN_PANEL_ENV.items():
        if (panel_vars.get(key) or {}).get("value") != value:
            fail(f"admin-panel.{key} must be exactly {value}")


def check_typescript() -> None:
    tsc = IAC_DIR / "node_modules/.bin/tsc"
    proc = subprocess.run([str(tsc), "-p", str(IAC_DIR / "tsconfig.json")], cwd=IAC_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        fail(f"tsc --noEmit failed: {(proc.stdout + proc.stderr).strip()[:500]}")


def main(argv: list[str]) -> int:
    check_no_config_as_code()
    check_sdk_pin()
    check_dockerfiles()
    reason = node_ready()
    if reason:
        skipped.append(f"railway.ts evaluation and type-check: {reason}")
    else:
        project = evaluate()
        if project is not None:
            check_graph(project)
        check_typescript()
    for s in skipped:
        print(f"SKIP  {s}", file=sys.stderr)
    if failures:
        print("FAIL  railway_checks", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    if skipped and "--allow-skip" not in argv:
        print("FAIL  railway_checks (checks skipped; pass --allow-skip to accept)", file=sys.stderr)
        return 1
    print("PASS  railway_checks" + (" (with skips)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
