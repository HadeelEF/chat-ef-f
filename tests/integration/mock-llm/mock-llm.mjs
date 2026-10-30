// Deterministic OpenAI-compatible mock LLM for the synthetic chat regression test (#38). Test-only: never deploy it.
// Runs with the Node.js runtime of the pinned LibreChat image (no extra image, no npm packages) on the internal
// `backend` network of the test stack, so it has no route to or from the internet.
//
//   GET  /health                  -> 200 "OK"
//   GET  /v1/models               -> the three model ids below
//   POST /v1/chat/completions     -> deterministic reply, streamed (SSE) or not, per model:
//        baseer-mock-echo   reply derived only from the request (same request -> same reply)
//        baseer-mock-slow   same reply padded to many slow chunks (for cancellation tests)
//        baseer-mock-error  HTTP 400 with an OpenAI-style error body (non-retryable: the client fails fast)
//        baseer-mock-5xx    HTTP 503 (retryable); the body names a fake internal host that must never reach the user
//        baseer-mock-429    HTTP 429 without Retry-After (rate limit: not retried by the client)
//        baseer-mock-401    HTTP 401 (provider rejects the key: not retried)
//        baseer-mock-gone   HTTP 404 model_not_found (listed in LibreChat, unknown to the provider)
//        baseer-mock-hang   accepts the request and never answers (client timeout path)
//        baseer-mock-stall  streams the first words of the reply, then sends nothing more (stream idle timeout, #39)
//        baseer-mock-markdown  fixed bilingual Markdown (heading, list, URL, code block, table) for RTL/bidi checks (#44)
//        qwen*, deepseek*   any Qwen or DeepSeek model id (the employee lineup, #37, #131): same as baseer-mock-echo;
//                           when the request carries `enable_thinking: true` the stream first sends THINKING as
//                           `reasoning_content`, also before a tool call
//   Scenarios on any model (#129), checked before the reply above:
//        ask_user_question  offered, and the last user message contains ASK_BATCH or ASK_ONE: the reply is a call of
//                           that tool (ASK_BATCH_ARGS / ASK_ONE_ARGS); the next request carries its result (role
//                           `tool`), answered by ANSWERED (+ the result) or SKIPPED when the user declined
//        summarization      a message contains SUMMARY_PROMPT_MARK (the Arabic summary prompts of librechat.yaml):
//                           the reply is SUMMARY
//        chat design #224   the last user message contains a key of DESIGN_REPLIES (SYNTH-DESIGN-*): the reply is that
//                           fixed text (a long reply with headings and a table ending with the suggestions block, a
//                           letter, an English reply, a short answer without the block) for tests/ui/chat_design.cjs,
//                           and three decks (SYNTH-DESIGN-DECK-*) for tests/ui/pptx_backgrounds.cjs
//
// Every request must carry `Authorization: Bearer $MOCK_LLM_API_KEY` (401 otherwise), proving that LibreChat sends the
// configured key. One JSON line per request goes to stdout (model, stream flag, message counts, a digest of each
// message, the number and names of the tools offered, the `enable_thinking`, `reasoning_effort` and output-limit
// values, how many assistant messages carry `reasoning_content` back, and the synthetic SYNTH-* markers found in the
// messages), never the key or the message text, so the test can inspect what LibreChat sent without logging content.
import { createHash, timingSafeEqual } from 'node:crypto';
import { createServer } from 'node:http';

const port = Number(process.env.MOCK_LLM_PORT ?? 8080);
const apiKey = process.env.MOCK_LLM_API_KEY ?? '';
const chunkDelayMs = Number(process.env.MOCK_LLM_CHUNK_DELAY_MS ?? 15);
const MODELS = ['baseer-mock-echo', 'baseer-mock-slow', 'baseer-mock-error', 'baseer-mock-5xx', 'baseer-mock-429',
  'baseer-mock-401', 'baseer-mock-gone', 'baseer-mock-hang', 'baseer-mock-stall', 'baseer-mock-markdown'];
// Lineup models (tests/integration/mock_chat.py routes the real Qwen Cloud endpoints of librechat.yaml to this mock).
const isLineupModel = (model) => typeof model === 'string' && /^(?:qwen|deepseek)[0-9a-z.-]*$/.test(model);
/** Fixed reasoning text streamed before the reply when thinking is requested; mock_chat.py checks it (THINKING). */
export const THINKING = 'تفكير اصطناعي ثابت. Synthetic reasoning.';
// Synthetic marker in failure bodies: the test asserts it never appears in what LibreChat stores or streams to users.
const CANARY = 'internal-gateway.corp.invalid';

if (apiKey.length < 16) {
  console.error('MOCK_LLM_API_KEY must be set (>= 16 characters)');
  process.exit(1);
}

const sha8 = (text) => createHash('sha256').update(text, 'utf8').digest('hex').slice(0, 8);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Plain text of an OpenAI message `content` (string or array of parts). */
function textOf(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content.map((part) => (typeof part === 'string' ? part : part?.text ?? '')).join('');
  }
  return '';
}

/** Fixed mixed Arabic/English Markdown (#44); tests/integration/mock_chat.py holds the same text (MARKDOWN). */
export const MARKDOWN = [
  '## ملخص اصطناعي — Synthetic summary',
  '',
  'هذا رد **ثابت** يجمع العربية و English في فقرة واحدة، مع التاريخ 2026-10-19 والنموذج `baseer-mock-markdown`.',
  '',
  '- البند الأول: الإعداد في `librechat.yaml` (version 1.3.17).',
  '- Second item: an English line inside an Arabic list.',
  '- الرابط: https://example.invalid/docs?lang=ar',
  '',
  '```python',
  'def greet(name: str) -> str:',
  '    return f"مرحباً {name}"  # تعليق عربي داخل الكود',
  '```',
  '',
  '| الحقل | Value |',
  '|---|---|',
  '| الحالة | Tested |',
].join('\n');

// Clarifying questions (#129). tests/integration/mockchat/checks_batch2.py holds the same triggers and texts.
export const ASK_BATCH = 'اكتب لي خطاباً';
export const ASK_ONE = 'رتّب لي اجتماعاً';
export const ASK_BATCH_ARGS = { questions: [
  { id: 'recipient', header: 'الجهة', question: 'لمن الخطاب؟', options: [
    { label: 'جهة حكومية', value: 'جهة حكومية' }, { label: 'موظف داخلي', value: 'موظف داخلي' },
    { label: 'مورّد', value: 'مورّد' }] },
  { id: 'tone', header: 'النبرة', question: 'ما نبرة الخطاب؟', options: [
    { label: 'رسمية', value: 'رسمية' }, { label: 'ودّية', value: 'ودّية' }] },
] };
export const ASK_ONE_ARGS = { questions: [
  { id: 'topics', header: 'المحاور', question: 'ما محاور الاجتماع؟', description: 'اختر محوراً أو أكثر.',
    multiSelect: true, options: [{ label: 'الميزانية', value: 'الميزانية' },
      { label: 'الجدول الزمني', value: 'الجدول الزمني' }, { label: 'المخاطر', value: 'المخاطر' }] },
] };
export const ANSWERED = 'شكراً، وصلتني إجابتك:';
export const SKIPPED = 'تخطّيت السؤال، فسأكمل بافتراض عام: خطاب رسمي إلى جهة حكومية.';
// Long-chat summaries (#129): a fragment of both Arabic prompts of librechat.yaml `summarization`.
export const SUMMARY_PROMPT_MARK = 'يحلّ محل';
export const SUMMARY = 'الهدف:\nملخص اصطناعي ثابت للمحادثة السابقة. SYNTH-SUMMARY';
const DECLINED = 'The user chose not to answer this question.'; // LibreChat's Skip answer (client/src/utils/approval.ts)

// Chat design (#224): fixed replies in the shapes librechat.yaml asks for; tests/ui/chat_design.cjs checks them.
const FOLLOW_UPS = (q, a) => `\n\n\`\`\`efaiw-followups\n${JSON.stringify({ q, a })}\n\`\`\``;
export const DESIGN_REPLIES = {
  'SYNTH-DESIGN-LONG': [
    'تحسّنت جودة الهواء 6٪ في الربع الثالث، والجسيمات الدقيقة ما زالت فوق الحد في موقعين.',
    '',
    '## التفاصيل',
    '- تحسّن المؤشر العام لجودة الهواء 6٪ عن الربع الثاني.',
    '- انخفض ثاني أكسيد النيتروجين في المناطق الصناعية.',
    '- بقيت الجسيمات الدقيقة فوق الحد في موقعين من سبعة.',
    '',
    '## المؤشرات',
    '| المؤشر (ميكروغرام/م³) | الربع 2 | الربع 3 |',
    '|---|---|---|',
    '| PM2.5 | 38 | 35 |',
    '| NO₂ | 41 | 36 |',
    '| O₃ | 52 | 50 |',
  ].join('\n') + FOLLOW_UPS(['ما أسباب ارتفاع الجسيمات في الموقعين؟', 'قارن بالربع الثالث من العام الماضي'],
    ['letter', 'shorten']),
  'SYNTH-DESIGN-LETTER': [
    '**الموضوع:** ملخص تقرير جودة الهواء للربع الثالث',
    '',
    'سعادة مدير إدارة الرصد البيئي المحترم،',
    'السلام عليكم ورحمة الله وبركاته، وبعد:',
    '',
    'نرفع لسعادتكم ملخص تقرير جودة الهواء للربع الثالث، إذ تحسّن المؤشر العام 6٪ عن الربع الثاني.',
    '',
    'وتقبلوا خالص التحية والتقدير،',
  ].join('\n') + FOLLOW_UPS(['أضف فقرة عن خطة المعالجة', 'اجعل الخطاب أقصر'], ['email', 'proofread']),
  'SYNTH-DESIGN-EN': [
    'Air quality improved 6% in Q3; fine particles stay above the limit at two sites.',
    '',
    '## Details',
    '- The overall index improved 6% on Q2.',
    '- Nitrogen dioxide fell in industrial areas.',
    '- Fine particles stayed above the limit at two of seven sites.',
  ].join('\n') + FOLLOW_UPS(['What caused the particle levels at those sites?'], ['table']),
  'SYNTH-DESIGN-SHORT': 'نعم، يشمل التقرير محطتين في الرياض.',
  // Decks in the shape the brand skill asks for, for the PowerPoint backgrounds (tests/ui/pptx_backgrounds.cjs).
  'SYNTH-DESIGN-DECK-AR': [
    '# خطة اصطناعية لتشجير الأحياء السكنية',
    '',
    'عرض تجريبي ببيانات اصطناعية للمراجعة الداخلية',
    '',
    '## الهدف',
    '- زيادة الغطاء النباتي في ثلاثة أحياء تجريبية.',
    '- قياس أثر التشجير في حرارة الأسطح.',
    '- إشراك السكان في الري والمتابعة.',
    '',
    '## المؤشرات',
    '| المؤشر | الأساس | المستهدف |',
    '|---|---|---|',
    '| عدد الأشجار | 1,200 | 5,000 |',
    '| الغطاء النباتي | 4٪ | 9٪ |',
    '| متوسط حرارة الأسطح (°م) | 48 | 45 |',
    '',
    '## الخلاصة',
    '- البدء بالحي الأول في الربع القادم.',
    '- **مراجعة** النتائج بعد ستة أشهر.',
    '- رفع توصية بالتوسع إن تحقق المستهدف.',
  ].join('\n') + FOLLOW_UPS(['أضف شريحة عن الميزانية'], ['shorten']),
  'SYNTH-DESIGN-DECK-EN': [
    '# Synthetic urban greening plan',
    '',
    'A test deck with synthetic data for internal review',
    '',
    '## Goals',
    '- Raise tree cover in three pilot districts.',
    '- Measure the effect on surface temperatures.',
    '',
    '## Next steps',
    '- Start with the first district next quarter.',
    '- Review the results after six months.',
  ].join('\n'),
  // Live QA 2026-10-26 (tests/ui/reply_guards.cjs): replies the platform must guard against or read through.
  'SYNTH-DESIGN-TOOLCALL':
    '<tool_call>\n<web_search>\n{"query": "أخبار البيئة"}\n</parameter>\n</function>\n</tool_call>',
  'SYNTH-DESIGN-EMPTY': FOLLOW_UPS(['سؤال لا يظهر تحت رد فارغ'], ['explain']).trim(),
  'SYNTH-DESIGN-BR': [
    '| المشروع | الوصف |',
    '|---|---|',
    '| سدير | محطة شمسية<br>في منطقة الرياض |',
  ].join('\n'),
  // A letter in the shape seen live: a stray empty «efaiw-» block, no fence inside the artifact, the subject after the
  // letterhead, date and reference.
  'SYNTH-DESIGN-ARTLETTER': [
    '```efaiw-brand-guidelines',
    '```',
    '',
    ':::artifact{identifier="thanks-letter" type="text/markdown" title="خطاب شكر"}',
    '**صندوق البيئة**',
    '**إدارة الاتصال المؤسسي**',
    '',
    'التاريخ: [التاريخ]',
    'الرقم المرجعي: EF/ADM/[الرقم]',
    '',
    '---',
    '',
    '**سعادة/ مدير الإدارة المحترم**',
    '**الموضوع:** شكر فريق العمل',
    '',
    'نشكر فريق العمل على تنظيم اليوم التطوعي.',
    ':::',
    '',
    'الافتراضات: اسم الإدارة افتراضي.',
  ].join('\n') + FOLLOW_UPS(['اجعل الخطاب أقصر'], ['letter', 'email']),
  // Latin names in parentheses in Arabic table cells, as live (mobile bidi check).
  'SYNTH-DESIGN-LATIN': [
    '| الشجرة | احتياج الماء |',
    '| :--- | :--- |',
    '| **السدر** (Ziziphus spina-christi) | متوسط إلى منخفض |',
    '| **النيم** (Azadirachta indica)* | متوسط |',
  ].join('\n'),
  'SYNTH-DESIGN-DECK-LONG': [
    '# خطة اصطناعية لتشجير ثلاثة أحياء سكنية تجريبية وقياس أثرها في خفض حرارة الأسطح خلال عامين',
    '',
    '## النطاق',
    '- ثلاثة أحياء تجريبية.',
    '',
    '## 3. الخطوات التالية',
    '- اعتماد الخطة.',
  ].join('\n'),
};

/** Synthetic markers (SYNTH-*) found anywhere in the messages: proves e.g. that a file's text reached the model. */
function markersIn(messages) {
  const text = messages.map((m) => textOf(m?.content)).join('\n');
  return [...new Set(text.match(/SYNTH-[A-Z0-9-]+/g) ?? [])].sort();
}

/** A tool call to stream instead of a text reply, or null. */
function toolCallFor(messages, tools) {
  const offered = Array.isArray(tools) && tools.some((t) => (t?.function?.name ?? t?.name) === 'ask_user_question');
  const last = messages.at(-1);
  if (!offered || last?.role !== 'user') return null;
  const text = textOf(last.content);
  const args = text.includes(ASK_BATCH) ? ASK_BATCH_ARGS : text.includes(ASK_ONE) ? ASK_ONE_ARGS : null;
  return args && { id: `call_${sha8(text)}`, name: 'ask_user_question', arguments: JSON.stringify(args) };
}

/** The deterministic reply. tests/integration/mock_chat.py computes the same string to check it exactly. */
export function replyFor(messages, model) {
  const final = messages.at(-1);
  if (final?.role === 'tool') {
    const result = textOf(final.content);
    return result.includes(DECLINED) ? SKIPPED : `${ANSWERED} ${result}`;
  }
  if (messages.some((m) => textOf(m?.content).includes(SUMMARY_PROMPT_MARK))) return SUMMARY;
  if (model === 'baseer-mock-markdown') return MARKDOWN;
  const userTexts = messages.filter((m) => m?.role === 'user').map((m) => textOf(m.content));
  const last = userTexts.at(-1) ?? '';
  const design = Object.keys(DESIGN_REPLIES).find((key) => last.includes(key));
  if (design) return DESIGN_REPLIES[design];
  const id = sha8(last);
  const turn = userTexts.length;
  if (/[؀-ۿ]/.test(last)) {
    return `رد اختباري ثابت من النموذج الوهمي. الدور ${turn}. المعرّف ${id}.`;
  }
  return `Deterministic mock reply. Turn ${turn}. ID ${id}.`;
}

function authorized(req) {
  const given = Buffer.from(String(req.headers.authorization ?? ''));
  const expected = Buffer.from(`Bearer ${apiKey}`);
  return given.length === expected.length && timingSafeEqual(given, expected);
}

function sendJson(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}

async function chatCompletions(req, res) {
  let body;
  try {
    body = JSON.parse(await readBody(req));
  } catch {
    return sendJson(res, 400, { error: { message: 'invalid JSON', type: 'invalid_request_error' } });
  }
  const model = body.model;
  const messages = Array.isArray(body.messages) ? body.messages : [];
  console.log(JSON.stringify({
    event: 'chat.completions',
    model,
    stream: body.stream === true,
    messages: messages.length,
    userTurns: messages.filter((m) => m?.role === 'user').length,
    digests: messages.map((m) => `${m?.role}:${sha8(textOf(m?.content))}`),
    tools: Array.isArray(body.tools) ? body.tools.length : 0,
    toolNames: Array.isArray(body.tools) ? body.tools.map((t) => t?.function?.name ?? t?.name ?? '?') : [],
    enableThinking: body.enable_thinking ?? null,
    reasoningEffort: body.reasoning_effort ?? null,
    enableSearch: body.enable_search ?? null,
    searchStrategy: body.search_options?.search_strategy ?? null,
    maxTokens: body.max_tokens ?? body.max_completion_tokens ?? null,
    replayedReasoning: messages.filter((m) => m?.role === 'assistant' && typeof m.reasoning_content === 'string'
      && m.reasoning_content !== '').length,
    markers: markersIn(messages),
    // #135: how each system message starts (the specs' instructions come first) and whether artifact instructions
    // (the `:::artifact` format) reach the model. #167: whether they are LibreChat's own English ones (`default` mode)
    // rather than only the specs' Arabic ones (`custom` mode).
    systemHeads: messages.filter((m) => m?.role === 'system').map((m) => sha8(textOf(m.content).slice(0, 64))),
    artifactPrompt: messages.some((m) => m?.role === 'system' && textOf(m.content).includes(':::artifact')),
    upstreamArtifactPrompt: messages.some((m) => m?.role === 'system'
      && textOf(m.content).includes('The assistant can create and reference artifacts')),
    // #138: digests of every line of the system messages, so a check can tell which variant of the instructions
    // (with or without internet search) a chat received.
    systemLines: [...new Set(messages.filter((m) => m?.role === 'system')
      .flatMap((m) => textOf(m.content).split('\n').map((line) => line.trim()).filter(Boolean).map(sha8)))],
    // #146: digests of every line of every message, whatever its role, so a check can tell whether a Skill's text
    // (primed as a message of its own or added to the instructions) reached the model.
    allLines: [...new Set(messages
      .flatMap((m) => textOf(m?.content).split('\n').map((line) => line.trim()).filter(Boolean).map(sha8)))],
  }));
  // As Qwen Cloud documents for its web search (#135): only streamed calls may search.
  if (body.enable_search === true && body.stream !== true) {
    return sendJson(res, 400, { error: { message: 'Non-streaming mode does not support Web Search', type: 'invalid_request_error' } });
  }
  if ((!MODELS.includes(model) && !isLineupModel(model)) || model === 'baseer-mock-gone') {
    return sendJson(res, 404, { error: { message: `model ${model} not found`, type: 'invalid_request_error',
      code: 'model_not_found' } });
  }
  if (model === 'baseer-mock-error') {
    return sendJson(res, 400, { error: { message: 'synthetic provider rejection (mock)', type: 'invalid_request_error' } });
  }
  if (model === 'baseer-mock-5xx') {
    return sendJson(res, 503, { error: { message: `upstream overloaded at ${CANARY}:8443 (synthetic)`, type: 'server_error' } });
  }
  if (model === 'baseer-mock-429') {
    return sendJson(res, 429, { error: { message: `rate limit reached on ${CANARY} (synthetic)`, type: 'requests',
      code: 'rate_limit_exceeded' } });
  }
  if (model === 'baseer-mock-401') {
    return sendJson(res, 401, { error: { message: `key rejected by ${CANARY} (synthetic)`, type: 'invalid_request_error',
      code: 'invalid_api_key' } });
  }
  if (model === 'baseer-mock-hang') {
    return; // never answer; the socket closes when LibreChat's per-attempt timeout aborts the request
  }

  const call = toolCallFor(messages, body.tools);
  const reply = call ? '' : replyFor(messages, model);
  const id = `chatcmpl-mock-${sha8(JSON.stringify(messages))}`;
  const created = 1700000000; // fixed: responses are byte-for-byte reproducible
  if (body.stream !== true) {
    const message = call
      ? { role: 'assistant', content: null, tool_calls: [{ id: call.id, type: 'function',
        function: { name: call.name, arguments: call.arguments } }] }
      : { role: 'assistant', content: reply };
    return sendJson(res, 200, {
      id, object: 'chat.completion', created, model,
      choices: [{ index: 0, message, finish_reason: call ? 'tool_calls' : 'stop' }],
      usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
    });
  }

  const slow = model === 'baseer-mock-slow';
  const pieces = reply.split(/(?<= )/); // keep the spaces, so the concatenation equals `reply`
  if (slow) pieces.push(...Array.from({ length: 200 }, (_, i) => ` …${i}`));
  const delay = slow ? 150 : chunkDelayMs;
  let closed = false;
  res.on('close', () => { closed = true; });
  res.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
  const frame = (delta, finish = null) =>
    `data: ${JSON.stringify({ id, object: 'chat.completion.chunk', created, model,
      choices: [{ index: 0, delta, finish_reason: finish }] })}\n\n`;
  // Like Qwen Cloud (seen live, #211): a streamed reply ends with a usage chunk; LibreChat records it in `transactions`.
  const usage = () => `data: ${JSON.stringify({ id, object: 'chat.completion.chunk', created, model, choices: [],
    usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } })}\n\n`;
  res.write(frame({ role: 'assistant', content: '' }));
  if (body.enable_thinking === true) {
    for (const piece of THINKING.split(/(?<= )/)) {
      res.write(frame({ reasoning_content: piece }));
      await sleep(delay);
    }
  }
  if (call) {
    res.write(frame({ tool_calls: [{ index: 0, id: call.id, type: 'function',
      function: { name: call.name, arguments: '' } }] }));
    for (const piece of call.arguments.match(/[\s\S]{1,40}/g)) {
      res.write(frame({ tool_calls: [{ index: 0, function: { arguments: piece } }] }));
      await sleep(delay);
    }
    res.write(frame({}, 'tool_calls'));
    res.write(usage());
    return res.end('data: [DONE]\n\n');
  }
  if (model === 'baseer-mock-stall') {
    res.write(frame({ content: pieces[0] }));
    // nothing more; the socket closes when LibreChat's stream idle timeout aborts the request
    return res.on('close', () => console.log(JSON.stringify({ event: 'client.disconnected', model })));
  }
  for (const piece of pieces) {
    if (closed) {
      console.log(JSON.stringify({ event: 'client.disconnected', model }));
      return;
    }
    res.write(frame({ content: piece }));
    await sleep(delay);
  }
  res.write(frame({}, 'stop'));
  res.write(usage());
  res.end('data: [DONE]\n\n');
}

const server = createServer((req, res) => {
  const url = new URL(req.url ?? '/', 'http://mock');
  if (req.method === 'GET' && url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    return res.end('OK');
  }
  if (!authorized(req)) {
    console.log(JSON.stringify({ event: 'unauthorized', path: url.pathname }));
    return sendJson(res, 401, { error: { message: 'invalid API key', type: 'invalid_request_error' } });
  }
  if (req.method === 'GET' && url.pathname === '/v1/models') {
    return sendJson(res, 200, { object: 'list', data: MODELS.map((id) => ({ id, object: 'model', owned_by: 'mock' })) });
  }
  if (req.method === 'POST' && url.pathname === '/v1/chat/completions') {
    return chatCompletions(req, res).catch((err) => {
      console.error(`mock error: ${err?.message}`);
      if (!res.headersSent) sendJson(res, 500, { error: { message: 'mock internal error', type: 'server_error' } });
    });
  }
  return sendJson(res, 404, { error: { message: 'not found', type: 'invalid_request_error' } });
});

server.listen(port, '0.0.0.0', () => console.log(JSON.stringify({ event: 'listening', port })));
