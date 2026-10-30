/**
 * EF MCP servers for admins only (ADR-0021, #218): sets the MCP_SERVERS permissions of the USER and ADMIN roles on
 * every start. LibreChat's `interface.mcpServers` writes one value to both roles, so librechat.yaml leaves the key out
 * and the server keeps the values this script writes (a role-editor change is reset on the next start).
 *
 * Runs inside the LibreChat container from /app/config, before the server (Railway: librechat-start.sh; Compose: the
 * librechat `command`), because the server caches the roles in memory once it has read them:
 *   node config/efaiw-roles-policy.js
 * It writes the two blocks with the raw driver, keyed by role name as upstream's initializeRoles reads them. On a new
 * database it creates both role documents and the server fills in the other permission types with its defaults.
 * Fails closed: if the database stays unreachable it exits non-zero and the server does not start, since a new
 * database would otherwise get upstream's defaults (MCP for every employee, sharing for admins).
 */
const mongoose = require('mongoose');
const { Permissions, PermissionTypes, SystemRoles } = require('librechat-data-provider');

const { USE, CREATE, SHARE, SHARE_PUBLIC, CONFIGURE_OBO } = Permissions;
/** Admins add and use remote MCP servers; nobody shares one, so employees never see a server. */
const noSharing = { [SHARE]: false, [SHARE_PUBLIC]: false, [CONFIGURE_OBO]: false };
const MCP_POLICY = {
  [SystemRoles.USER]: { [USE]: false, [CREATE]: false, ...noSharing },
  [SystemRoles.ADMIN]: { [USE]: true, [CREATE]: true, ...noSharing },
};

const RETRY_MS = 5 * 1000;
const MAX_WAIT_MS = 2 * 60 * 1000;
const log = (message) => console.log(`efaiw-roles-policy: ${message}`);

/** Connects to MONGO_URI, retrying while the database starts; throws after MAX_WAIT_MS. */
async function connect() {
  if (!process.env.MONGO_URI) {
    throw new Error('MONGO_URI is not set');
  }
  for (let waited = 0; ; waited += RETRY_MS) {
    try {
      return await mongoose.connect(process.env.MONGO_URI, { serverSelectionTimeoutMS: RETRY_MS });
    } catch (error) {
      if (waited >= MAX_WAIT_MS) {
        throw error;
      }
      log(`database not reachable yet (${error.message}); retrying`);
      await new Promise((resolve) => setTimeout(resolve, RETRY_MS));
    }
  }
}

async function apply() {
  await connect();
  const roles = mongoose.connection.db.collection('roles');
  for (const [name, block] of Object.entries(MCP_POLICY)) {
    await roles.updateOne(
      { name },
      { $set: { [`permissions.${PermissionTypes.MCP_SERVERS}`]: block } },
      { upsert: true },
    );
  }
  log(`MCP_SERVERS applied: ADMIN use+create, USER none, sharing off (${Object.keys(MCP_POLICY).join(', ')})`);
}

apply()
  .catch((error) => {
    log(`failed, the server will not start: ${error.message}`);
    process.exitCode = 1;
  })
  .finally(() => mongoose.disconnect().finally(() => process.exit()));
