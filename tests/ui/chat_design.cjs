#!/usr/bin/env node
/*
 * Browser checks of the chat design (#224): the message box («+», skills as text, placeholders, the skills tip), a
 * reply (blue headings, no summary card, toolbar, «More», download menu, document bar, suggestions), the model menu's
 * line on Pro, a skill and a file kept across a model switch (#241), the phone's temporary chat, bottom sheets and «$»
 * list above the message box (#241), in Arabic and English, on desktop (1440×900) and phone (390×844, touch);
 * axe-core (WCAG 2.0/2.1 A and AA, 2.2 AA) on each screen, no page errors, no horizontal scroll. The replies come from
 * the deterministic mock model (tests/integration/mock-llm, SYNTH-DESIGN-*); its request log shows what reached it.
 *
 *   node tests/ui/chat_design.cjs <state.json from tests/ui/ui_stack.py> [screenshot-dir]
 *
 * Needs Node.js, Docker (to read the mock model's log) and Playwright with Chromium (require('playwright')). axe-core
 * is fetched from the npm registry at a pinned version and sha256. Prints PASS/FAIL per check (IDs in
 * docs/quality/concept1-interface-test-cases.md §12) and exits 1 on any failure.
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
  console.error('usage: node tests/ui/chat_design.cjs <state.json> [screenshot-dir]');
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

/** A skill made for the test: its text carries a marker the mock model reports when the text reaches it. */
const SKILL = {
  name: 'synthetic-minutes',
  displayTitle: 'كتابة المحاضر الاصطناعية',
  description: 'مثال: «حوّل ملاحظات الاجتماع إلى محضر»',
  body: '# محضر اصطناعي\nاكتب الرد محضراً بعنوان وبنود مرقمة وقسم «المهام». SYNTH-SKILL-MINUTES',
};
/** Two more synthetic skills (#241), so the phone's list has more rows than it shows. */
const MORE_SKILLS = [
  {
    name: 'synthetic-letters',
    displayTitle: 'الخطابات الاصطناعية',
    description: 'مثال: «اكتب خطاب شكر»',
    body: '# خطاب اصطناعي\nاكتب الرد خطاباً رسمياً. SYNTH-SKILL-LETTERS',
  },
  {
    name: 'synthetic-tables',
    displayTitle: 'الجداول الاصطناعية',
    description: 'مثال: «رتّب البيانات في جدول»',
    body: '# جدول اصطناعي\nاكتب الرد جدولاً. SYNTH-SKILL-TABLES',
  },
];
/** A synthetic text file attached before a model switch (#241); the mock reports its marker when it reaches it. */
const SWITCH_FILE = {
  name: 'synthetic-switch.txt',
  mimeType: 'text/plain',
  buffer: Buffer.from('ملف اصطناعي للاختبار. SYNTH-FILE-SWITCH\n', 'utf8'),
};

const TEXT = {
  ar: {
    placeholder: 'اسأل بصير، أو اكتب / لأمر جاهز و$ لمهارة',
    skillPlaceholder: 'اكتب طلبك، مثل: حوّل ملاحظاتي إلى محضر',
    temporaryPlaceholder: 'اسأل بصير. لن تُحفظ هذه الدردشة',
    webNote: 'البحث في الإنترنت يعمل تلقائياً',
    howto: 'كيف تستخدم مهارة؟',
    auto: 'تلقائي',
    brandSkill: 'هوية صندوق البيئة',
    tipOk: 'فهمت',
    model: 'بصير لايت',
    plusModel: 'بصير بلس',
    downloadTitle: 'تنزيل الرد',
    letter: 'خطاب رسمي',
    shorten: 'اختصر',
    share: 'مشاركة المحادثة',
    proNote: 'لا يبحث في الإنترنت حالياً',
    download: 'تنزيل',
  },
  en: {
    placeholder: 'Ask Baseer, or type / for a ready command and $ for a skill',
    model: 'بصير لايت',
    downloadTitle: 'Download reply',
    download: 'Download',
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

/** The mock model's requests (one JSON line each), newest last. */
function mockRequests() {
  const out = execFileSync('docker', ['logs', `${state.project}-mock-llm-1`], {
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return out
    .split('\n')
    .filter((line) => line.startsWith('{'))
    .map((line) => JSON.parse(line))
    .filter((entry) => entry.event === 'chat.completions');
}

async function apiLogin(role) {
  const account = state.accounts[role];
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: account.email, password: account.password }),
  });
  if (!res.ok) {
    throw new Error(`login ${role}: HTTP ${res.status}`);
  }
  return (await res.json()).token;
}

async function createSkill(token, skill = SKILL) {
  const res = await fetch(`${BASE}/api/skills`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(skill),
  });
  if (!res.ok && res.status !== 409) {
    throw new Error(`create skill: HTTP ${res.status} ${(await res.text()).slice(0, 200)}`);
  }
}

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
    permissions: ['clipboard-read', 'clipboard-write'],
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

async function endSession(role, context) {
  const { cookies } = await context.storageState();
  signedIn[role] = { cookies: cookies.filter((cookie) => cookie.name !== 'lang'), origins: [] };
  await context.close();
}

const shot = (page, name) =>
  page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: false }).catch(() => {});

async function settle(page) {
  await page.waitForLoadState('load');
  await page.getByTestId('text-input').waitFor({ timeout: 30000 });
  await page.waitForTimeout(500);
}

const box = (page) => page.getByTestId('text-input');
/** Menus fade in: screenshots and axe wait for the end of it. */
const FADE_MS = 400;
const lastReply = (page) => page.locator('.agent-turn').last();
const lastTools = (page) => page.locator('[data-efaiw-actions="last"]');

/** Types and sends a message, then waits for the reply's toolbar (the reply has finished). */
async function send(page, text) {
  const before = await page.locator('.agent-turn').count();
  await box(page).fill(text);
  await page.getByTestId('send-button').click();
  await page.waitForFunction(
    (n) => document.querySelectorAll('.agent-turn').length > n,
    before,
    { timeout: 30000 },
  );
  await lastTools(page).locator('[data-testid="copy-response-button"]').waitFor({ timeout: 30000 });
  await page.waitForTimeout(400);
}

/** Where a list the message box opens («$», «/») sits against the box and the chat header (#241). */
function composerListGeometry(page, selector) {
  return page.evaluate((sel) => {
    const pop = document.querySelector(sel);
    const p = pop.getBoundingClientRect();
    const b = document.querySelector('form .bg-surface-chat.border').getBoundingClientRect();
    const header = document.querySelector('[data-efaiw="chat-header"]');
    const list = pop.querySelector('.ReactVirtualized__List');
    const howto = pop.querySelector('.efaiw-skills-howto');
    return {
      top: Math.round(p.top),
      bottom: Math.round(p.bottom),
      width: Math.round(p.width),
      boxTop: Math.round(b.top),
      boxBottom: Math.round(b.bottom),
      headerBottom: header ? Math.round(header.getBoundingClientRect().bottom) : 0,
      vh: window.innerHeight,
      above: p.bottom <= b.top + 0.5,
      list: list ? Math.round(list.getBoundingClientRect().height) : 0,
      rows: pop.querySelectorAll('[id^="skill-item-"]').length,
      howto: howto != null && getComputedStyle(howto).display !== 'none',
      foot: [...pop.querySelectorAll('.efaiw-skills-foot button')].map((x) => Math.round(x.getBoundingClientRect().height)),
    };
  }, selector);
}

async function openPlus(page) {
  await page.locator('#tools-dropdown-button').click();
  const menu = page.locator('#tools-dropdown-menu');
  await menu.waitFor();
  await page.waitForTimeout(FADE_MS);
  return menu;
}

/* ------------------------------------------------------------------------------------------------ desktop, Arabic */
async function desktopArabic(browser) {
  const tag = 'employee-ar-1440';
  const t = TEXT.ar;
  const { context, page, errors } = await newSession(browser, {
    role: 'employee',
    lang: 'ar',
    viewport: { width: 1440, height: 900 },
    phone: false,
  });

  await check(`CD-01 ${tag}`, 'new chat: the box hints «/» and «$»; the skills tip shows once', async () => {
    const placeholder = await box(page).getAttribute('placeholder');
    const tip = page.locator('.efaiw-skills-tip');
    const shown = await tip.isVisible();
    await shot(page, `${tag}-new`);
    await tip.getByRole('button', { name: t.tipOk }).click();
    await page.reload({ waitUntil: 'domcontentloaded' });
    await settle(page);
    const again = await page.locator('.efaiw-skills-tip').count();
    return [placeholder === t.placeholder && shown && again === 0, `placeholder=${placeholder} shown=${shown} again=${again}`];
  });

  await check(`CD-02 ${tag}`, '«+»: file, documents, ready command, skill, then the web-search line; no internet or skills switch', async () => {
    const menu = await openPlus(page);
    const ids = await menu
      .locator('[data-testid^="tools-menu-"]')
      .evaluateAll((items) => items.map((i) => i.getAttribute('data-testid')));
    const order = ['tools-menu-attach', 'tools-menu-documents', 'tools-menu-prompts', 'tools-menu-skills'];
    const inOrder = order.every((id, i) => ids.indexOf(id) === i);
    const note = await menu.getByTestId('tools-menu-web-note').innerText();
    const switches = await menu.locator('[role="menuitemcheckbox"]').evaluateAll((items) =>
      items.map((i) => i.getAttribute('data-testid')),
    );
    const noOldSwitch = !switches.includes('tools-menu-internet') && !ids.includes('tools-menu-internet');
    await shot(page, `${tag}-plus`);
    const a11y = await axe(page);
    await page.keyboard.press('Escape');
    return [
      inOrder && note.includes(t.webNote) && noOldSwitch && a11y[0],
      `ids=${ids} note=${note} switches=${switches} axe=${a11y[1]}`,
    ];
  });

  await check(`CD-03 ${tag}`, '«+» → «Skill»: the list opens with «How to use a skill», the brand skill first as «Automatic», manage and create', async () => {
    const menu = await openPlus(page);
    await menu.getByTestId('tools-menu-skills').click();
    const pop = page.locator('.efaiw-skills-popover');
    await pop.waitFor();
    await page.waitForTimeout(FADE_MS);
    await page.getByRole('button', { name: new RegExp(SKILL.displayTitle) }).waitFor();
    const howto = await pop.locator('.efaiw-skills-howto').innerText();
    const steps = await pop.locator('.efaiw-skills-howto li').count();
    const first = pop.locator('#skill-item-0');
    const firstBadge = await first.locator('.efaiw-skill-badge').count();
    const firstName = await first.locator('.efaiw-skill-row > span').innerText();
    const example = await pop
      .getByRole('button', { name: new RegExp(SKILL.displayTitle) })
      .locator('small')
      .innerText();
    const foot = await pop.locator('.efaiw-skills-foot button').count();
    await shot(page, `${tag}-skills`);
    const a11y = await axe(page);
    return [
      howto.includes(t.howto) && steps === 3 && firstBadge === 1 && firstName === t.brandSkill &&
        example === SKILL.description && foot === 2 && a11y[0],
      `steps=${steps} badge=${firstBadge} first=${firstName} example=${example} foot=${foot} axe=${a11y[1]}`,
    ];
  });

  await check(`CD-04 ${tag}`, 'picking a skill: a «$» chip on the box and the hint asks for the request', async () => {
    await page.getByRole('button', { name: new RegExp(SKILL.displayTitle) }).click();
    const chip = page.locator('form .efaiw-skill-chip');
    await chip.waitFor({ timeout: 15000 });
    await page.waitForFunction(
      () => !document.querySelector('form [role="progressbar"], form .animate-spin'),
      null,
      { timeout: 15000 },
    ).catch(() => {});
    await page.waitForTimeout(1200);
    const name = await chip.locator('.efaiw-skill-chip-name').innerText();
    const placeholder = await box(page).getAttribute('placeholder');
    await shot(page, `${tag}-skill-picked`);
    return [name === SKILL.displayTitle && placeholder === t.skillPlaceholder, `name=${name} placeholder=${placeholder}`];
  });

  await check(`CD-05 ${tag}`, 'the skill reaches the model as text, with no tools and search on; the sent message shows the chip', async () => {
    const before = mockRequests().length;
    await send(page, 'حوّل ملاحظات الاجتماع إلى محضر SYNTH-DESIGN-SHORT');
    const requests = mockRequests().slice(before);
    const hit = requests.find((r) => (r.markers || []).includes('SYNTH-SKILL-MINUTES'));
    const userChip = await page.locator('.user-turn .efaiw-skill-chip').count();
    return [
      hit != null && hit.tools === 0 && hit.enableSearch === true && userChip >= 1,
      `requests=${requests.length} hit=${JSON.stringify(hit && { tools: hit.tools, toolNames: hit.toolNames, enableSearch: hit.enableSearch })} userChip=${userChip}`,
    ];
  });

  await check(`CD-06 ${tag}`, 'a short reply without the block: suggestions from the rules (explain, translate), no questions', async () => {
    const fu = lastReply(page).locator('.efaiw-followups');
    const questions = await fu.locator('.efaiw-fu-question').count();
    const actions = await fu.locator('.efaiw-fu-action').allInnerTexts();
    return [questions === 0 && actions.length === 2, `questions=${questions} actions=${actions}`];
  });

  await check(`CD-07 ${tag}`, 'a long reply: headings in primary blue, no summary card, the block hidden, two questions and the model\'s actions', async () => {
    await send(page, 'لخّص تقرير جودة الهواء SYNTH-DESIGN-LONG');
    const reply = lastReply(page);
    const heading = await reply.locator('.markdown h2').first().evaluate((el) => getComputedStyle(el).color);
    const body = await reply.locator('.markdown p').first().evaluate((el) => getComputedStyle(el).color);
    const quotes = await reply.locator('.markdown blockquote').count();
    const text = await reply.locator('.markdown').innerText();
    const blockShown = text.includes('efaiw-followups') || text.includes('"q"');
    const questions = await reply.locator('.efaiw-fu-question').allInnerTexts();
    const actions = await reply.locator('.efaiw-fu-action').allInnerTexts();
    await shot(page, `${tag}-long`);
    return [
      heading === 'rgb(44, 58, 130)' && body === 'rgb(15, 24, 34)' && quotes === 0 && !blockShown &&
        questions.length === 2 && actions.join('|') === `${t.letter}|${t.shorten}`,
      `heading=${heading} body=${body} quotes=${quotes} blockShown=${blockShown} q=${questions} a=${actions}`,
    ];
  });

  await check(`CD-08 ${tag}`, 'the toolbar: copy, download, regenerate, rating, «More», then the model; no name above the reply', async () => {
    const tools = lastTools(page);
    const copy = await tools.getByTestId('copy-response-button').count();
    const download = await tools.getByRole('button', { name: t.download, exact: true }).count();
    const regenerate = await tools.getByTestId('regenerate-generation-button').count();
    const more = await tools.getByTestId('reply-more-button').count();
    const model = await tools.locator('.efaiw-reply-model').innerText();
    const head = await lastReply(page).locator('> h2').boundingBox();
    const edit = await tools.locator('[id^="edit-"]').count();
    return [
      copy === 1 && download === 1 && regenerate === 1 && more === 1 && model === t.model && head.height <= 1 && edit === 0,
      `copy=${copy} download=${download} regen=${regenerate} more=${more} model=${model} head=${head.height} edit=${edit}`,
    ];
  });

  await check(`CD-09 ${tag}`, 'copy leaves the suggestions block out', async () => {
    await lastTools(page).getByTestId('copy-response-button').click();
    await page.waitForTimeout(300);
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    return [copied.includes('جودة الهواء') && !copied.includes('efaiw-followups'), copied.slice(-120)];
  });

  await check(`CD-10 ${tag}`, 'download: the title, the file name, and each format as a badge (Word, PDF, PowerPoint, Excel, Markdown)', async () => {
    await lastTools(page).getByRole('button', { name: t.download, exact: true }).click();
    const menu = page.locator('.efaiw-download-menu');
    await menu.waitFor();
    await page.waitForTimeout(FADE_MS);
    const head = await menu.locator('.efaiw-menu-head').innerText();
    const badges = await menu.locator('.efaiw-fmt').allInnerTexts();
    await shot(page, `${tag}-download`);
    const a11y = await axe(page);
    await page.keyboard.press('Escape');
    return [
      head.includes(t.downloadTitle) && badges.join(',') === 'DOCX,PDF,PPTX,XLSX,MD' && a11y[0],
      `head=${head} badges=${badges} axe=${a11y[1]}`,
    ];
  });

  await check(`CD-11 ${tag}`, '«More»: share first, then edit, fork and a retry with each other model', async () => {
    await lastTools(page).getByTestId('reply-more-button').click();
    const menu = page.locator('.efaiw-reply-more-menu');
    await menu.waitFor();
    await page.waitForTimeout(FADE_MS);
    const ids = await menu.locator('[id^="reply-more-"]').evaluateAll((items) => items.map((i) => i.id));
    const share = await menu.locator('#reply-more-share').count();
    const startsWithShare = share === 0 || ids[0] === 'reply-more-share';
    const redo = ids.filter((id) => id.startsWith('reply-more-redo-'));
    await shot(page, `${tag}-more`);
    const a11y = await axe(page);
    await page.keyboard.press('Escape');
    return [
      startsWithShare && ids.includes('reply-more-edit') && ids.includes('reply-more-fork') &&
        redo.join(',') === 'reply-more-redo-careful,reply-more-redo-deep' && a11y[0],
      `ids=${ids} axe=${a11y[1]}`,
    ];
  });

  await check(`CD-12 ${tag}`, 'a suggested question sends as it reads and gets a reply', async () => {
    const question = (await lastReply(page).locator('.efaiw-fu-question').first().innerText()).trim();
    const before = await page.locator('.agent-turn').count();
    await lastReply(page).locator('.efaiw-fu-question').first().click();
    await page.waitForFunction((n) => document.querySelectorAll('.agent-turn').length > n, before, {
      timeout: 30000,
    });
    await lastTools(page).getByTestId('copy-response-button').waitFor({ timeout: 30000 });
    const sent = (await page.locator('.user-turn').last().innerText()).trim();
    return [sent.includes(question), `question=${question} sent=${sent}`];
  });

  await check(`CD-13 ${tag}`, 'suggestions only under the latest reply', async () =>
    [(await page.locator('.efaiw-followups').count()) === 1, `${await page.locator('.efaiw-followups').count()}`],
  );

  await check(`CD-14 ${tag}`, 'a letter: the Word/PDF bar with the file name, and letter suggestions', async () => {
    await send(page, 'اكتب خطاباً للمدير SYNTH-DESIGN-LETTER');
    const bar = lastReply(page).locator('.efaiw-docbar');
    const name = await bar.locator('.efaiw-docbar-text > span').innerText();
    const pills = await bar.locator('.efaiw-docbar-pill').count();
    await shot(page, `${tag}-letter`);
    return [name.endsWith('.docx') && pills === 2, `name=${name} pills=${pills}`];
  });

  await check(`CD-15 ${tag}`, 'the model menu: Pro says it does not search the web for now', async () => {
    await page.getByTestId('model-selector-button').click();
    const note = await page.locator('[data-efaiw-speed="deep"] .efaiw-model-noweb').innerText();
    await page.keyboard.press('Escape');
    return [note === t.proNote, note];
  });

  await check(`CD-16 ${tag}`, 'the skill attachment is not listed on Documents', async () => {
    await page.goto(`${BASE}/files`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
    const listed = await page.getByText('.efaiw-skill.txt').count();
    return [listed === 0, `listed=${listed}`];
  });

  await check(`CD-17 ${tag}`, 'axe on the chat; no horizontal scroll; no page errors', async () => {
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await settle(page);
    const a11y = await axe(page);
    const scroll = await noHScroll(page);
    return [a11y[0] && scroll[0] && errors.length === 0, `${a11y[1]} ${scroll[1]} errors=${errors.join(' | ')}`];
  });

  await check(`CD-18 ${tag}`, 'a new chat: a skill and a file added on «بصير لايت» stay when the model changes and reach «بصير بلس» (#241)', async () => {
    await page.goto(`${BASE}/c/new`, { waitUntil: 'domcontentloaded' });
    await settle(page);
    const modelButton = page.getByTestId('model-selector-button');
    const before = (await modelButton.innerText()).trim();
    await box(page).click();
    await page.keyboard.type('$');
    await page.locator('.efaiw-skills-popover').waitFor();
    await page.getByRole('button', { name: new RegExp(SKILL.displayTitle) }).click();
    await page.locator('form .efaiw-skill-chip').waitFor({ timeout: 15000 });
    await page.locator('form input[type="file"]').first().setInputFiles(SWITCH_FILE);
    const fileChip = page.locator('form').getByText(/synthetic-switch/);
    await fileChip.first().waitFor({ timeout: 15000 });
    await page.waitForFunction(
      () => !document.querySelector('form [role="progressbar"], form .animate-spin'),
      null,
      { timeout: 15000 },
    ).catch(() => {});
    await modelButton.click();
    await page.locator('[data-efaiw-speed="careful"]').first().click();
    await page.waitForTimeout(800);
    const after = (await modelButton.innerText()).trim();
    const chips = await page.locator('form .efaiw-skill-chip').count();
    const files = await fileChip.count();
    await shot(page, `${tag}-switch-kept`);
    const n = mockRequests().length;
    await send(page, 'حوّل الملف المرفق إلى محضر SYNTH-DESIGN-SHORT');
    const hit = mockRequests().slice(n).find((r) => (r.markers || []).includes('SYNTH-SKILL-MINUTES'));
    return [
      before.includes(t.model) && after.includes(t.plusModel) && chips === 1 && files >= 1 && hit != null &&
        hit.markers.includes('SYNTH-FILE-SWITCH') && hit.enableThinking === true && hit.tools === 0 &&
        errors.length === 0,
      `model=${before}→${after} chips=${chips} files=${files} hit=${JSON.stringify(hit && { markers: hit.markers, thinking: hit.enableThinking, tools: hit.tools })} errors=${errors.join(' | ')}`,
    ];
  });
  await endSession('employee', context);
}

/* ------------------------------------------------------------------------------------------------ desktop, English */
async function desktopEnglish(browser) {
  const tag = 'employee-en-1440';
  const t = TEXT.en;
  const { context, page, errors } = await newSession(browser, {
    role: 'employee',
    lang: 'en',
    viewport: { width: 1440, height: 900 },
    phone: false,
  });
  await check(`CD-20 ${tag}`, 'English: the box hint, an English reply with blue headings and its suggestions', async () => {
    const placeholder = await box(page).getAttribute('placeholder');
    await send(page, 'Summarize the air quality report SYNTH-DESIGN-EN');
    const reply = lastReply(page);
    const heading = await reply.locator('.markdown h2').first().evaluate((el) => getComputedStyle(el).color);
    const questions = await reply.locator('.efaiw-fu-question').count();
    const model = await lastTools(page).locator('.efaiw-reply-model').innerText();
    await shot(page, `${tag}-reply`);
    return [
      placeholder === t.placeholder && heading === 'rgb(44, 58, 130)' && questions === 1 && model === t.model,
      `placeholder=${placeholder} heading=${heading} q=${questions} model=${model}`,
    ];
  });

  await check(`CD-21 ${tag}`, 'axe; no horizontal scroll; no page errors', async () => {
    const a11y = await axe(page);
    const scroll = await noHScroll(page);
    return [a11y[0] && scroll[0] && errors.length === 0, `${a11y[1]} ${scroll[1]} errors=${errors.join(' | ')}`];
  });
  await endSession('employee', context);
}

/* ------------------------------------------------------------------------------------------------ phone, Arabic */
async function phoneArabic(browser) {
  const tag = 'employee-ar-390';
  const t = TEXT.ar;
  const { context, page, errors } = await newSession(browser, {
    role: 'employee',
    lang: 'ar',
    viewport: { width: 390, height: 844 },
    phone: true,
  });

  await check(`CD-30 ${tag}`, 'phone: the temporary chat is in the new chat\'s header and changes the hint', async () => {
    const toggle = page.locator('[data-efaiw="chat-header"] button[aria-pressed]:visible').first();
    await toggle.tap();
    await page.waitForTimeout(400);
    const placeholder = await box(page).getAttribute('placeholder');
    await shot(page, `${tag}-temporary`);
    await toggle.tap();
    await page.waitForTimeout(300);
    return [placeholder === t.temporaryPlaceholder, `placeholder=${placeholder}`];
  });

  await check(`CD-31 ${tag}`, 'phone: «+» is a bottom sheet across the screen', async () => {
    const menu = await openPlus(page);
    await page.waitForTimeout(300);
    const r = await menu.boundingBox();
    await shot(page, `${tag}-plus`);
    const a11y = await axe(page);
    await page.keyboard.press('Escape');
    const bottom = Math.abs(r.y + r.height - 844) <= 2;
    return [bottom && r.width >= 388 && a11y[0], `box=${JSON.stringify(r)} axe=${a11y[1]}`];
  });

  await check(`CD-35 ${tag}`, 'phone: «$» opens a short list right above the message box: two and a half rows, no steps, a slim foot (#241)', async () => {
    await box(page).tap();
    await page.keyboard.type('$');
    await page.locator('.efaiw-skills-popover').waitFor();
    await page.getByRole('button', { name: new RegExp(SKILL.displayTitle) }).waitFor();
    await page.waitForTimeout(FADE_MS);
    const g = await composerListGeometry(page, '.efaiw-skills-popover');
    await shot(page, `${tag}-skills`);
    const a11y = await axe(page);
    await page.keyboard.press('Escape');
    await box(page).fill('');
    return [
      g.above && g.list <= 141 && g.rows >= 4 && !g.howto && g.foot.length === 2 && g.foot.every((h) => h >= 44) &&
        g.width >= 360 && a11y[0],
      `${JSON.stringify(g)} axe=${a11y[1]}`,
    ];
  });

  await check(`CD-36 ${tag}`, 'phone with the keyboard open (390×500): the «$» list fits between the header and the box; «/» sits above the box too', async () => {
    await page.setViewportSize({ width: 390, height: 500 });
    await page.waitForTimeout(400);
    await box(page).tap();
    await page.keyboard.type('$');
    await page.locator('.efaiw-skills-popover').waitFor();
    await page.waitForTimeout(FADE_MS);
    const skills = await composerListGeometry(page, '.efaiw-skills-popover');
    await shot(page, `${tag}-skills-keyboard`);
    await page.keyboard.press('Escape');
    await box(page).fill('');
    await box(page).tap();
    await page.keyboard.type('/');
    await page.locator('form .popover').first().waitFor();
    await page.waitForTimeout(FADE_MS);
    const slash = await composerListGeometry(page, 'form .popover');
    await shot(page, `${tag}-commands-keyboard`);
    await page.keyboard.press('Escape');
    await box(page).fill('');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(400);
    return [
      skills.above && skills.top >= skills.headerBottom && skills.boxBottom <= skills.vh && slash.above,
      `skills=${JSON.stringify(skills)} slash=${JSON.stringify({ top: slash.top, bottom: slash.bottom, boxTop: slash.boxTop })}`,
    ];
  });

  await check(`CD-32 ${tag}`, 'phone: an older reply keeps its actions out of view until tapped; the latest shows them', async () => {
    await send(page, 'سؤال أول SYNTH-DESIGN-SHORT');
    await send(page, 'لخّص SYNTH-DESIGN-LONG');
    const older = page.locator('[data-efaiw-actions="older"]').last();
    const hidden = await older.evaluate((el) => getComputedStyle(el).visibility);
    const latest = await lastTools(page).evaluate((el) => getComputedStyle(el).visibility);
    await page.locator('.agent-turn').nth(-2).locator('[data-testid="message-body"]').tap({ position: { x: 40, y: 10 } });
    await page.waitForTimeout(300);
    const shown = await older.evaluate((el) => getComputedStyle(el).visibility);
    await shot(page, `${tag}-replies`);
    return [hidden === 'hidden' && latest === 'visible' && shown === 'visible', `older=${hidden}→${shown} latest=${latest}`];
  });

  await check(`CD-33 ${tag}`, 'phone: «More» is a bottom sheet', async () => {
    await lastTools(page).getByTestId('reply-more-button').tap();
    const menu = page.locator('.efaiw-reply-more-menu');
    await menu.waitFor();
    await page.waitForTimeout(300);
    const r = await menu.boundingBox();
    await shot(page, `${tag}-more`);
    await page.keyboard.press('Escape');
    return [Math.abs(r.y + r.height - 844) <= 2 && r.width >= 388, JSON.stringify(r)];
  });

  await check(`CD-34 ${tag}`, 'phone: axe; no horizontal scroll; no page errors', async () => {
    const a11y = await axe(page);
    const scroll = await noHScroll(page);
    return [a11y[0] && scroll[0] && errors.length === 0, `${a11y[1]} ${scroll[1]} errors=${errors.join(' | ')}`];
  });
  await endSession('employee', context);
}

(async () => {
  const token = await apiLogin('employee');
  for (const skill of [SKILL, ...MORE_SKILLS]) {
    await createSkill(token, skill);
  }
  const browser = await chromium.launch();
  try {
    await desktopArabic(browser);
    await desktopEnglish(browser);
    await phoneArabic(browser);
  } finally {
    await browser.close();
  }
  console.log(`\n${passed} passed, ${failed} failed; screenshots in ${SHOTS}`);
  process.exit(failed === 0 ? 0 : 1);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
