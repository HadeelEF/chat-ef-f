// Merges the EF Arabic translation overlay (ar.json) into LibreChat's Arabic locale before the web client is built
// (ADR-0013). Node standard library only. Usage: node merge-locale.mjs <client/src/locales> <ar.json>
//
// Fails the build (exit 1) when the overlay no longer matches the pinned English source, so an upgrade cannot ship
// stale or broken strings silently:
//   - every overlay key exists in English (or is an Arabic plural form of an English plural key);
//   - every merged value, upstream or overlay, keeps the English {{placeholders}}, <tags> and line breaks (upstream
//     Arabic strings left behind by an English change are caught here and must be replaced in ar.json);
//   - the merged Arabic locale covers 100% of the English keys (no English fallback anywhere in the interface).
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const [localesDir, overlayPath] = process.argv.slice(2);
if (!localesDir || !overlayPath) {
  console.error('usage: node merge-locale.mjs <client/src/locales> <ar.json>');
  process.exit(2);
}
const read = (path) => JSON.parse(readFileSync(path, 'utf8'));
const en = read(join(localesDir, 'en', 'translation.json'));
const upstreamAr = read(join(localesDir, 'ar', 'translation.json'));
const overlay = read(overlayPath);

const PLURAL = /^(.*)_(zero|one|two|few|many|other)$/;
const tokens = (text, rx) => (text.match(rx) ?? []).sort().join('\u0000');
const PLACEHOLDER = /\{\{[^}]+\}\}/g;
const TAG = /<\/?[A-Za-z0-9]+\s*\/?>/g;

/** English source of a key: the key itself, or for an Arabic-only plural form, its English `_other` or `_one` sibling. */
function englishFor(key) {
  if (key in en) {
    return en[key];
  }
  const m = key.match(PLURAL);
  return m ? (en[`${m[1]}_other`] ?? en[`${m[1]}_one`]) : undefined;
}

const errors = [];
for (const [key, value] of Object.entries(overlay)) {
  if (englishFor(key) === undefined) {
    errors.push(`${key}: not in the pinned English locale (stale after an upgrade? remove or re-key it)`);
  } else if (typeof value !== 'string' || value.trim() === '') {
    errors.push(`${key}: empty or not a string`);
  }
}

const merged = {};
for (const key of Object.keys(en)) {
  const value = overlay[key] ?? upstreamAr[key];
  if (value !== undefined) {
    merged[key] = value;
  }
}
for (const [key, value] of Object.entries(overlay)) {
  merged[key] ??= value;
}
for (const [key, value] of Object.entries(merged)) {
  const source = englishFor(key);
  if (source === undefined || typeof value !== 'string') {
    continue;
  }
  const origin = key in overlay ? 'ar.json' : 'upstream Arabic (replace it in ar.json)';
  if (tokens(source, PLACEHOLDER) !== tokens(value, PLACEHOLDER)) {
    errors.push(`${key}: placeholders differ from English [${origin}]`);
  }
  if (tokens(source, TAG) !== tokens(value, TAG)) {
    errors.push(`${key}: tags differ from English [${origin}]`);
  }
  if (source.split('\n').length !== value.split('\n').length) {
    errors.push(`${key}: line breaks differ from English [${origin}]`);
  }
}
const missing = Object.keys(en).filter((key) => !(key in merged));
if (missing.length > 0) {
  errors.push(`${missing.length} English key(s) without Arabic, e.g. ${missing.slice(0, 5).join(', ')}`);
}

if (errors.length > 0) {
  console.error(`efaiw: Arabic locale overlay rejected (${errors.length} problem(s)):`);
  errors.slice(0, 50).forEach((e) => console.error(`  - ${e}`));
  process.exit(1);
}
writeFileSync(join(localesDir, 'ar', 'translation.json'), `${JSON.stringify(merged, null, 2)}\n`);
const overridden = Object.keys(overlay).filter((key) => key in upstreamAr).length;
console.log(
  `efaiw: Arabic locale ${Object.keys(en).length}/${Object.keys(en).length} English keys covered ` +
    `(upstream ${Object.keys(upstreamAr).filter((k) => k in en).length}, overlay ${Object.keys(overlay).length}, ` +
    `of which ${overridden} replace upstream wording)`,
);
