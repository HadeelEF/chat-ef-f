#!/usr/bin/env node
/*
 * Browser checks of sidebar v5 (#221, toward #194): the rail, «Customize», the tool pages' way back, the phone drawer,
 * for an ADMIN and a USER, in Arabic and English, on desktop (1440×900, 1366×768) and phone (390×844, 360×740, touch)
 * widths; axe-core (WCAG 2.0/2.1 A and AA, 2.2 AA) on every screen, no page errors, no horizontal scroll.
 *
 *   node tests/ui/sidebar_v5.cjs <state.json from tests/ui/ui_stack.py> [screenshot-dir]
 *
 * Needs Node.js and Playwright with Chromium (require('playwright')). axe-core is fetched from the npm registry at a
 * pinned version and sha256, as the image build does. Prints PASS/FAIL per check (IDs in
 * docs/quality/concept1-interface-test-cases.md §11) and exits 1 on any failure.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const [stateFile, shotArg] = process.argv.slice(2);
if (!stateFile) {
  console.error('usage: node tests/ui/sidebar_v5.cjs <state.json> [screenshot-dir]');
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
    customize: 'التخصيص',
    forYou: 'لك',
    adminTools: 'للمسؤول فقط',
    connectors: 'الموصلات',
    builder: 'منشئ المساعدين',
    brand: 'بصير',
    skills: 'المهارات',
    documents: 'المستندات',
    projects: 'المشاريع',
  },
  en: {
    customize: 'Customize',
    forYou: 'For you',
    adminTools: 'Admins only',
    connectors: 'Connectors',
    builder: 'Agent Builder',
    brand: 'Baseer',
    skills: 'Skills',
    documents: 'Documents',
    projects: 'Projects',
  },
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

const box = (locator) => locator.boundingBox();

/** One sign-in per account (LibreChat limits sign-ins per address): later sessions reuse its cookies. */
const signedIn = {};

async function newSession(browser, { role, lang, viewport, phone }) {
  const context = await browser.newContext({
    viewport,
    isMobile: phone,
    hasTouch: phone,
    deviceScaleFactor: phone ? 3 : 1,
    locale: lang === 'ar' ? 'ar-SA' : 'en-US',
    storageState: signedIn[role],
  });
  const code = lang === 'ar' ? 'ar' : 'en-US';
  await context.addCookies([{ name: 'lang', value: code, url: BASE }]);
  await context.addInitScript((value) => {
    try {
      window.localStorage.setItem('lang', JSON.stringify(value));
    } catch {
      /* storage off */
    }
  }, code);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  if (signedIn[role]) {
    await page.goto(`${BASE}/c/new`, { waitUntil: 'domcontentloaded' });
  } else {
    const account = state.accounts[role];
    await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
    await page.locator('#email').fill(account.email);
    await page.locator('#password').fill(account.password);
    await page.getByTestId('login-button').click();
  }
  await page.waitForURL((url) => url.pathname.startsWith('/c/'), { timeout: 30000 });
  await settle(page);
  if (!signedIn[role]) {
    const { cookies } = await context.storageState();
    signedIn[role] = { cookies: cookies.filter((cookie) => cookie.name !== 'lang'), origins: [] };
  }
  return { context, page, errors };
}

/** LibreChat rotates the refresh token on every refresh, so the next session takes this one's latest cookies. */
async function endSession(role, context) {
  const { cookies } = await context.storageState();
  signedIn[role] = { cookies: cookies.filter((cookie) => cookie.name !== 'lang'), origins: [] };
  await context.close();
}

const shot = (page, name) =>
  page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: false }).catch(() => {});

/** LibreChat keeps a connection open, so «network idle» never comes: wait for the app's frame instead. */
async function settle(page) {
  await page.waitForLoadState('load');
  await page
    .locator('nav.efaiw-rail:visible, [data-testid$="open-sidebar-button"]:visible, main.efaiw-page:visible')
    .first()
    .waitFor({ timeout: 30000 });
  await page.waitForTimeout(400);
}

async function goto(page, route) {
  await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
  await settle(page);
}

async function cardIds(section) {
  return section
    .locator('li[data-testid^="efaiw-cz-"]')
    .evaluateAll((items) => items.map((i) => i.getAttribute('data-testid').replace('efaiw-cz-', '')));
}
const section = (page, name) =>
  page.locator('section', { has: page.getByRole('heading', { level: 2, name, exact: true }) });

/* ------------------------------------------------------------------------------------------------ desktop */
async function desktop(browser, { role, lang, viewport, full }) {
  const tag = `${role}-${lang}-${viewport.width}`;
  const t = TEXT[lang];
  const admin = role === 'admin';
  const { context, page, errors } = await newSession(browser, { role, lang, viewport, phone: false });
  const rail = page.locator('nav.efaiw-rail');
  const panel = page.locator('#efaiw-chats-panel');

  await check(`V5-D01 ${tag}`, 'rail: new chat, chats, Projects, Documents, Customize, at the start edge; no Skills, no More', async () => {
    const ids = ['new-chat-button', 'efaiw-rail-chats', 'efaiw-rail-projects', 'efaiw-rail-files', 'efaiw-rail-customize'];
    const ys = [];
    for (const id of ids) {
      ys.push((await box(rail.getByTestId(id))).y);
    }
    const sorted = ys.every((y, i) => i === 0 || y > ys[i - 1]);
    const r = await box(rail);
    const startEdge = lang === 'ar' ? Math.abs(r.x + r.width - viewport.width) < 2 : r.x < 2;
    const gone = (await page.getByTestId('efaiw-rail-skills').count()) + (await page.getByTestId('efaiw-rail-more').count());
    const label = await rail.getByTestId('efaiw-rail-customize').innerText();
    return [sorted && startEdge && gone === 0 && label.includes(t.customize), `ys=${ys} rail=${r.x},${r.width} gone=${gone} label=${label}`];
  });
  await shot(page, `${tag}-home`);

  await check(`V5-D02 ${tag}`, '«Customize» opens its page; the rail marks it; the chats panel stays', async () => {
    await rail.getByTestId('efaiw-rail-customize').click();
    await page.waitForURL(/\/customize$/);
    const h1 = await page.locator('main.efaiw-page h1').innerText();
    const current = await rail.getByTestId('efaiw-rail-customize').getAttribute('aria-current');
    return [h1 === t.customize && current === 'page' && (await panel.isVisible()), `h1=${h1} current=${current}`];
  });

  await check(`V5-D03 ${tag}`, `cards: «${t.forYou}» ready commands, skills, memory, bookmarks${admin ? '; «Admins only» marketplace, connectors' : '; no admin tools'}`, async () => {
    const mine = await cardIds(section(page, t.forYou));
    const okMine = JSON.stringify(mine) === JSON.stringify(['prompts', 'skills', 'memories', 'bookmarks']);
    const adminSection = section(page, t.adminTools);
    if (!admin) {
      return [okMine && (await adminSection.count()) === 0, `mine=${mine}`];
    }
    const theirs = await cardIds(adminSection);
    const badges = await adminSection.locator('.efaiw-admin-badge').count();
    const okAdmin =
      theirs[0] === 'marketplace' && theirs.includes('mcp-builder') && !theirs.includes('agents') && badges === theirs.length;
    return [okMine && okAdmin, `mine=${mine} admin=${theirs} badges=${badges}`];
  });
  await shot(page, `${tag}-customize`);

  await check(`V5-D04 ${tag}`, 'the daily-use tip («/», «$») is shown', async () =>
    (await page.locator('.efaiw-cz-tip').innerText()).includes('$'),
  );
  await check(`V5-D11 ${tag}`, 'no horizontal scroll on «Customize»', () => noHScroll(page));
  await check(`V5-D12 ${tag}`, 'axe: «Customize»', () => axe(page));

  if (full) {
    for (const [id, route] of [
      ['prompts', '/prompts'],
      ['skills', '/skills'],
      ['memories', '/memories'],
      ['bookmarks', '/bookmarks'],
    ]) {
      await check(`V5-D05 ${tag} ${id}`, `card «${id}» opens ${route}; the breadcrumb leads back to «Customize»`, async () => {
        await goto(page, '/customize');
        await page.getByTestId(`efaiw-cz-${id}`).locator('.efaiw-cz-link').click();
        await page.waitForURL(new RegExp(`${route}$`));
        const crumb = page.locator('nav.efaiw-crumb a');
        const current = await rail.getByTestId('efaiw-rail-customize').getAttribute('aria-current');
        const crumbText = await crumb.innerText();
        const scroll = await noHScroll(page);
        if (id === 'skills') {
          await shot(page, `${tag}-skills-breadcrumb`);
        }
        await crumb.click();
        await page.waitForURL(/\/customize$/);
        return [crumbText === t.customize && current === 'page' && scroll[0], `crumb=${crumbText} current=${current} ${scroll[1]}`];
      });
    }
    await check(`V5-D12 ${tag} skills`, 'axe: a tool page with its breadcrumb', async () => {
      await goto(page, '/skills');
      return axe(page);
    });

    await check(`V5-D10 ${tag}`, 'keyboard: Tab reaches a card, its ring shows, Enter opens it', async () => {
      await goto(page, '/customize');
      await page.locator('main.efaiw-page h1').click();
      let onCard = false;
      for (let i = 0; i < 40 && !onCard; i += 1) {
        await page.keyboard.press('Tab');
        onCard = await page.evaluate(() => document.activeElement?.classList.contains('efaiw-cz-link'));
      }
      const ring = await page.evaluate(() => getComputedStyle(document.activeElement, '::after').boxShadow);
      await page.keyboard.press('Enter');
      await page.waitForURL(/\/(prompts|skills|memories|bookmarks)$/);
      return [onCard && ring.includes('78, 97, 200'), `ring=${ring}`];
    });

    if (admin) {
      await check(`V5-D06 ${tag}`, 'connectors open in the panel under their name, «Customize» marked; back returns the chats', async () => {
        await goto(page, '/customize');
        await page.getByTestId('efaiw-cz-mcp-builder').locator('.efaiw-cz-link').click();
        const title = panel.locator('h2');
        await title.filter({ hasText: t.connectors }).waitFor({ timeout: 10000 });
        const current = await rail.getByTestId('efaiw-rail-customize').getAttribute('aria-current');
        await shot(page, `${tag}-connectors-panel`);
        const ax = await axe(page);
        await panel.getByTestId('efaiw-back-to-chats').click();
        const pressed = await rail.getByTestId('efaiw-rail-chats').getAttribute('aria-pressed');
        return [current === 'page' && pressed === 'true' && ax[0], `current=${current} pressed=${pressed} ${ax[1]}`];
      });
      await check(`V5-D07 ${tag}`, '«New assistant» starts a new chat with the builder in the panel', async () => {
        await goto(page, '/customize');
        await page.getByTestId('efaiw-cz-new-agent').click();
        await page.waitForURL(/\/c\/new/);
        await panel.locator('h2').filter({ hasText: t.builder }).waitFor({ timeout: 10000 });
        await shot(page, `${tag}-new-assistant`);
        await panel.getByTestId('efaiw-back-to-chats').click();
        return true;
      });
      await check(`V5-D08 ${tag}`, 'the marketplace card opens /agents; «Customize» stays marked', async () => {
        await goto(page, '/customize');
        await page.getByTestId('efaiw-cz-marketplace').locator('.efaiw-cz-link').click();
        await page.waitForURL(/\/agents/);
        return (await rail.getByTestId('efaiw-rail-customize').getAttribute('aria-current')) === 'page';
      });
      await check(`V5-D09 ${tag}`, 'with the panel collapsed, a panel tool opens it', async () => {
        await goto(page, '/customize');
        await rail.getByTestId('efaiw-rail-chats').click();
        await panel.waitFor({ state: 'detached', timeout: 5000 }).catch(() => {});
        const collapsed = !(await panel.isVisible().catch(() => false));
        await page.getByTestId('efaiw-cz-mcp-builder').locator('.efaiw-cz-link').click();
        await panel.locator('h2').filter({ hasText: t.connectors }).waitFor({ timeout: 10000 });
        await panel.getByTestId('efaiw-back-to-chats').click();
        return [collapsed, 'panel did not collapse first'];
      });
    }

    await check(`V5-D13 ${tag}`, 'shortcuts: one set of panel targets; Ctrl+Shift+S collapses and reopens the panel', async () => {
      await goto(page, '/c/new');
      const ids = await page
        .locator('[data-testid^="nav-panel-"]')
        .evaluateAll((els) => els.map((e) => e.getAttribute('data-testid')));
      const unique = new Set(ids).size === ids.length;
      await page.locator('body').click({ position: { x: viewport.width / 2, y: 10 } });
      await page.keyboard.press('Control+Shift+S');
      await page.waitForTimeout(500);
      const closed = !(await panel.isVisible().catch(() => false));
      await page.keyboard.press('Control+Shift+S');
      await page.waitForTimeout(500);
      const open = await panel.isVisible();
      return [unique && closed && open, `unique=${unique} closed=${closed} open=${open}`];
    });
    await check(`V5-D12 ${tag} home`, 'axe: the chat page with the rail and the panel', async () => {
      await goto(page, '/c/new');
      return axe(page);
    });
  }

  await check(`V5-D14 ${tag}`, 'no page errors', () => [errors.length === 0, errors.join(' | ')]);
  await endSession(role, context);
}

/* ------------------------------------------------------------------------------------------------ phone */
async function openDrawer(page) {
  /** The chat header's menu button, or a page's (EfSectionPage). */
  await page.locator('[data-testid$="open-sidebar-button"]:visible').first().click();
  await page.waitForFunction(() => {
    const d = document.getElementById('mobile-drawer');
    return d != null && !d.hasAttribute('inert');
  });
  await page.waitForTimeout(450); // the slide
}
/** Opens the drawer unless an earlier step left it open. */
async function ensureDrawer(page) {
  if (await page.evaluate(() => document.getElementById('mobile-drawer')?.hasAttribute('inert'))) {
    await openDrawer(page);
  }
}
async function drawerClosed(page) {
  await page.waitForFunction(() => document.getElementById('mobile-drawer')?.hasAttribute('inert'));
  return true;
}

async function phone(browser, { role, lang, viewport, full }) {
  const tag = `${role}-${lang}-${viewport.width}`;
  const t = TEXT[lang];
  const admin = role === 'admin';
  const { context, page, errors } = await newSession(browser, { role, lang, viewport, phone: true });
  const drawer = page.locator('#mobile-drawer');
  const tiles = drawer.locator('nav.efaiw-drawer-tiles');

  await check(`V5-P01 ${tag}`, 'drawer: «Baseer» and X (focused), search, then Projects, Documents, Customize; no tab bar, no floating button', async () => {
    await openDrawer(page);
    const brand = await drawer.locator('.efaiw-drawer-brand').innerText();
    const focused = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    const order = await tiles
      .locator('a')
      .evaluateAll((as) => as.map((a) => a.getAttribute('data-testid')));
    const search = await box(drawer.locator('.efaiw-side-search'));
    const first = await box(tiles);
    const legacy = (await page.locator('.efaiw-tabs, .efaiw-fab, [data-testid="efaiw-tab-more"]').count()) === 0;
    await shot(page, `${tag}-drawer`);
    return [
      brand === t.brand &&
        focused === 'close-sidebar-button' &&
        JSON.stringify(order) === JSON.stringify(['efaiw-drawer-projects', 'efaiw-drawer-files', 'efaiw-drawer-customize']) &&
        first.y > search.y &&
        legacy,
      `brand=${brand} focused=${focused} order=${order} legacy=${legacy}`,
    ];
  });

  await check(`V5-P02 ${tag}`, 'tiles: at least 44 px tall, names whole', async () => {
    const info = await tiles.locator('a').evaluateAll((as) =>
      as.map((a) => {
        const l = a.querySelector('.efaiw-drawer-tile-label');
        return { h: a.getBoundingClientRect().height, cut: l.scrollWidth > l.clientWidth + 1, text: l.textContent };
      }),
    );
    return [info.every((i) => i.h >= 44 && !i.cut), JSON.stringify(info)];
  });

  await check(`V5-P04 ${tag}`, 'dock: «New chat» (≥44 px) and the account at the bottom, below the history', async () => {
    const vh = viewport.height;
    const dockNew = await box(drawer.getByTestId('nav-new-chat-fab'));
    const me = await drawer.locator('.efaiw-dock [data-testid="nav-user"]').count();
    const list = await box(drawer.locator('#chat-history-nav'));
    return [
      dockNew.height >= 44 && dockNew.y + dockNew.height <= vh + 1 && me === 1 && list.y + list.height <= dockNew.y + 1,
      `new=${JSON.stringify(dockNew)} me=${me} list=${JSON.stringify(list)}`,
    ];
  });

  if (full) {
    await check(`V5-P03 ${tag}`, '«Chats» with the sort and filter menu, the chips, and the history under the tiles', async () => {
      const sub = await drawer.locator('.efaiw-chats-sub').innerText();
      const filter = await drawer.locator('.efaiw-chats-sub #chat-filter-menu-button').count();
      const chips = await drawer.locator('[aria-pressed]').filter({ hasText: lang === 'ar' ? 'الكل' : 'All' }).count();
      const item = await box(drawer.locator('[data-testid="convo-item"]').first());
      const tilesBox = await box(tiles);
      return [sub.includes(lang === 'ar' ? 'الدردشات' : 'Chats') && filter === 1 && chips >= 1 && item.y > tilesBox.y, `sub=${sub} filter=${filter} chips=${chips}`];
    });
    await check(`V5-P12 ${tag}`, 'axe: the open drawer', () => axe(page));
    await check(`V5-P13 ${tag}`, 'the account menu opens from the dock, inside the screen', async () => {
      await drawer.locator('.efaiw-dock [data-testid="nav-user"]').tap();
      const menu = page.locator('.account-settings-popover:visible');
      await menu.waitFor({ timeout: 5000 });
      await page.waitForTimeout(300); // the fade-in
      const b = await box(menu);
      await shot(page, `${tag}-account`);
      await page.keyboard.press('Escape');
      return [b.x >= 0 && b.x + b.width <= viewport.width + 1 && b.y >= 0, JSON.stringify(b)];
    });
  }

  await check(`V5-P05 ${tag}`, '«Customize» tile closes the drawer and opens the page; cards in one column; no horizontal scroll', async () => {
    await ensureDrawer(page);
    await tiles.getByTestId('efaiw-drawer-customize').tap();
    await drawerClosed(page);
    await page.waitForURL(/\/customize$/);
    await settle(page);
    const xs = await page
      .locator('li[data-testid^="efaiw-cz-"]')
      .evaluateAll((items) => items.map((i) => Math.round(i.getBoundingClientRect().x)));
    const menu = await page.locator('main.efaiw-page').getByRole('button', { name: lang === 'ar' ? /القائمة|الشريط/ : /sidebar|menu/i }).count();
    const scroll = await noHScroll(page);
    await shot(page, `${tag}-customize`);
    return [new Set(xs).size === 1 && xs.length >= 4 && menu >= 1 && scroll[0], `xs=${xs} menu=${menu} ${scroll[1]}`];
  });
  await check(`V5-P12 ${tag} customize`, 'axe: «Customize» on a phone', () => axe(page));

  if (full) {
    await check(`V5-P06 ${tag}`, 'a tool page leads back to «Customize»', async () => {
      await page.getByTestId('efaiw-cz-skills').locator('.efaiw-cz-link').tap();
      await page.waitForURL(/\/skills$/);
      const back = page.getByTestId('efaiw-page-parent');
      const label = await back.getAttribute('aria-label');
      await shot(page, `${tag}-skills`);
      await back.tap();
      await page.waitForURL(/\/customize$/);
      return [label != null && label.includes(t.customize), `label=${label}`];
    });
    await check(`V5-P07 ${tag}`, 'reopened on «Customize», the drawer marks its tile', async () => {
      await openDrawer(page);
      const current = await tiles.getByTestId('efaiw-drawer-customize').getAttribute('aria-current');
      await shot(page, `${tag}-drawer-on-customize`);
      await page.keyboard.press('Escape');
      await drawerClosed(page);
      return [current === 'page', `current=${current}`];
    });
    if (admin) {
      await check(`V5-P08 ${tag}`, 'connectors open in the drawer under their name; back returns the chats', async () => {
        await page.getByTestId('efaiw-cz-mcp-builder').locator('.efaiw-cz-link').tap();
        await page.waitForFunction(() => !document.getElementById('mobile-drawer')?.hasAttribute('inert'));
        await drawer.locator('h2').filter({ hasText: t.connectors }).waitFor({ timeout: 10000 });
        await page.waitForTimeout(450);
        await shot(page, `${tag}-connectors`);
        await drawer.getByTestId('efaiw-back-to-chats').tap();
        await tiles.waitFor({ timeout: 5000 });
        return true;
      });
    }
    await check(`V5-P09 ${tag}`, 'a chat in the drawer opens and closes the drawer', async () => {
      await ensureDrawer(page);
      await drawer.locator('[data-testid="convo-item"] > button').first().tap();
      await drawerClosed(page);
      await page.waitForURL(/\/c\/[0-9a-f-]{36}/);
      return true;
    });
    await check(`V5-P10 ${tag}`, '«New chat» in the dock closes the drawer and opens a new chat', async () => {
      await ensureDrawer(page);
      await drawer.getByTestId('nav-new-chat-fab').tap();
      await drawerClosed(page);
      await page.waitForURL(/\/c\/new/);
      return true;
    });
    await check(`V5-P11 ${tag}`, 'Escape closes the drawer', async () => {
      await ensureDrawer(page);
      await page.keyboard.press('Escape');
      return drawerClosed(page);
    });
  }

  await check(`V5-P14 ${tag}`, 'no page errors', () => [errors.length === 0, errors.join(' | ')]);
  await endSession(role, context);
}

(async () => {
  const browser = await chromium.launch();
  console.log(`# sidebar v5 UI checks (#221)  base=${BASE}  image=${state.image}  date=${new Date().toISOString()}`);
  try {
    for (const role of ['employee', 'admin']) {
      await desktop(browser, { role, lang: 'ar', viewport: { width: 1440, height: 900 }, full: true });
      await desktop(browser, { role, lang: 'ar', viewport: { width: 1366, height: 768 }, full: false });
      await desktop(browser, { role, lang: 'en', viewport: { width: 1440, height: 900 }, full: role === 'admin' });
      await phone(browser, { role, lang: 'ar', viewport: { width: 390, height: 844 }, full: true });
      await phone(browser, { role, lang: 'ar', viewport: { width: 360, height: 740 }, full: role === 'employee' });
      await phone(browser, { role, lang: 'en', viewport: { width: 390, height: 844 }, full: false });
    }
  } finally {
    await browser.close();
  }
  console.log(`# result: ${passed}/${passed + failed} passed  screenshots=${SHOTS}`);
  process.exit(failed ? 1 : 0);
})();
