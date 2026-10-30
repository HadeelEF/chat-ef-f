#!/usr/bin/env node
/*
 * Browser checks of the phone app feel (#238): sign-in fields that do not make iPhone zoom, 44 px touch targets,
 * interface chrome without text selection, iPhone safe areas (viewport-fit=cover), the install row and the iPhone
 * hint, nothing of either inside the installed app, and the new-version bar after a deploy. Arabic (and the hint in
 * English) on an iPhone 13 Pro Max as an installed app (428×879), plus 390×844 and 360×740 for the reply toolbar.
 *
 *   node tests/ui/mobile_app.cjs <state.json from tests/ui/ui_stack.py> [screenshot-dir]
 *
 * Needs Node.js and Playwright with Chromium (require('playwright')); the full Chromium, whose DevTools Protocol
 * emulates the iPhone safe areas. Chromium stands in for Safari: real-device checks stay with the owner (#234).
 * axe-core is fetched from the npm registry at a pinned version and sha256. Prints PASS/FAIL per check (IDs in
 * docs/quality/concept1-interface-test-cases.md §15) and exits 1 on any failure. MA-12 simulates a deploy by
 * changing sw.js in the stack's mounted client for a moment, then restores it.
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
  console.error('usage: node tests/ui/mobile_app.cjs <state.json> [screenshot-dir]');
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

const TEXT = {
  ar: {
    install: 'تثبيت التطبيق',
    hintTitle: 'ثبّت بصير على جوالك',
    hintOk: 'فهمت',
    update: 'نسخة جديدة من بصير متاحة.',
    reload: 'تحديث',
  },
  en: { hintTitle: 'Install Baseer on your phone' },
};
/** iPhone 13 Pro Max as an installed app: the screen less the status bar (the bar stays opaque, «default»). */
const IPHONE_APP = { width: 428, height: 879 };
const HOME_INDICATOR = 34;
const NOTCH_LANDSCAPE = 47;
const MIN_TARGET = 44;

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

async function axe(page, include) {
  await page.addScriptTag({ content: AXE_JS });
  const res = await page.evaluate(
    ([tags, sel]) => window.axe.run(sel ? { include: [sel] } : document, { runOnly: { type: 'tag', values: tags } }),
    [AXE_TAGS, include],
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

/** Visible elements under `selector` smaller than 44×44, as «name w×h». */
async function smallTargets(page, selector) {
  return page.locator(selector).evaluateAll((els, min) => {
    const out = [];
    for (const el of els) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0 || el.closest('[inert]')) continue;
      if (r.width < min || r.height < min) {
        const name = (el.getAttribute('aria-label') || el.textContent || el.tagName).trim().slice(0, 30);
        out.push(`${name} ${Math.round(r.width)}×${Math.round(r.height)}`);
      }
    }
    return out;
  }, MIN_TARGET);
}

/** The reply toolbar's model name: on screen (it may end in «…»), never cut by the screen edge. */
async function modelNameOnScreen(page) {
  return page.evaluate(() => {
    const el = [...document.querySelectorAll('.agent-turn .efaiw-reply-model')].pop();
    if (!el) return [true, 'no model name'];
    const r = el.getBoundingClientRect();
    return [r.left >= 0 && r.right <= window.innerWidth && r.width > 0, `model name ${Math.round(r.left)}–${Math.round(r.right)} of ${window.innerWidth}`];
  });
}

/** LibreChat keeps a connection open, so «network idle» never comes: wait for the app's frame instead. */
async function settle(page) {
  await page.waitForLoadState('load');
  await page
    .locator('[data-testid$="open-sidebar-button"]:visible, nav.efaiw-rail:visible, main.efaiw-page:visible, #email')
    .first()
    .waitFor({ timeout: 30000 });
  await page.waitForTimeout(500);
}

/** One sign-in per account (LibreChat limits sign-ins per address): later contexts reuse its cookies. */
let cookies = null;
async function session(browser, { device = 'iphone', viewport = IPHONE_APP, lang = 'ar', installed = false, signIn = true } = {}) {
  const descriptor = { ...devices[device === 'iphone' ? 'iPhone 13 Pro Max' : 'Pixel 7'] };
  delete descriptor.defaultBrowserType;
  const context = await browser.newContext({
    ...descriptor,
    viewport,
    locale: lang === 'ar' ? 'ar-SA' : 'en-US',
    serviceWorkers: 'allow',
    storageState: cookies ? { cookies, origins: [] } : undefined,
  });
  const code = lang === 'ar' ? 'ar' : 'en-US';
  await context.addCookies([{ name: 'lang', value: code, url: BASE }]);
  await context.addInitScript(
    ([value, standalone]) => {
      try {
        window.localStorage.setItem('lang', JSON.stringify(value));
      } catch {
        /* storage off */
      }
      if (standalone) {
        Object.defineProperty(navigator, 'standalone', { get: () => true });
      }
    },
    [code, installed],
  );
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  if (!signIn) {
    return { context, page, errors };
  }
  if (cookies) {
    await page.goto(`${BASE}/c/new`, { waitUntil: 'domcontentloaded' });
  } else {
    const account = state.accounts.employee;
    await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
    await page.locator('#email').fill(account.email);
    await page.locator('#password').fill(account.password);
    await page.getByTestId('login-button').click();
  }
  await page.waitForURL((url) => url.pathname.startsWith('/c/'), { timeout: 30000 });
  await settle(page);
  return { context, page, errors };
}
/** LibreChat rotates the refresh token on every refresh, so the next context takes this one's latest cookies. */
async function close({ context }) {
  const s = await context.storageState();
  cookies = s.cookies.filter((cookie) => cookie.name !== 'lang');
  await context.close();
}

async function openDrawer(page) {
  await page.locator('[data-testid$="open-sidebar-button"]:visible').first().click();
  await page.waitForFunction(() => {
    const d = document.getElementById('mobile-drawer');
    return d != null && !d.hasAttribute('inert');
  });
  await page.waitForTimeout(450);
}
async function openAccountMenu(page) {
  await openDrawer(page);
  await page.locator('#mobile-drawer [data-testid="nav-user"]').click();
  await page.waitForTimeout(300);
}
async function openChatWithReply(page) {
  await openDrawer(page);
  await page.locator('#mobile-drawer [data-testid="convo-item"]').first().click();
  /** «Read aloud» comes first and is hidden on phones, so wait for a visible one. */
  await page.locator('.agent-turn .hover-button:visible').first().waitFor({ timeout: 20000 });
  await page.waitForTimeout(500);
}

async function main() {
  const browser = await chromium.launch({ channel: 'chromium' });
  const allErrors = [];

  // Sign-in page, as on the iPhone.
  {
    const s = await session(browser, { signIn: false });
    const { page } = s;
    await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
    await settle(page);
    await check('MA-01', 'viewport-fit=cover: iPhone applies the safe-area spacing', async () => {
      const content = await page.locator('meta[name="viewport"]').getAttribute('content');
      return [/viewport-fit=cover/.test(content || ''), content];
    });
    await check('MA-02', 'sign-in fields at 16 px; the e-mail keyboard, no capital first letter, no autocorrect', async () => {
      const fields = await page.evaluate(() =>
        ['#email', '#password'].map((sel) => {
          const el = document.querySelector(sel);
          const attr = (name) => el.getAttribute(name);
          return {
            sel,
            size: parseFloat(getComputedStyle(el).fontSize),
            inputmode: attr('inputmode'),
            autocapitalize: attr('autocapitalize'),
            autocorrect: attr('autocorrect'),
            spellcheck: attr('spellcheck'),
            autocomplete: attr('autocomplete'),
          };
        }),
      );
      const [email, password] = fields;
      const ok =
        email.size >= 16 &&
        password.size >= 16 &&
        email.inputmode === 'email' &&
        email.autocapitalize === 'none' &&
        email.autocorrect === 'off' &&
        email.spellcheck === 'false' &&
        email.autocomplete === 'email' &&
        password.autocomplete === 'current-password';
      return [ok, JSON.stringify(fields)];
    });
    await check('MA-03', 'sign-in: the password eye and «سجّل الآن» are 44 px targets', async () => {
      const small = await smallTargets(page, '.group\\/secret-input button, a[href$="/register"]');
      const count = await page.locator('.group\\/secret-input button, a[href$="/register"]').count();
      return [count >= 2 && small.length === 0, `count=${count} ${small.join(' | ')}`];
    });
    await shot(page, 'ma-login-iphone');
    allErrors.push(...s.errors);
    await s.context.close();
  }

  // Home, drawer and a chat, as the installed app on an iPhone 13 Pro Max.
  {
    const s = await session(browser, { installed: true });
    const { page } = s;
    await check('MA-04', 'home: header buttons 44 px; every visible text field at least 16 px', async () => {
      const small = await smallTargets(page, '[data-efaiw="chat-header"] button');
      const fonts = await page.evaluate(() =>
        [...document.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=file]):not([type=hidden]), textarea')]
          .filter((el) => el.getBoundingClientRect().width > 0)
          .map((el) => ({ id: el.id || el.name || el.tagName, size: parseFloat(getComputedStyle(el).fontSize) }))
          .filter((f) => f.size < 16),
      );
      return [small.length === 0 && fonts.length === 0, `${small.join(' | ')} ${JSON.stringify(fonts)}`];
    });
    await check('MA-07', 'no text selection or long-press menu on chrome; message text and fields stay selectable', async () => {
      await openChatWithReply(page);
      const sel = await page.evaluate(() => {
        const us = (el) => (el ? getComputedStyle(el).webkitUserSelect || getComputedStyle(el).userSelect : 'missing');
        return {
          headerButton: us(document.querySelector('[data-efaiw="chat-header"] button')),
          toolbarButton: us(document.querySelector('.agent-turn .hover-button')),
          replyText: us(document.querySelector('.agent-turn .markdown p, .agent-turn p')),
          composer: us(document.querySelector('#prompt-textarea')),
        };
      });
      const ok = sel.headerButton === 'none' && sel.toolbarButton === 'none' && sel.replyText !== 'none' && sel.composer === 'text';
      return [ok, JSON.stringify(sel)];
    });
    await check('MA-05', 'reply toolbar: every button 44 px, in one row, the model name on screen, no sideways scroll (428 px)', async () => {
      const small = await smallTargets(page, '.agent-turn .hover-button');
      const rows = await page.locator('.agent-turn .hover-button:visible').evaluateAll((els) =>
        new Set(els.map((el) => Math.round(el.getBoundingClientRect().top))).size,
      );
      const [flat, scroll] = await noHScroll(page);
      const [named, where] = await modelNameOnScreen(page);
      await shot(page, 'ma-chat-iphone-app');
      return [small.length === 0 && rows === 1 && flat && named, `${small.join(' | ')} rows=${rows} ${where} ${flat ? '' : scroll}`];
    });
    await check('MA-08a', 'iPhone portrait: the composer clears the home indicator (34 px)', async () => {
      const cdp = await s.context.newCDPSession(page);
      await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 0, bottom: HOME_INDICATOR, left: 0, right: 0 } });
      await page.waitForTimeout(300);
      const gap = await page.evaluate(() => {
        const box = document.querySelector('form [data-testid="composer-surface"]') || document.querySelector('#prompt-textarea');
        return Math.round(window.innerHeight - box.getBoundingClientRect().bottom);
      });
      await shot(page, 'ma-chat-iphone-safe-area');
      await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 0, bottom: 0, left: 0, right: 0 } });
      return [gap >= HOME_INDICATOR, `composer ${gap} px above the bottom edge`];
    });
    await check('MA-06', 'drawer: close, filter and each chat menu are 44 px targets', async () => {
      await openDrawer(page);
      const small = await smallTargets(page, '#mobile-drawer :is(.efaiw-chats-close, #chat-filter-menu-button, button[id^="conversation-menu-"])');
      const count = await page.locator('#mobile-drawer :is(.efaiw-chats-close, #chat-filter-menu-button, button[id^="conversation-menu-"])').count();
      await shot(page, 'ma-drawer-iphone-app');
      return [count >= 3 && small.length === 0, `count=${count} ${small.join(' | ')}`];
    });
    await check('MA-11', 'inside the installed app: no install hint and no «تثبيت التطبيق» row', async () => {
      const hint = await page.locator('.efaiw-install-hint').count();
      await page.locator('#mobile-drawer [data-testid="nav-user"]').click();
      await page.waitForTimeout(300);
      const row = await page.getByTestId('efaiw-install-app').count();
      await page.keyboard.press('Escape');
      return [hint === 0 && row === 0, `hint=${hint} row=${row}`];
    });
    await check('MA-08b', 'iPhone landscape: header and composer clear the notch (47 px each side)', async () => {
      await page.setViewportSize({ width: 926, height: 407 });
      const cdp = await s.context.newCDPSession(page);
      await cdp.send('Emulation.setSafeAreaInsetsOverride', {
        insets: { top: 0, bottom: 21, left: NOTCH_LANDSCAPE, right: NOTCH_LANDSCAPE },
      });
      await page.goto(`${BASE}/c/new`, { waitUntil: 'domcontentloaded' });
      await settle(page);
      const out = await page.evaluate((notch) => {
        const els = [...document.querySelectorAll('[data-efaiw="chat-header"] button, form [data-testid="composer-surface"]')];
        return els
          .map((el) => el.getBoundingClientRect())
          .filter((r) => r.width > 0 && (r.left < notch || r.right > window.innerWidth - notch))
          .map((r) => `${Math.round(r.left)}–${Math.round(r.right)}`);
      }, NOTCH_LANDSCAPE);
      const [flat, scroll] = await noHScroll(page);
      await shot(page, 'ma-landscape-iphone-safe-area');
      await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets: { top: 0, bottom: 0, left: 0, right: 0 } });
      return [out.length === 0 && flat, `${out.join(' | ')} ${flat ? '' : scroll}`];
    });
    allErrors.push(...s.errors);
    await close(s);
  }

  // The reply toolbar on narrower phones.
  for (const viewport of [{ width: 390, height: 844 }, { width: 360, height: 740 }]) {
    const s = await session(browser, { device: 'android', viewport, installed: true });
    await check(`MA-05 ${viewport.width}`, `reply toolbar: 44 px buttons in one row, the model name on screen, no sideways scroll (${viewport.width} px)`, async () => {
      await openChatWithReply(s.page);
      const small = await smallTargets(s.page, '.agent-turn .hover-button');
      const rows = await s.page.locator('.agent-turn .hover-button:visible').evaluateAll((els) =>
        new Set(els.map((el) => Math.round(el.getBoundingClientRect().top))).size,
      );
      const [flat, scroll] = await noHScroll(s.page);
      const [named, where] = await modelNameOnScreen(s.page);
      await shot(s.page, `ma-chat-${viewport.width}`);
      return [small.length === 0 && rows === 1 && flat && named, `${small.join(' | ')} rows=${rows} ${where} ${flat ? '' : scroll}`];
    });
    allErrors.push(...s.errors);
    await close(s);
  }

  // Android in the browser: the menu row opens the browser's install dialog.
  {
    const s = await session(browser, { device: 'android', viewport: { width: 412, height: 839 } });
    const { page } = s;
    await check('MA-09', 'Android: «تثبيت التطبيق» appears with the browser offer, opens its dialog, goes once installed', async () => {
      await page.evaluate(() => {
        const event = new Event('beforeinstallprompt', { cancelable: true });
        event.prompt = () => {
          window.__efaiwPrompted = (window.__efaiwPrompted || 0) + 1;
          return Promise.resolve();
        };
        event.userChoice = Promise.resolve({ outcome: 'accepted' });
        window.dispatchEvent(event);
      });
      await openAccountMenu(page);
      const row = page.getByTestId('efaiw-install-app');
      const label = (await row.textContent()) || '';
      /** The row only: upstream's menu already fails aria-required-children for its e-mail line (role=note). */
      const [clean, violations] = await axe(page, '[data-testid="efaiw-install-app"]');
      await shot(page, 'ma-android-install-row');
      await row.click();
      await page.waitForTimeout(300);
      const prompted = await page.evaluate(() => window.__efaiwPrompted || 0);
      await page.evaluate(() => window.dispatchEvent(new Event('appinstalled')));
      await page.locator('#mobile-drawer [data-testid="nav-user"]').click();
      await page.waitForTimeout(300);
      const after = await page.getByTestId('efaiw-install-app').count();
      await page.keyboard.press('Escape');
      const hint = await page.locator('.efaiw-install-hint').count();
      const ok = label.includes(TEXT.ar.install) && clean && prompted === 1 && after === 0 && hint === 0;
      return [ok, `label=${label} prompted=${prompted} after=${after} hint=${hint} ${violations}`];
    });
    allErrors.push(...s.errors);
    await close(s);
  }

  // iPhone in the browser: the hint, once; the menu row brings it back.
  {
    const s = await session(browser, { viewport: { width: 428, height: 746 } });
    const { page } = s;
    await check('MA-10', 'iPhone browser: the hint once, alone (axe 0); «فهمت» hides it for good and lets the skills tip show; the menu row shows it again', async () => {
      const hint = page.locator('.efaiw-install-hint');
      await hint.waitFor({ timeout: 10000 });
      const text = (await hint.textContent()) || '';
      /** One card at a time: the skills tip waits until the hint is dismissed. */
      const tipWhileHint = await page.locator('.efaiw-skills-tip').count();
      const [clean, violations] = await axe(page, '.efaiw-install-hint');
      const [flat, scroll] = await noHScroll(page);
      await shot(page, 'ma-iphone-install-hint');
      await hint.getByRole('button', { name: TEXT.ar.hintOk }).click();
      const gone = (await hint.count()) === 0;
      const tipAfter = await page.locator('.efaiw-skills-tip').count();
      await page.reload({ waitUntil: 'domcontentloaded' });
      await settle(page);
      const stillGone = (await page.locator('.efaiw-install-hint').count()) === 0;
      await openAccountMenu(page);
      await page.getByTestId('efaiw-install-app').click();
      const back = await page.locator('.efaiw-install-hint').isVisible();
      const ok = text.includes(TEXT.ar.hintTitle) && clean && flat && gone && stillGone && back && tipWhileHint === 0 && tipAfter === 1;
      return [ok, `text=${text.slice(0, 60)} tips=${tipWhileHint}/${tipAfter} gone=${gone} stillGone=${stillGone} back=${back} ${flat ? '' : scroll} ${violations}`];
    });
    allErrors.push(...s.errors);
    await close(s);
  }
  {
    const s = await session(browser, { viewport: { width: 428, height: 746 }, lang: 'en' });
    await check('MA-10 en', 'iPhone browser in English: the hint reads «Install Baseer on your phone»', async () => {
      const hint = s.page.locator('.efaiw-install-hint');
      await hint.waitFor({ timeout: 10000 });
      return [((await hint.textContent()) || '').includes(TEXT.en.hintTitle), await hint.textContent()];
    });
    allErrors.push(...s.errors);
    await close(s);
  }

  // A deploy while the app is open: the new-version bar.
  {
    const s = await session(browser, { device: 'android', viewport: { width: 412, height: 839 }, installed: true });
    const { page } = s;
    const swFile = path.join(state.work, 'dist', 'sw.js');
    const original = fs.readFileSync(swFile);
    await check('MA-12', 'a deploy while open: «نسخة جديدة من بصير متاحة — تحديث» (axe 0); «تحديث» reloads into the new version', async () => {
      await page.evaluate(() => navigator.serviceWorker.ready);
      const controlled = await page.evaluate(() => navigator.serviceWorker.controller != null);
      fs.writeFileSync(swFile, Buffer.concat([original, Buffer.from(`\n/* efaiw test deploy ${Date.now()} */\n`)]));
      await page.evaluate(() => navigator.serviceWorker.getRegistration().then((r) => r.update()));
      const bar = page.locator('.efaiw-update-bar');
      await bar.waitFor({ timeout: 20000 });
      const text = (await bar.textContent()) || '';
      const [clean, violations] = await axe(page, '.efaiw-update-bar');
      await shot(page, 'ma-update-bar');
      await Promise.all([page.waitForEvent('load'), bar.getByRole('button', { name: TEXT.ar.reload }).click()]);
      await settle(page);
      const after = await page.locator('.efaiw-update-bar').count();
      const ok = controlled && text.includes(TEXT.ar.update) && clean && after === 0;
      return [ok, `controlled=${controlled} text=${text} after=${after} ${violations}`];
    });
    fs.writeFileSync(swFile, original);
    allErrors.push(...s.errors);
    await close(s);
  }

  await check('MA-13', 'page errors', () => [allErrors.length === 0, allErrors.join(' | ')]);

  await browser.close();
  console.log(`\n${passed} passed, ${failed} failed; screenshots in ${SHOTS}`);
  process.exit(failed ? 1 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
