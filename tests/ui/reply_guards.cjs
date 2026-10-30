#!/usr/bin/env node
/*
 * Browser checks of the chat page fixes from the live QA on Railway dev (2026-10-26): a reply that is only a search call
 * written as text or only the hidden suggestions block (a notice, one automatic retry, then «أعد المحاولة»), «<br>» in
 * a table cell, a letter carried as an artifact (its Word/PDF bar, the document alone in the file, no «خطاب رسمي»
 * under it), the screen reader's announcement without the hidden block, and no 403 on the MCP server list for an
 * employee. From the retest (patch 0042): the letter opens with a letterhead and «سعادة/» after an empty
 * «```efaiw-brand-guidelines» block that is never shown, and Latin names in Arabic table cells on a phone. The replies
 * come from the deterministic mock model
 * (tests/integration/mock-llm, SYNTH-DESIGN-*); its request log shows what reached it.
 *
 *   node tests/ui/reply_guards.cjs <state.json from tests/ui/ui_stack.py> [output-dir]
 *
 * Needs Node.js, Docker (to read the mock model's log), unzip and Playwright with Chromium (require('playwright')).
 * Prints PASS/FAIL per check (IDs in docs/quality/concept1-interface-test-cases.md §15) and exits 1 on any failure.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const [stateFile, outArg] = process.argv.slice(2);
if (!stateFile) {
  console.error('usage: node tests/ui/reply_guards.cjs <state.json> [output-dir]');
  process.exit(2);
}
const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
const BASE = state.base;
const OUT = outArg || fs.mkdtempSync(path.join(os.tmpdir(), 'efaiw-guards-'));
fs.mkdirSync(OUT, { recursive: true });

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

/** The mock model's chat requests on the search spec (titles and memory go elsewhere), oldest first. */
function chatRequests(marker) {
  const out = execFileSync('docker', ['logs', `${state.project}-mock-llm-1`], {
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return out
    .split('\n')
    .filter((line) => line.startsWith('{'))
    .map((line) => JSON.parse(line))
    .filter((e) => e.event === 'chat.completions' && e.enableSearch === true && (e.markers || []).includes(marker));
}

const lastReply = (page) => page.locator('.agent-turn').last();

/** Sends a message and waits until the reply has finished (its toolbar or the empty-reply notice). */
async function send(page, text) {
  const before = await page.locator('.agent-turn').count();
  await page.getByTestId('text-input').fill(text);
  await page.getByTestId('send-button').click();
  await page.waitForFunction((n) => document.querySelectorAll('.agent-turn').length > n, before, { timeout: 30000 });
  await page.waitForFunction(
    () =>
      document.querySelector('[data-efaiw-actions="last"] [data-testid="copy-response-button"]') != null ||
      document.querySelector('.efaiw-empty-reply') != null,
    null,
    { timeout: 30000 },
  );
  // An empty reply is retried once by itself: let that retry finish too.
  await page.waitForTimeout(3500);
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'ar-SA', acceptDownloads: true });
  await context.addCookies([{ name: 'lang', value: 'ar', url: BASE }]);
  const page = await context.newPage();
  const errors = [];
  const forbidden = [];
  page.on('pageerror', (err) => errors.push(err.message));
  page.on('response', (res) => {
    if (res.url().includes('/api/mcp/servers') && res.status() === 403) {
      forbidden.push(res.url());
    }
  });
  const account = state.accounts.employee;
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await page.locator('#email').fill(account.email);
  await page.locator('#password').fill(account.password);
  await page.getByTestId('login-button').click();
  await page.waitForURL((url) => url.pathname.startsWith('/c/'), { timeout: 30000 });
  await page.getByTestId('text-input').waitFor({ timeout: 30000 });

  await check('RG-01', 'a reply that is only a written search call: hidden, a notice, one automatic retry, no suggestions', async () => {
    await send(page, 'ما أخبار البيئة؟ SYNTH-DESIGN-TOOLCALL');
    const reply = lastReply(page);
    const text = await reply.innerText();
    const notice = await page.locator('.efaiw-empty-reply').last().innerText();
    const requests = chatRequests('SYNTH-DESIGN-TOOLCALL').length;
    const suggestions = await page.locator('.efaiw-followups').count();
    await page.screenshot({ path: path.join(OUT, 'RG-01-toolcall.png') });
    return [
      !text.includes('tool_call') && !text.includes('web_search') && notice.includes('لم يصل رد') && requests === 2 && suggestions === 0,
      `requests=${requests} suggestions=${suggestions} notice=${notice} text=${text.slice(0, 200)}`,
    ];
  });

  await check('RG-02', 'a reply that is only the suggestions block: the notice, one automatic retry, then «أعد المحاولة» asks again', async () => {
    await send(page, 'اكتب مقالاً SYNTH-DESIGN-EMPTY');
    const after = chatRequests('SYNTH-DESIGN-EMPTY').length;
    await page.locator('.efaiw-empty-reply').last().getByRole('button', { name: 'أعد المحاولة' }).click();
    await page.waitForTimeout(3000);
    const again = chatRequests('SYNTH-DESIGN-EMPTY').length;
    const questions = await page.locator('.efaiw-followups').getByText('سؤال لا يظهر تحت رد فارغ').count();
    return [after === 2 && again === 3 && questions === 0, `after=${after} again=${again} questions=${questions}`];
  });

  await check('RG-03', '«<br>» in a table cell is a line break on the page and in Word', async () => {
    await send(page, 'اعرض الجدول SYNTH-DESIGN-BR');
    const cell = lastReply(page).locator('td', { hasText: 'محطة شمسية' });
    const html = await cell.innerHTML();
    await page.locator('[data-efaiw-actions="last"]').getByRole('button', { name: 'تنزيل', exact: true }).click();
    await page.locator('.efaiw-download-menu').waitFor();
    await page.waitForTimeout(400);
    const [download] = await Promise.all([page.waitForEvent('download'), page.getByTestId('download-docx').click()]);
    const file = path.join(OUT, 'RG-03-table.docx');
    await download.saveAs(file);
    const xml = execFileSync('unzip', ['-p', file, 'word/document.xml']).toString('utf8');
    return [
      /<br\s*\/?>/.test(html) && !html.includes('&lt;br') && xml.includes('<w:br/>') && !xml.includes('&lt;br'),
      `cell=${html.slice(0, 160)}`,
    ];
  });

  await check('RG-04', 'a letter with a letterhead as an artifact: its Word/PDF bar, no «efaiw-» block, the document alone in the file, no «خطاب رسمي» under it', async () => {
    await send(page, 'اكتب خطاب شكر SYNTH-DESIGN-ARTLETTER');
    const bar = page.locator('.efaiw-docbar').last();
    await bar.waitFor({ timeout: 10000 });
    const shown = await lastReply(page).innerText();
    const codeBlocks = await lastReply(page).locator('pre').count();
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      bar.locator('.efaiw-docbar-primary').click(),
    ]);
    const file = path.join(OUT, 'RG-04-letter.docx');
    await download.saveAs(file);
    const xml = execFileSync('unzip', ['-p', file, 'word/document.xml']).toString('utf8');
    const actions = await page.locator('.efaiw-followups .efaiw-fu-action').allInnerTexts();
    return [
      !shown.includes('efaiw') &&
        codeBlocks === 0 &&
        xml.includes('سعادة') &&
        xml.includes('شكر فريق العمل') &&
        !xml.includes('الافتراضات') &&
        !actions.some((a) => a.includes('خطاب')),
      `codeBlocks=${codeBlocks} efaiwShown=${shown.includes('efaiw')} actions=${actions} hasAssumptions=${xml.includes('الافتراضات')}`,
    ];
  });

  await check('RG-07', 'the screen reader hears the reply without the hidden suggestions block', async () => {
    const announced = await page.evaluate(() =>
      [...document.querySelectorAll('#root > .sr-only')].map((n) => n.textContent || '').join(' '),
    );
    return [!announced.includes('efaiw-followups') && announced.includes('الافتراضات'), announced.slice(0, 200)];
  });

  await check('RG-08', 'on a phone, Latin names in Arabic table cells keep their order and the page does not scroll sideways', async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await send(page, 'جدول أشجار SYNTH-DESIGN-LATIN');
    const cell = lastReply(page).locator('td', { hasText: 'Ziziphus' });
    const style = await cell.evaluate((td) => {
      const css = getComputedStyle(td);
      return { direction: css.direction, bidi: css.unicodeBidi };
    });
    const sideways = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    await page.screenshot({ path: path.join(OUT, 'RG-08-latin-mobile.png') });
    await page.setViewportSize({ width: 1440, height: 900 });
    return [
      style.direction === 'rtl' && style.bidi === 'plaintext' && !sideways,
      `direction=${style.direction} unicode-bidi=${style.bidi} sideways=${sideways}`,
    ];
  });

  await check('RG-05', 'no 403 on the MCP server list for an employee', async () => [forbidden.length === 0, forbidden.join(' ')]);
  await check('RG-06', 'no page errors', async () => [errors.length === 0, errors.join(' | ')]);

  await browser.close();
  console.log(`\n${passed} passed, ${failed} failed. Files in ${OUT}`);
  process.exit(failed ? 1 : 0);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
