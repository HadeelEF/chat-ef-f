/**
 * EF official ready commands (ADR-0018, #189): creates each template of ai/prompts/ef-templates.json once, as a prompt
 * group with a `/command`, owned by the first ADMIN account and viewable by everyone signed in (PUBLIC viewer, the
 * same grant LibreChat's own config/migrate-prompt-permissions.js gives a global prompt).
 *
 * Runs inside the LibreChat container from /app/config (it reuses config/connect.js and the API's models), in the
 * background of the server start (Railway: librechat-start.sh; Compose: the librechat `command`):
 *   node config/efaiw-prompts-seed.js <templates.json>
 * It waits until the server has seeded its access roles and an ADMIN account exists (the first account of a new
 * database), then exits. Each template is created once, ever: a marker in the `efaiw_seeds` collection records it, so
 * an admin's edit is never overwritten and a template an admin deleted is not created again.
 */
// The prompts need no conversation search, and the search plugin must stay the server's alone: loading the models with
// it creates the Meilisearch indexes and marks `user` filterable, so a server starting next to this script on an empty
// index (a lost Meilisearch volume) would see its settings in place and skip the full rebuild (mock_chat.py M55).
delete process.env.MEILI_HOST;
delete process.env.MEILI_MASTER_KEY;

const fs = require('fs');
const path = require('path');
const mongoose = require('mongoose');
const { AccessRoleIds, PrincipalType, ResourceType, SystemRoles } = require('librechat-data-provider');

require('module-alias')({ base: path.resolve(__dirname, '..', 'api') });
const connect = require('./connect');

const { grantPermission } = require('~/server/services/PermissionService');
const { createPromptGroup, findRoleByIdentifier } = require('~/models');
const { PromptGroup, User } = require('~/db/models');

const WAIT_MS = 20 * 1000;
const MAX_WAIT_MS = 60 * 60 * 1000;
const log = (message) => console.log(`efaiw-prompts-seed: ${message}`);

/** Resolves when the access roles exist and an ADMIN account can own the templates; null after MAX_WAIT_MS. */
async function waitForAdmin() {
  for (let waited = 0; waited <= MAX_WAIT_MS; waited += WAIT_MS) {
    const [owner, viewer] = await Promise.all([
      findRoleByIdentifier(AccessRoleIds.PROMPTGROUP_OWNER),
      findRoleByIdentifier(AccessRoleIds.PROMPTGROUP_VIEWER),
    ]);
    const admin =
      owner && viewer
        ? await User.findOne({ role: SystemRoles.ADMIN }).sort({ createdAt: 1 }).select('_id').lean()
        : null;
    if (admin) {
      return admin;
    }
    await new Promise((resolve) => setTimeout(resolve, WAIT_MS));
  }
  return null;
}

async function seed(file) {
  const { authorName, templates } = JSON.parse(fs.readFileSync(file, 'utf8'));
  await connect();
  const admin = await waitForAdmin();
  if (!admin) {
    log('no ADMIN account yet; nothing created (runs again on the next start)');
    return;
  }
  const markers = mongoose.connection.db.collection('efaiw_seeds');
  let created = 0;
  // Lists show the newest group first: create the file's first template last so it leads the «/» list.
  for (const { command, name, category, oneliner, prompt } of [...templates].reverse()) {
    const markerId = `prompt:${command}`;
    if (await markers.findOne({ _id: markerId })) {
      continue;
    }
    if (!(await PromptGroup.exists({ command }))) {
      const author = admin._id.toString();
      const { group } = await createPromptGroup({
        prompt: { prompt, type: 'text' },
        group: { name, category, oneliner, command },
        author,
        authorName,
      });
      for (const [principalType, principalId, accessRoleId] of [
        [PrincipalType.USER, author, AccessRoleIds.PROMPTGROUP_OWNER],
        [PrincipalType.PUBLIC, null, AccessRoleIds.PROMPTGROUP_VIEWER],
      ]) {
        await grantPermission({
          principalType,
          principalId,
          resourceType: ResourceType.PROMPTGROUP,
          resourceId: group._id,
          accessRoleId,
          grantedBy: author,
        });
      }
      created++;
    }
    await markers.insertOne({ _id: markerId, at: new Date() });
  }
  log(`${created} created, ${templates.length - created} already present`);
}

seed(process.argv[2])
  .catch((error) => {
    log(`failed: ${error.message}`);
    process.exitCode = 1;
  })
  .finally(() => mongoose.disconnect().finally(() => process.exit()));
