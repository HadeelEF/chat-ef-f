#!/usr/bin/env node
/*
 * The PowerPoint download with the guide's backgrounds: three decks from the deterministic mock model
 * (SYNTH-DESIGN-DECK-*, tests/integration/mock-llm) are downloaded from a reply's «Download» menu as an employee would,
 * then read back: EF-BG-09 behind the title slide with the title on its calm side, EF-BG-07 behind a last
 * «الخلاصة» / «Next steps» slide in white text, content slides white, the files the same bytes the platform serves,
 * the font and logo still embedded, and nothing of the hidden suggestions block in the deck.
 *
 *   node tests/ui/pptx_backgrounds.cjs <state.json from tests/ui/ui_stack.py> [output-dir]
 *
 * Needs Node.js, unzip and Playwright with Chromium (require('playwright')). Keeps the decks in output-dir (to open or
 * render them). Prints PASS/FAIL per check (IDs in docs/quality/concept1-interface-test-cases.md §13) and exits 1 on
 * any failure.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const [stateFile, outArg] = process.argv.slice(2);
if (!stateFile) {
  console.error('usage: node tests/ui/pptx_backgrounds.cjs <state.json> [output-dir]');
  process.exit(2);
}
const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
const BASE = state.base;
const OUT = outArg || fs.mkdtempSync(path.join(os.tmpdir(), 'efaiw-pptx-'));
fs.mkdirSync(OUT, { recursive: true });

const TITLE_BG = '/assets/ef-ppt-bg-09-navy-radial-left.jpg';
const CLOSING_BG = '/assets/ef-ppt-bg-07-navy-radial-bottom-left.jpg';
/** efaiwPptx.ts: the calm side of the title background starts at 45% of the 16:9 slide; the margin is 0.65 in. */
const CALM_X = String(Math.round(12192000 * 0.45));

let passed = 0;
let failed = 0;
async function check(id, label, fn) {
  try {
    const [ok, detail] = await fn();
    if (ok) {
      passed += 1;
      console.log(`PASS  ${id}  ${label}`);
    } else {
      failed += 1;
      console.log(`FAIL  ${id}  ${label} :: ${String(detail || '').slice(0, 400)}`);
    }
  } catch (err) {
    failed += 1;
    console.log(`FAIL  ${id}  ${label} :: ${err.name}: ${err.message.split('\n')[0]}`);
  }
}

const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const part = (file, name) => execFileSync('unzip', ['-p', file, name], { maxBuffer: 64 * 1024 * 1024 });
const text = (file, name) => part(file, name).toString('utf8');
const names = (file) =>
  execFileSync('unzip', ['-Z1', file], { encoding: 'utf8' }).split('\n').filter(Boolean);
const titleX = (xml) => xml.match(/name="Title 1"[\s\S]*?<a:off x="(\d+)"/)?.[1];

async function served(asset) {
  const res = await fetch(`${BASE}${asset}`);
  return { status: res.status, type: res.headers.get('content-type'), sha: sha(Buffer.from(await res.arrayBuffer())) };
}

/** Sends the prompt, waits for the reply, and downloads it as PowerPoint from the reply's «Download» menu. */
async function deckFrom(page, prompt, file) {
  const before = await page.locator('.agent-turn').count();
  await page.getByTestId('text-input').fill(prompt);
  await page.getByTestId('send-button').click();
  await page.waitForFunction((n) => document.querySelectorAll('.agent-turn').length > n, before, { timeout: 30000 });
  const tools = page.locator('[data-efaiw-actions="last"]');
  await tools.locator('[data-testid="copy-response-button"]').waitFor({ timeout: 30000 });
  await page.waitForTimeout(400);
  await tools.getByRole('button', { name: 'تنزيل', exact: true }).click();
  await page.locator('.efaiw-download-menu').waitFor();
  await page.waitForTimeout(400);
  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 30000 }),
    page.getByTestId('download-pptx').click(),
  ]);
  const target = path.join(OUT, file);
  await download.saveAs(target);
  return target;
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'ar-SA', acceptDownloads: true });
  await context.addCookies([{ name: 'lang', value: 'ar', url: BASE }]);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  const account = state.accounts.employee;
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await page.locator('#email').fill(account.email);
  await page.locator('#password').fill(account.password);
  await page.getByTestId('login-button').click();
  await page.waitForURL((url) => url.pathname.startsWith('/c/'), { timeout: 30000 });
  await page.getByTestId('text-input').waitFor({ timeout: 30000 });

  const titleBg = await served(TITLE_BG);
  const closingBg = await served(CLOSING_BG);
  const ar = await deckFrom(page, 'اعمل عرضاً عن خطة التشجير SYNTH-DESIGN-DECK-AR', 'deck-ar.pptx');
  const en = await deckFrom(page, 'Make a deck on the greening plan SYNTH-DESIGN-DECK-EN', 'deck-en.pptx');
  const long = await deckFrom(page, 'اعمل عرضاً بعنوان طويل SYNTH-DESIGN-DECK-LONG', 'deck-long.pptx');

  await check('PB-01', 'the platform serves both backgrounds as JPEG', async () => [
    titleBg.status === 200 && closingBg.status === 200 && /image\/jpeg/.test(titleBg.type) && /image\/jpeg/.test(closingBg.type),
    JSON.stringify({ titleBg, closingBg }),
  ]);

  await check('PB-02', 'Arabic deck: EF-BG-09 behind the title slide, the title on its calm side, the logo and font kept', async () => {
    const slide = text(ar, 'ppt/slides/slide1.xml');
    const rels = text(ar, 'ppt/slides/_rels/slide1.xml.rels');
    const files = names(ar);
    const ok =
      slide.includes('<a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="rIdBg"/>') &&
      rels.includes('Target="../media/bg-title.jpg"') &&
      sha(part(ar, 'ppt/media/bg-title.jpg')) === titleBg.sha &&
      titleX(slide) === CALM_X &&
      slide.includes('<a:blip r:embed="rIdLogo"/>') &&
      files.includes('ppt/fonts/font1.fntdata') &&
      files.includes('ppt/fonts/font2.fntdata');
    return [ok, `x=${titleX(slide)} files=${files.filter((f) => /media|fonts/.test(f))}`];
  });

  await check('PB-03', 'Arabic deck: the last «الخلاصة» on EF-BG-07 in white with green bullets; content slides white', async () => {
    const files = names(ar).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f));
    const last = text(ar, `ppt/slides/slide${files.length}.xml`);
    const rels = text(ar, `ppt/slides/_rels/slide${files.length}.xml.rels`);
    const middle = files.slice(1, -1).map((f) => text(ar, f));
    const all = files.map((f) => text(ar, f)).join('');
    const ok =
      files.length === 4 &&
      last.includes('<a:t>الخلاصة</a:t>') &&
      rels.includes('Target="../media/bg-closing.jpg"') &&
      sha(part(ar, 'ppt/media/bg-closing.jpg')) === closingBg.sha &&
      last.includes('<a:buClr><a:srgbClr val="C0CB6C"/></a:buClr>') &&
      !last.includes('val="0F1822"') &&
      middle.every((xml) => !xml.includes('<p:bg>')) &&
      !all.includes('efaiw-followups');
    return [ok, `slides=${files.length} middleBg=${middle.map((xml) => xml.includes('<p:bg>'))}`];
  });

  await check('PB-04', 'English deck: the same background, not mirrored, the title left-aligned on the calm side; «Next steps» closes', async () => {
    const slide = text(en, 'ppt/slides/slide1.xml');
    const files = names(en).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f));
    const closing = text(en, `ppt/slides/_rels/slide${files.length}.xml.rels`);
    const ok =
      sha(part(en, 'ppt/media/bg-title.jpg')) === titleBg.sha &&
      titleX(slide) === CALM_X &&
      /name="Title 1"[\s\S]*?<a:pPr algn="l"\/>/.test(slide) &&
      closing.includes('Target="../media/bg-closing.jpg"');
    return [ok, `x=${titleX(slide)} slides=${files.length}`];
  });

  await check('PB-05', 'a long title steps down to 28 pt; a numbered «3. الخطوات التالية» closes', async () => {
    const slide = text(long, 'ppt/slides/slide1.xml');
    const files = names(long).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f));
    const closing = text(long, `ppt/slides/_rels/slide${files.length}.xml.rels`);
    const ok = /name="Title 1"[\s\S]*?sz="2800"/.test(slide) && closing.includes('bg-closing.jpg');
    return [ok, `slides=${files.length}`];
  });

  await check('PB-06', 'no page errors', async () => [errors.length === 0, errors.join(' | ')]);

  await browser.close();
  console.log(`\n${passed} passed, ${failed} failed. Decks in ${OUT}`);
  process.exit(failed ? 1 : 0);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
