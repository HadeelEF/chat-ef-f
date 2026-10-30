// Offline evaluation of .railway/railway.ts, mirroring how the Railway CLI evaluates it (CLI src/iac/eval.rs:
// `node --experimental-strip-types`, default export called with a context and a project factory). Prints the project
// definition as JSON on stdout. Needs no Railway token and makes no network calls.
//
// Usage: node --experimental-strip-types --disable-warning=ExperimentalWarning scripts/validate/railway_eval.mjs [env]
// Prerequisite: npm ci --prefix .railway   (installs the pinned SDK)
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const sdk = path.join(root, ".railway", "node_modules", "railway", "dist", "iac", "index.js");
const file = path.join(root, ".railway", "railway.ts");
const environment = process.argv[2] ?? "dev";

const iac = await import(pathToFileURL(sdk).href);
const ctx = iac.createRailwayContext({ command: "plan", environment, environmentName: environment });
const mod = await import(pathToFileURL(file).href);
const factory = (name, definition = {}) => ({ name, ...definition, resources: (definition.resources ?? []).flat() });
const project = typeof mod.default === "function" ? await mod.default(ctx, factory) : mod.default;

process.stdout.write(JSON.stringify(project, null, 2) + "\n");
