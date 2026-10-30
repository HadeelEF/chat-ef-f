// Runs once, by the official mongo image entrypoint, only when the data volume is empty.
// Creates the least-privilege user LibreChat connects with (readWrite on its own database only).
// Credentials come from the container environment; nothing secret is stored in this file.
const dbName = process.env.MONGO_APP_DATABASE || 'LibreChat';
const user = process.env.MONGO_APP_USERNAME;
const pwd = process.env.MONGO_APP_PASSWORD;

if (!user || !pwd) {
  throw new Error('MONGO_APP_USERNAME and MONGO_APP_PASSWORD must be set');
}

db.getSiblingDB(dbName).createUser({
  user,
  pwd,
  roles: [{ role: 'readWrite', db: dbName }],
});

print(`Created application user for database ${dbName} with role readWrite`);
