/**
 * EF AI Workspace — Railway Infrastructure as Code (Environment A: cloud development / demo). Decision: ADR-0008.
 *
 * Evaluated by the Railway CLI (`railway config plan` / `railway config apply`, CLI >= 5.42.1) with the SDK pinned in
 * .railway/package.json. Variables and IaC changes reach Railway only through plan/apply, run by the delegated agent in
 * the `dev` environment (ADR-0009) or by the owner (docs/operations/railway.md). Offline checks: scripts/validate/railway_checks.py.
 *
 * Topology: four services built from this repository's Dockerfiles; each data service has exactly one volume (Railway
 * allows one per service):
 *   mongodb      infrastructure/railway/mongodb.Dockerfile     -> volume mongodb-data at /data/db; private
 *   meilisearch  infrastructure/railway/meilisearch.Dockerfile -> volume meilisearch-data at /meili_data; private
 *   librechat    infrastructure/railway/librechat.Dockerfile   -> volume librechat-storage at /app/storage; public
 *   admin-panel  infrastructure/railway/admin-panel.Dockerfile -> no volume (no data); public (ADR-0016, #141)
 * Every image derives from the exact digest pinned in infrastructure/compose/compose.yaml.
 *
 * Secrets are NEVER written here. They are declared with preserve() and set once per environment with
 * scripts/setup/railway-secrets.sh (values generated locally, piped via stdin). Until they exist every service refuses
 * to start, so MongoDB can never initialise its volume without authentication nor Meilisearch serve without a key.
 * NO REAL ENVIRONMENT FUND DATA on Railway: synthetic data only (NFR-PRIV-01). There is no Railway region in Saudi Arabia.
 */
import { defineRailway, github, preserve, project, service, volume } from "railway/iac";

// AUTODEPLOY FROM main (ADR-0010, owner decision 2026-10-19; supersedes the manual-only part of #16 D2 revised). All
// services track this repository's `main` branch: a push to main that changes a file baked into a service's image
// (its watch paths below) rebuilds and redeploys that service. Everything else (docs, Compose, checks) deploys nothing.
// Wait for CI stays off (checkSuites: false) because GitHub Actions is not used. Variables in this file (librechat.env
// policy, secrets) are NOT applied by a push: they still need `railway config plan/apply`. railway_checks.py accepts
// only this repository, branch main, checkSuites false, and watch paths equal to each Dockerfile's inputs.
// Manual fallback / rollback: scripts/setup/railway-deploy.sh (railway.md §4). Railway `dev` only, synthetic data only.
const REPO = "faenazi/ef-ai-workspace";
const fromMain = () => github(REPO, { branch: "main", checkSuites: false });

// Railway has no Middle East region; EU West (Amsterdam) is the closest offered region. Owner-approved target (#16 D3,
// 2026-10-18); changing it later migrates the volumes. Synthetic data only.
const REGION = "europe-west4-drams3a";

// Application policy: MUST equal infrastructure/common/librechat.env (railway_checks.py fails on any drift).
const LIBRECHAT_POLICY = {
  NODE_ENV: "production",
  CONFIG_PATH: "/app/librechat.yaml",
  TRUST_PROXY: "1",
  NO_INDEX: "true",
  ALLOW_REGISTRATION: "false",
  ALLOW_EMAIL_LOGIN: "true",
  ALLOW_SOCIAL_LOGIN: "false",
  ALLOW_SOCIAL_REGISTRATION: "false",
  ALLOW_PASSWORD_RESET: "false",
  ALLOW_UNVERIFIED_EMAIL_LOGIN: "false",
  ALLOW_SHARED_LINKS: "true",
  ALLOW_SHARED_LINKS_PUBLIC: "false",
  SEARCH: "true",
  MEILI_SYNC_THRESHOLD: "0",
  SCHEDULES_DISABLED: "true",
  SCHEDULES_SINGLE_PROCESS: "true",
  DEBUG_LOGGING: "false",
  APP_TITLE: "بصير | صندوق البيئة",
  CUSTOM_FOOTER: "بصير قد يخطئ، فتحقّق من المعلومات المهمة. لا تُدخل معلومات سرية أو بيانات شخصية.",
  HELP_AND_FAQ_URL: "/assets/ef-help.html",
  ENABLE_STATIC_ASSET_BROTLI: "true",
};

// Volume sizes (MB): Railway Pro would default to 50 GB per volume, and ~2-3% of a volume's size is billed as filesystem
// metadata even when empty. Approved initial size 5 GB per service volume (#16 D3; Meilisearch under the same envelope,
// owner approval of batch 1 on #125); measured initial MongoDB data ~0.2 GB.
// Volumes grow live without downtime (increase sizeMB + apply, after review) but can never shrink.
const VOLUME_SIZE_MB = 5_000;

const MONGO_APP_DATABASE = "LibreChat";
const MONGO_APP_USERNAME = "librechat";

/** Railway reference variable `${{service.KEY}}` (resolved by Railway at deploy time; never a secret in Git). */
const ref = (serviceName: string, key: string): string => "${{" + serviceName + "." + key + "}}";

export default defineRailway(() => {
  const mongodbData = volume("mongodb-data", { region: REGION, sizeMB: VOLUME_SIZE_MB });
  const librechatStorage = volume("librechat-storage", { region: REGION, sizeMB: VOLUME_SIZE_MB });
  const meilisearchData = volume("meilisearch-data", { region: REGION, sizeMB: VOLUME_SIZE_MB });

  const mongodb = service("mongodb", {
    source: fromMain(),
    build: {
      builder: "DOCKERFILE",
      dockerfilePath: "infrastructure/railway/mongodb.Dockerfile",
      // Exactly the Dockerfile and its COPY sources (railway_checks.py): a redeploy restarts MongoDB (brief downtime).
      watchPatterns: [
        "/infrastructure/railway/mongodb.Dockerfile",
        "/infrastructure/common/mongo-init/**",
        "/infrastructure/railway/mongodb-start.sh",
      ],
    },
    replicas: { [REGION]: 1 },
    deploy: {
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
      // Approved cap (#16 D3): 1 vCPU / 1 GB (vCPU, bytes). Trial estimate (idle ~0.25 GB measured), not load-tested.
      limitOverride: { containers: { cpu: 1, memoryBytes: 1_000_000_000 } },
    },
    volumeMounts: { "/data/db": mongodbData },
    // Private by design: no domains, no TCP proxy. Reachable only as mongodb.railway.internal:27017.
    env: {
      MONGO_INITDB_ROOT_USERNAME: preserve(),
      MONGO_INITDB_ROOT_PASSWORD: preserve(),
      MONGO_APP_DATABASE,
      MONGO_APP_USERNAME,
      MONGO_APP_PASSWORD: preserve(),
    },
  });

  // Conversation search (#125). The index holds chat text: private like MongoDB, behind its master key, and derived
  // from MongoDB (no backup needed; rebuild: docs/operations/railway.md). A redeploy briefly hides the search box only.
  const meilisearch = service("meilisearch", {
    source: fromMain(),
    build: {
      builder: "DOCKERFILE",
      dockerfilePath: "infrastructure/railway/meilisearch.Dockerfile",
      watchPatterns: ["/infrastructure/railway/meilisearch.Dockerfile", "/infrastructure/railway/meilisearch-start.sh"],
    },
    replicas: { [REGION]: 1 },
    deploy: {
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
      // Same cap as MongoDB (#16 D3 envelope, #125): 1 vCPU / 1 GB. Synthetic data; not load-tested.
      limitOverride: { containers: { cpu: 1, memoryBytes: 1_000_000_000 } },
    },
    volumeMounts: { "/meili_data": meilisearchData },
    // Private by design: no domains, no TCP proxy. Reachable only as meilisearch.railway.internal:7700.
    env: {
      MEILI_MASTER_KEY: preserve(),
    },
  });

  const librechat = service("librechat", {
    source: fromMain(),
    build: {
      builder: "DOCKERFILE",
      dockerfilePath: "infrastructure/railway/librechat.Dockerfile",
      // Image changes deploy on push to main (these watch paths = the Dockerfile and its COPY sources). Policy
      // (librechat.env -> variables below) and IaC changes still reach Railway only via `railway config plan/apply`.
      watchPatterns: [
        "/infrastructure/railway/librechat.Dockerfile",
        "/infrastructure/common/client/**",
        "/infrastructure/common/librechat.yaml",
        "/infrastructure/railway/librechat-start.sh",
        "/ai/skills/**",
        "/ai/prompts/**",
        "/infrastructure/common/prompts-seed.js",
        "/infrastructure/common/roles-policy.js",
      ],
    },
    healthcheck: "/health",
    // LibreChat needs up to ~90 s on first start (index creation); Railway's default is also 300 s.
    healthcheckTimeout: 300,
    replicas: { [REGION]: 1 },
    deploy: {
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
      // Approved cap (#16 D3): 2 vCPU / 2 GB (vCPU, bytes). Trial estimate (idle ~0.5 GB measured), not load-tested.
      limitOverride: { containers: { cpu: 2, memoryBytes: 2_000_000_000 } },
    },
    volumeMounts: { "/app/storage": librechatStorage },
    env: {
      ...LIBRECHAT_POLICY,
      HOST: "0.0.0.0",
      PORT: "3080",
      // The public *.up.railway.app domain is generated once in the dashboard (target port 3080); it is not IaC.
      DOMAIN_CLIENT: "https://${{RAILWAY_PUBLIC_DOMAIN}}",
      DOMAIN_SERVER: "https://${{RAILWAY_PUBLIC_DOMAIN}}",
      MONGO_URI:
        "mongodb://" +
        ref("mongodb", "MONGO_APP_USERNAME") +
        ":" +
        ref("mongodb", "MONGO_APP_PASSWORD") +
        "@" +
        ref("mongodb", "RAILWAY_PRIVATE_DOMAIN") +
        ":27017/" +
        ref("mongodb", "MONGO_APP_DATABASE") +
        "?authSource=" +
        ref("mongodb", "MONGO_APP_DATABASE"),
      // Conversation search (#125): the private Meilisearch service; its key is referenced, never copied.
      MEILI_HOST: "http://" + ref("meilisearch", "RAILWAY_PRIVATE_DOMAIN") + ":7700",
      MEILI_MASTER_KEY: ref("meilisearch", "MEILI_MASTER_KEY"),
      CREDS_KEY: preserve(),
      CREDS_IV: preserve(),
      JWT_SECRET: preserve(),
      JWT_REFRESH_SECRET: preserve(),
      // Approved LLM provider key (#37, OD-01): set once by the owner in the Railway dashboard, never in Git.
      QWEN_API_KEY: preserve(),
      // Admin Panel (ADR-0016): its generated public domain (the Settings link for admins, a trusted admin-login
      // origin). librechat-start.sh drops it while the panel has no domain yet.
      ADMIN_PANEL_URL: "https://" + ref("admin-panel", "RAILWAY_PUBLIC_DOMAIN"),
    },
  });

  // LibreChat Admin Panel (ADR-0016, #141; owner authorisation 2026-10-23): users, groups, custom roles and grants.
  // No data and no volume (the session is an encrypted cookie); every action goes through LibreChat's /api/admin/*,
  // which checks admin rights itself. The public *.up.railway.app domain (target port 3000) is generated by hand after
  // the SC-18 scan of this image; it is not IaC.
  const adminPanel = service("admin-panel", {
    source: fromMain(),
    build: {
      builder: "DOCKERFILE",
      dockerfilePath: "infrastructure/railway/admin-panel.Dockerfile",
      watchPatterns: [
        "/infrastructure/railway/admin-panel.Dockerfile",
        "/infrastructure/railway/admin-panel/patches/**",
        "/infrastructure/railway/admin-panel-start.sh",
        // The EF brand files patch 0002 uses (#160).
        "/infrastructure/common/client/brand/fonts/aktiv-grotesk-regular.otf",
        "/infrastructure/common/client/brand/fonts/aktiv-grotesk-semibold.otf",
        "/infrastructure/common/client/brand/fonts/aktiv-grotesk-bold.otf",
        "/infrastructure/common/client/brand/assets/logo.svg",
        "/infrastructure/common/client/brand/assets/logo-dark.svg",
        "/infrastructure/common/client/brand/assets/ef-app-icon.svg",
        "/infrastructure/common/client/brand/assets/favicon-32x32.png",
      ],
    },
    healthcheck: "/health",
    replicas: { [REGION]: 1 },
    deploy: {
      restartPolicyType: "ON_FAILURE",
      restartPolicyMaxRetries: 10,
      // Owner-approved cap (#141, 2026-10-23): 1 vCPU / 512 MB. Measured idle ~0.1 GB (cloud session), not load-tested.
      limitOverride: { containers: { cpu: 1, memoryBytes: 512_000_000 } },
    },
    env: {
      PORT: "3000",
      // Server-side calls to LibreChat stay on the private network; the browser-facing URL serves OAuth redirects.
      API_SERVER_URL: "http://" + ref("librechat", "RAILWAY_PRIVATE_DOMAIN") + ":3080",
      VITE_API_BASE_URL: "https://" + ref("librechat", "RAILWAY_PUBLIC_DOMAIN"),
      SESSION_SECRET: preserve(),
    },
  });

  return project("ef-ai-workspace", {
    resources: [mongodb, mongodbData, meilisearch, meilisearchData, librechat, librechatStorage, adminPanel],
  });
});
