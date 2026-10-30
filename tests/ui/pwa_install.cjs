#!/usr/bin/env node
/*
 * Browser checks of the installable app (PWA): what Android Chrome and iPhone Safari read before «تثبيت التطبيق» /
 * «إضافة إلى الشاشة الرئيسية» — the manifest, its icons, the service worker, Chromium's own installability verdict
 * (DevTools Protocol `Page.getInstallabilityErrors`), the start address and the «محادثة جديدة» shortcut opened as
 * the installed app opens them, the offline page, and the iPhone tags in index.html. Arabic, Android phone (Pixel 7,
 * touch).
 *
 *   node tests/ui/pwa_install.cjs <state.json from tests/ui/ui_stack.py> [screenshot-dir]
 *
 * Needs Node.js and Playwright with Chromium (require('playwright')). axe-core is fetched from the npm registry at a
 * pinned version and sha256. Prints PASS/FAIL per check (IDs in docs/quality/concept1-interface-test-cases.md §14)
 * and exits 1 on any failure. Safari itself and real devices are not covered: iPhone has no installability API.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { chromium, devices } = require('playwright');

const [stateFile, shotArg] = process.argv.slice(2);
if (!stateFile) {
  console.error('usage: node tests/ui/pwa_install.cjs <state.json> [screenshot-dir]');
  process.exit(2);
}
const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
const BASE = state.base;
const SHOTS = shotArg || fs.mkdtempSync(path.join(os.tmpdir(), 'efaiw-ui-'));
fs.mkdirSync(SHOTS, { recursive: true });

const AXE = {
  url: 'https://registry.npmjs.org/axe-core/-/axe-core-4.10.3.tgz',
  sha256: '0f2b4d7dcdf7d1219df8d1959ad68e565f51d14c3f0d88bb71cd59abeb956292',
};
const AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

/** What the installed app shows on the phone: its name, language and colours (patches 0006, 0011, 0013). */
const APP = {
  name: 'بصير | صندوق البيئة',
  shortName: 'بصير',
  lang: 'ar',
  dir: 'rtl',
  display: 'standalone',
  background: '#FFFFFF',
  shortcut: 'محادثة جديدة',
  offlineTitle: 'لا يوجد اتصال بالشبكة',
};

let passed = 0;
let failed = 0;
function report(id, label, ok, detail) {
  if (ok) {
    passed += 1;
    console.log(`PASS  ${id}  ${label}`);
  } else {
    failed += 1;
    console.log(`FAIL  ${id}  ${label} :: ${String(detail || '').slice(0, 400)}`);
  }
}
async function check(id, label, fn) {
  try {
    const result = await fn();
    const [ok, detail] = Array.isArray(result) ? result : [result !== false, ''];
    report(id, label, ok, detail);
  } catch (err) {
    report(id, label, false, `${err.name}: ${err.message.split('\n')[0]}`);
  }
}

function axeSource() {
  const cache = path.join(os.tmpdir(), 'efaiw-axe-core-4.10.3');
  const js = path.join(cache, 'package', 'axe.min.js');
  if (!fs.existsSync(js)) {
    fs.mkdirSync(cache, { recursive: true });
    const tgz = path.join(cache, 'axe-core.tgz');
    execFileSync('curl', ['-sSfL', '-o', tgz, AXE.url]);
    const sum = crypto.createHash('sha256').update(fs.readFileSync(tgz)).digest('hex');
    if (sum !== AXE.sha256) {
      throw new Error(`axe-core tarball sha256 ${sum}, expected ${AXE.sha256}`);
    }
    execFileSync('tar', ['-xzf', tgz, '-C', cache, 'package/axe.min.js']);
  }
  return fs.readFileSync(js, 'utf8');
}
const AXE_JS = axeSource();

async function axe(page) {
  await page.addScriptTag({ content: AXE_JS });
  const res = await page.evaluate(
    (tags) => window.axe.run(document, { runOnly: { type: 'tag', values: tags } }),
    AXE_TAGS,
  );
  const bad = res.violations.map((v) => `${v.id}(${v.nodes.length}): ${v.nodes[0]?.target}`);
  return [bad.length === 0, bad.join(' | ')];
}

async function noHScroll(page) {
  const [sw, w] = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  return [sw <= w, `scrollWidth ${sw} > ${w}`];
}

const shot = (page, name) =>
  page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: false }).catch(() => {});

/** Width and height from a PNG's IHDR chunk, or null when the bytes are not a PNG. */
function pngSize(buf) {
  const signature = '89504e470d0a1a0a';
  if (buf.length < 24 || buf.subarray(0, 8).toString('hex') !== signature) {
    return null;
  }
  return `${buf.readUInt32BE(16)}x${buf.readUInt32BE(20)}`;
}

/** Fetches through the page's context (its service worker and cookies), as the browser fetches app assets. */
async function fetchBytes(context, url) {
  const res = await context.request.get(url);
  return { status: res.status(), type: res.headers()['content-type'] || '', body: await res.body() };
}

/** LibreChat keeps a connection open, so «network idle» never comes: wait for the app's frame instead. */
async function settle(page) {
  await page.waitForLoadState('load');
  await page
    .locator('nav.efaiw-rail:visible, [data-testid$="open-sidebar-button"]:visible, main.efaiw-page:visible, #email')
    .first()
    .waitFor({ timeout: 30000 });
  await page.waitForTimeout(400);
}

async function main() {
  // The full Chromium with a profile on disk: the headless shell answers every installability query with no errors,
  // and a browser context without a profile is incognito («in-incognito»), where Chrome never offers to install.
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'efaiw-pwa-profile-'));
  const pixel = { ...devices['Pixel 7'] };
  delete pixel.defaultBrowserType; // a browser choice, not a context option
  const context = await chromium.launchPersistentContext(profile, {
    ...pixel,
    channel: 'chromium',
    locale: 'ar-SA',
    serviceWorkers: 'allow',
  });
  await context.addCookies([{ name: 'lang', value: 'ar', url: BASE }]);
  await context.addInitScript(() => {
    try {
      window.localStorage.setItem('lang', JSON.stringify('ar'));
    } catch {
      /* storage off */
    }
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  const cdp = await context.newCDPSession(page);

  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await settle(page);

  // The manifest as Chromium parsed it from the page's <link rel="manifest">.
  const { url: manifestUrl, errors: parseErrors, data } = await cdp.send('Page.getAppManifest');
  const manifest = data ? JSON.parse(data) : {};
  const resolve = (href) => new URL(href, manifestUrl).href;
  const scope = resolve(manifest.scope || '.');
  const startUrl = resolve(manifest.start_url || '.');

  await check('PW-01', 'manifest: linked, parsed without errors, name and language', async () => {
    const want = {
      name: APP.name,
      short_name: APP.shortName,
      lang: APP.lang,
      dir: APP.dir,
      display: APP.display,
      background_color: APP.background,
    };
    const wrong = Object.entries(want)
      .filter(([key, value]) => manifest[key] !== value)
      .map(([key, value]) => `${key}=${JSON.stringify(manifest[key])} (want ${JSON.stringify(value)})`);
    const res = await fetchBytes(context, manifestUrl);
    const bad = [
      ...(parseErrors || []).map((e) => `parse: ${e.message}`),
      ...wrong,
      ...(res.status === 200 ? [] : [`HTTP ${res.status}`]),
      ...(manifest.id ? [] : ['no id']),
      ...(manifest.description ? [] : ['no description']),
      ...(/^#[0-9a-f]{6}$/i.test(manifest.theme_color || '') ? [] : [`theme_color ${manifest.theme_color}`]),
      ...(startUrl.startsWith(scope) ? [] : [`start_url ${startUrl} outside scope ${scope}`]),
    ];
    return [manifestUrl.startsWith(BASE) && bad.length === 0, `${manifestUrl} ${bad.join('; ')}`];
  });

  await check('PW-02', 'icons: every manifest icon is a PNG of its declared size; 192, 512 and maskable 512', async () => {
    const icons = manifest.icons || [];
    const bad = [];
    for (const icon of icons) {
      const res = await fetchBytes(context, resolve(icon.src));
      const size = pngSize(res.body);
      if (res.status !== 200 || size !== icon.sizes) {
        bad.push(`${icon.src}: HTTP ${res.status}, ${size || res.type}, declared ${icon.sizes}`);
      }
    }
    const any = (sizes) => icons.some((i) => i.sizes === sizes && (i.purpose || 'any').split(' ').includes('any'));
    const maskable = icons.some((i) => i.sizes === '512x512' && (i.purpose || '').split(' ').includes('maskable'));
    if (!any('192x192')) bad.push('no any-purpose 192x192');
    if (!any('512x512')) bad.push('no any-purpose 512x512');
    if (!maskable) bad.push('no maskable 512x512');
    return [icons.length > 0 && bad.length === 0, bad.join(' | ')];
  });

  await check('PW-03', 'service worker: active for the whole site and controls the page after a reload', async () => {
    const reg = await page.evaluate(async () => {
      const r = await navigator.serviceWorker.ready; // resolves while the first worker may still be «activating»
      if (r.active.state === 'activating') {
        await new Promise((done) => r.active.addEventListener('statechange', done, { once: true }));
      }
      return { scope: r.scope, state: r.active.state, script: r.active.scriptURL };
    });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await settle(page);
    const controlled = await page.evaluate(() => Boolean(navigator.serviceWorker.controller));
    const ok = reg.scope === `${BASE}/` && reg.state === 'activated' && controlled;
    return [ok, `${JSON.stringify(reg)} controlled=${controlled}`];
  });

  await check('PW-04', 'Chromium installability: no errors (what Android Chrome needs for «تثبيت التطبيق»)', async () => {
    const verdict = async (session) => {
      const { installabilityErrors } = await session.send('Page.getInstallabilityErrors');
      return installabilityErrors.map((e) =>
        [e.errorId, ...(e.errorArguments || []).map((a) => `${a.name}=${a.value}`)].join(' '));
    };
    const bad = await verdict(cdp);
    // Control: the offline page has no manifest, so the same query must name «no-manifest».
    const other = await context.newPage();
    await other.goto(`${BASE}/assets/ef-offline.html`, { waitUntil: 'load' });
    const control = await verdict(await context.newCDPSession(other));
    await other.close();
    const live = control.includes('no-manifest');
    return [live && bad.length === 0, `${bad.join(' | ')} control=${JSON.stringify(control)}`];
  });

  await check('PW-05', 'iPhone: touch icon 180x180, home-screen title «بصير», standalone and status-bar tags', async () => {
    const tags = await page.evaluate(() => {
      const meta = (name) => document.querySelector(`meta[name="${name}"]`)?.getAttribute('content') ?? null;
      return {
        icon: document.querySelector('link[rel="apple-touch-icon"]')?.href ?? null,
        capable: meta('apple-mobile-web-app-capable'),
        title: meta('apple-mobile-web-app-title'),
        statusBar: meta('apple-mobile-web-app-status-bar-style'),
        themeColor: meta('theme-color'),
        viewport: meta('viewport'),
      };
    });
    const res = tags.icon ? await fetchBytes(context, tags.icon) : { status: 0, body: Buffer.alloc(0) };
    const bad = [
      ...(res.status === 200 && pngSize(res.body) === '180x180' ? [] : [`icon ${tags.icon}: HTTP ${res.status}`]),
      ...(tags.capable === 'yes' ? [] : [`capable ${tags.capable}`]),
      ...(tags.title === APP.shortName ? [] : [`title ${tags.title}`]),
      ...(tags.statusBar ? [] : ['no status-bar style']),
      ...(tags.themeColor ? [] : ['no theme-color']),
    ];
    console.log(`      iPhone tags: ${JSON.stringify(tags)}`);
    return [bad.length === 0, bad.join(' | ')];
  });

  // Signed in once: the installed app keeps its own session, as on the phone.
  const account = state.accounts.employee;
  await page.locator('#email').fill(account.email);
  await page.locator('#password').fill(account.password);
  await page.getByTestId('login-button').click();
  await page.waitForURL((url) => url.pathname.startsWith('/c/'), { timeout: 30000 });
  await settle(page);

  // The installed app opens these addresses in its own window. The client has no `display-mode` styles, so the page is
  // the one a tab shows (Chromium's DevTools Protocol does not emulate that media feature).
  await check('PW-06', 'start address as the installed app opens it: Arabic, right to left, composer, no sideways scroll', async () => {
    const app = await context.newPage();
    app.on('pageerror', (err) => errors.push(err.message));
    await app.goto(startUrl, { waitUntil: 'domcontentloaded' });
    await settle(app);
    const info = await app.evaluate(() => ({
      lang: document.documentElement.lang,
      dir: document.documentElement.dir,
      path: location.pathname,
    }));
    const composer = await app.locator('#prompt-textarea').isVisible();
    const [flat, scroll] = await noHScroll(app);
    await shot(app, 'pwa-start-ar-phone');
    await app.close();
    const ok = info.lang.startsWith('ar') && info.dir === 'rtl' && info.path.startsWith('/c/') && composer && flat;
    return [ok, `${JSON.stringify(info)} composer=${composer} ${flat ? '' : scroll}`];
  });

  await check('PW-07', 'shortcut «محادثة جديدة»: inside the app scope, opens a new chat', async () => {
    const shortcut = (manifest.shortcuts || []).find((s) => s.name === APP.shortcut);
    if (!shortcut) {
      return [false, `shortcuts ${JSON.stringify(manifest.shortcuts)}`];
    }
    const target = resolve(shortcut.url);
    const app = await context.newPage();
    await app.goto(target, { waitUntil: 'domcontentloaded' });
    await settle(app);
    const where = new URL(app.url()).pathname;
    const composer = await app.locator('#prompt-textarea').isVisible();
    const empty = await app.locator('[data-testid^="message-"], .message-render').count();
    await app.close();
    return [target.startsWith(scope) && where === '/c/new' && composer && empty === 0, `${target} -> ${where} composer=${composer}`];
  });

  await check('PW-08', 'offline: the installed app shows the Arabic offline page with «إعادة المحاولة»; axe 0', async () => {
    const app = await context.newPage();
    await context.setOffline(true);
    try {
      await app.goto(`${BASE}/c/new`, { waitUntil: 'domcontentloaded' });
      await app.waitForLoadState('load');
      const heading = (await app.locator('h1').first().textContent()) || '';
      const retry = await app.locator('a.retry').getAttribute('href');
      const [flat, scroll] = await noHScroll(app);
      await shot(app, 'pwa-offline-ar-phone');
      const [clean, violations] = await axe(app);
      const ok = heading.trim() === APP.offlineTitle && retry === '/' && flat && clean;
      return [ok, `h1=${heading.trim()} retry=${retry} ${flat ? '' : scroll} ${violations}`];
    } finally {
      await context.setOffline(false);
      await app.close();
    }
  });

  await check('PW-09', 'page errors', () => [errors.length === 0, errors.join(' | ')]);

  await context.close();
  fs.rmSync(profile, { recursive: true, force: true });
  console.log(`\n${passed} passed, ${failed} failed; screenshots in ${SHOTS}`);
  process.exit(failed ? 1 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
