# Changelog

All notable changes to this repository are recorded here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/) (see `project/ROADMAP.md` §5).

## [Unreleased]

### Changed — Self-registration closed (ADR-0024, #245)

- **Why:** the owner asked to stop registration. There were no usage limits, so any new account could spend the
  Qwen Cloud credit.
- `ALLOW_REGISTRATION=false` in `librechat.env` and `.railway/railway.ts`, applied on Railway `dev`. The sign-up link
  is gone and `/api/auth/register` answers 403. Accounts are created by the administrator; existing ones keep signing in.
- ADR-0024 supersedes ADR-0020; the checks (N12, N14, T13/T14, R16/R17, M06) expect registration off.

### Fixed — The chat stretched to the full screen width in a desktop browser (#243)

- **Why:** the owner saw the chat at the full width of a desktop screen: one long line per reply, a screen-wide message
  box, and the model name far from the reply.
- **Cause:** LibreChat's «تكبير مساحة الدردشة» setting, saved in that browser, removed the 48rem reading width.
- **Fix:** the setting is gone and a saved value is ignored, so every screen keeps the centred column. ChatGPT (about
  48rem) and Claude also keep a centred column with no full-width option.
- Patch 0044; `client/src/store/__tests__/maximizeChatSpace.spec.ts`.

### Fixed — A picked skill was dropped when the model changed; the phone's «$» list covered the screen (#241)

- **Why:** the owner found that skills seemed to work only with «بصير لايت», and that on the phone the `$` list
  covered the screen.
- **Skills and files:** in a new chat, a skill or file added before changing the model was silently dropped. Upstream
  starts a fresh message box on a model switch. Since a new chat opens on «بصير لايت», a skill picked first never
  reached «بصير بلس» or «بصير برو». The box now keeps its attachments, as it already kept the typed text.
- **Phone:**
  - The `$` list sits right above the message box, as in ChatGPT, Claude and Gemini, instead of a sheet over it.
  - It shows two and a half rows, drops the three steps, and has «إدارة المهارات» and «أنشئ مهارة» in one slim row.
  - The `/` and `@` lists sit above the box too.
  - The one-time skills tip goes once the skills list is opened.
- Patch 0043 and `brand.css`; `tests/ui/chat_design.cjs` CD-18, CD-35, CD-36.

### Fixed — Chat page issues left after the live retest of the fixes below (2026-10-26, #41)

- **Why:** the retest on Railway dev after those fixes passed most checks and found four items still open.
- **Replies:**
  - A stray block in the platform's own `efaiw-` namespace, such as an empty `efaiw-brand-guidelines` block, is never shown.
  - With search on, the model no longer names its training cutoff or says it has no internet access.
- **Documents:**
  - A letter that opens with a letterhead, date and reference number, or with «سعادة/», gets its Word/PDF bar.
  - Slide titles drop the «الشريحة 1 —» / «Slide 2:» numbering the model adds.
- Patch 0042 and `librechat.yaml`; `tests/ui/reply_guards.cjs` 8/8.

### Added — the web client behaves like a phone app (#238, owner decision 2026-10-26)

- **Why:** the owner installed «بصير» on an iPhone 13 Pro Max and asked for it to feel like a phone app. An audit of
  the installed app found six gaps; the owner approved fixing all six.
- Sign-in fields at 16 px on touch screens, so iPhone stops zooming; the e-mail field gets the e-mail keyboard, with no
  capital first letter or autocorrect.
- 44 px touch targets for the header, the reply toolbar, the password eye, «سجّل الآن» and the drawer controls; on a
  360 px phone the model name moves under the reply buttons.
- No text selection or long-press menu on interface chrome; message text and fields stay selectable.
- `viewport-fit=cover`, so the layout keeps clear of iPhone's home indicator and, in landscape, the notch.
- «تثبيت التطبيق» in the account menu: the browser's dialog on Android, a hint on iPhone. The iPhone hint shows once, on
  its own, before the skills tip; neither appears inside the installed app.
- After a deploy, an open app shows «نسخة جديدة من بصير متاحة — تحديث» instead of staying on the old version.
- Patch 0041, `brand.css`, `ar.json`; `tests/ui/mobile_app.cjs` 17/17, with no regression in the other UI suites.

### Fixed — Chat page issues found in the live QA on Railway dev (2026-10-26, desktop and mobile, #41)

- **Why:** a full live test with the QA account (97 checks, three models, Arabic and English, phone and desktop) and
  direct Qwen measurements found the following.
  - A reply that was only raw `<tool_call>` markup, and replies with no text.
  - Invented source links, and «لا أملك وصولاً إلى الإنترنت» on search-enabled models.
  - The model denying recent events it did not know, and English questions answered in Arabic.
  - Letters losing their Word/PDF bar, and other smaller defects.
- **Replies:**
  - A search call the model writes as text is never shown.
  - An empty reply says «لم يصل رد هذه المرة.» with «أعد المحاولة», and the latest one is retried once by itself. This
    covers a reply that is only the hidden suggestions or only «أبحث عن…».
- **Instructions:**
  - Today's date, and never deny an event it does not know.
  - Answer in the language of the user's last message.
  - «المصادر» lists organisation names without links.
  - Saudi Arabia first, no announcing a search, no Chinese words.
  - «بصير برو» no longer claims it can search, and points to «لايت» and «بلس».
- **Documents:**
  - A letter that comes as an artifact gets its Word/PDF bar.
  - Downloads give the document alone.
  - «الخلاصة والخطوات التالية» closes a deck.
  - `<br>` in a table cell is a line break on the page and in every file.
- **Suggestions and errors:**
  - Actions follow the reply's language under an artifact.
  - No «جدول» under a table, and no «خطاب رسمي» under a letter.
  - Employees no longer get a 403 for the MCP server list.

### Changed — CURRENT_STATE one line per area; dev deploy log on #15 (ADR-0023, owner decision 2026-10-26)

- **Why:** `project/CURRENT_STATE.md` was 1 byte under its 10 KB budget, and every deploy needed a follow-up «deployed» PR.
- §1 keeps one line per area (level + link to its owning doc or Issue); counts and deploy IDs live in the test docs,
  the Issues and #15. 10,239 → about 9 KB, with every fact kept in
  `docs/history/2026-10-26-current-state-ledger.md`.
- ADR-0023 amends ADR-0009 item 3: each `dev` deploy is one comment on #15, and the state file changes only when a
  verified state changes. Owner phone checks are one checklist, #234.

### Added — phone app (PWA) installability check (#232)

- `tests/ui/pwa_install.cjs` checks what Android Chrome and iPhone Safari read before installing «بصير»: the manifest,
  icons, service worker, Chromium's own installability verdict (with a live control), iPhone tags, the start address,
  the «محادثة جديدة» shortcut and the offline page. 9/9 on an image built from `main`; a broken manifest fails it.
- The LibreChat upgrade runbook runs it, so a changed upstream manifest shows before an upgrade.

### Changed — PowerPoint downloads on the brand guide's presentation backgrounds (owner decision 2026-10-26)

- **Why:** the owner's brand skill carries nine presentation backgrounds; the platform skill holds only text, and
  downloaded decks had a solid blue title slide. The owner approved putting the guide's backgrounds into the files the
  platform builds.
- **Title slide:** `EF-BG-09` behind it (blue, the radial on the left). The title and subtitle sit on its calm right side;
  the white logo stays at the top right. Not mirrored for English.
- **Closing slide:** a last «الخلاصة» or «الخطوات التالية» slide with points only goes on `EF-BG-07`, in white text with
  green bullets. The model instructions and the brand skill now ask every deck to end with that slide.
- **Content slides** stay white. Without the backgrounds, both slides are solid primary blue.
- Patch 0039; the two JPEGs are copied unchanged into `brand/assets/` (about 107 KB, fetched only when downloading).

### Changed — Chat replies: no summary card, headings back to primary blue (owner decision after the live test, #224)

- **Why:** on the live site, a long reply opened with a nine-line «الخلاصة» card on the phone, which repeated the reply.
  The owner asked to remove it. The reply already starts with the answer.
- **Summary:** the instruction is gone and replaced by «no summary that repeats the reply». The card styling and the
  conversion of a bare «**الخلاصة:**» line (#226) are gone too.
- **Headings:** back to primary blue `#2C3A82`, as the brand guide assigns it and as the reply's Word and PDF files carry
  it. Body text stays in the primary dark.

### Changed — Chat page redesign: reply toolbar, smart suggestions, skills as text, web search always on (owner-approved, #224, ADR-0022)

- **Why:** the owner approved one chat design, covering 21 states on phone and desktop, after a comparison with ChatGPT,
  Gemini, Claude and Copilot. The owner asked for web search always available and for skills that work with the models
  and with search.
- **Web search:** there is no switch any more; a line in «+» says search runs by itself. A chat saved without search
  shows «بلا إنترنت ×», which turns search back on.
- **Skills:** a picked skill's instructions travel with the message as a text attachment, with no tools, so Qwen keeps
  searching (#213). The «$» list explains how to use a skill in three steps and gives an example for each one. A picked
  skill is a green «$» chip, and a one-time tip introduces skills.
- **Composer:** «+» now offers a file, Documents, a ready command, a skill, and memory. The hint changes with the state:
  a skill picked, a file attached, or a temporary chat. On phones the temporary chat sits in the header, and «+»,
  «المزيد» and download open as bottom sheets.
- **Replies:** long replies open with a summary card (also when the model drops the quote mark), and headings are dark. The toolbar is copy, download, regenerate,
  rating and «المزيد» (share the chat first), with the model's name at the end. Download shows each format as a badge
  next to the file name. Letters and minutes get a Word/PDF bar.
- **Smart suggestions:** two or three questions from the reply and up to two actions, under the latest reply. They come
  from a hidden block the model writes; without one, the actions come from rules.
- **«بصير برو»:** unchanged, with «لا يبحث في الإنترنت حالياً» in the model menu. The model decision stays with the
  owner (#213).
- **Tests:** `tests/ui/chat_design.cjs` (phone and desktop, Arabic and English, axe), new mock replies
  (`SYNTH-DESIGN-*`), and Jest specs for suggestions, skills, chips and the toolbar.

### Changed — Sidebar v5: «التخصيص» gathers the tools, the phone drawer shows its sections on top (owner-approved, #221)

- **Why:** the owner's phone feedback: the drawer's bottom tab bar went unnoticed, and the floating «دردشة جديدة» covered
  the history. The owner also wants a sidebar that takes future sections without a redesign.
- **«التخصيص» page (`/customize`):** a card per tool with one line on what it is for.
  - **«لك»:** ready commands, skills, memory and bookmarks.
  - **«للمسؤول فقط»:** assistants with «مساعد جديد» (a new chat with the builder open), the parameters, and MCP servers
    named «الموصلات».
  - **Built from LibreChat's own sidebar links:** a section that an upgrade or a newly enabled feature adds appears as a
    card marked «جديد», with no sidebar change.
  - **Tool pages** lead back to it: a breadcrumb on desktop, a back button on phones.
- **Desktop rail:** new chat, chats, Projects, Documents, «التخصيص», account. «المزيد» is gone, and Skills moved into
  «التخصيص». The chats panel is unchanged.
- **Phone drawer:** «بصير» and X on top, then the search, then three section tiles (Projects, Documents, Customize), then
  «الدردشات» with its filter, the chips and the history. The account and «دردشة جديدة» sit at the bottom. There is no tab
  bar and no floating button.
- **Upgrade cost:** the page is EF's own file. The tools open LibreChat's components unchanged. Only small edits touch
  files already patched (patch 0037).
- **Tests in the repository** (toward #194): `tests/ui/ui_stack.py` and `tests/ui/sidebar_v5.cjs`, 135 checks (desktop and
  phone, Arabic and English, employee and admin, axe). Jest specs cover the rail, the page and the way back.

### Changed — MCP servers for admins only (owner decision, #218, ADR-0021)

- **Admins** add remote MCP servers and use their tools. Employees still have no MCP (403), and nobody can share a
  server, so an admin's server never reaches employees.
- **How:** `infrastructure/common/roles-policy.js` sets the MCP permissions of the two roles before every LibreChat
  start (Railway start script, Compose `command`). `interface.mcpServers` is gone from `librechat.yaml`, because that key
  writes one value to both roles. If MongoDB stays unreachable, the server does not start.
- **Safety unchanged:** no local (`stdio`) servers and no `${VAR}` URLs from the UI. Without `mcpSettings.allowedDomains`,
  LibreChat's SSRF protection refuses private, loopback, link-local and internal service addresses.
- **Sidebar:** «خوادم MCP» joins «للمسؤول فقط» in «المزيد», with the «للمسؤول» badge (patch 0036). A tool in the
  panel keeps its whole name in the header: the way back now reads «‹ الدردشات».
- **Checks:** M22, M24, M25, M35, M36, M80 and M82 updated; new M92 (admin access, `stdio` and `${VAR}` refused) and
  M93 (private addresses refused, nothing stored).

### Changed — LibreChat's self-registration is on (owner decision, ADR-0020)

- **Sign-up:** the sign-in page shows LibreChat's registration link. Anyone can create an account with email and
  password; it gets role USER and signs in at once (no mail service, so the address is not verified).
- **Arabic:** the sign-up link reads «سجّل الآن» (upstream: «سجل الان»; `ar.json`). The form is fully Arabic.
- **No new usage limits** (owner decision). Upstream's registration cap of 5 accounts per IP per hour applies.
- **New environments:** create the administrator with `create-user` before a stack is reachable, because the first
  account of an empty database becomes ADMIN (deployment.md section 3).
- **Checks:** T13, T14 and T15 (Compose), R16 and R17 (Railway emulation) and M06 (mock chat) now expect registration on.
  T14, R17 and M06 also check that a self-registered account is a USER. N12 and N14 pin the new value.

### Added — Model strategy check: usage and cost report, replayable benchmark (#211)

- **Verified, unchanged:** two models and three modes (سريع `qwen3.8-flash` without thinking, the default; متأنٍّ the
  same model at `medium`; عميق `deepseek-v4.1-flash-1017` at `high`), internet on in every new chat, the composer's
  switch moving the chat to a twin without search, and only approved models accepted by the API.
- **Usage report:** `scripts/operations/usage-report.sh` (read-only) counts calls and input/output tokens per month,
  mode, model, background task and user from LibreChat's own records, with a cost estimate from dated Qwen Cloud list
  prices. It reads no chat text. Searches, separate reasoning tokens and the memory agent's calls are not recorded by
  LibreChat; the Qwen bill stays the reference. New check M91.
- **Benchmark:** `tests/benchmark/` holds 33 synthetic scenarios (letters, email, summaries, translation, proofreading,
  minutes, reports, analysis, comparisons, reasoning, files, images, recent news, timeless questions, internet on/off).
  `--offline` needs no network; `--live` measures time, tokens, cost, searches and checks per mode.
- **Search instructions:** results come from the internet, never «a knowledge base»; a reply that used them ends with
  «المصادر» and one line saying web information can be incomplete or out of date (owner requirement). Sources still
  appear in only 3 of 8 searched replies: Qwen's OpenAI-compatible API returns no source list.
- **Measured gaps, for an owner decision (#213):** «عميق» never searches on Qwen Cloud's Chat Completions API (0 of 14
  recent-news questions), and the «Skills» switch stops the search in practice. Nothing is changed for them yet.
- **Mock model:** a streamed reply now ends with a usage chunk, as Qwen Cloud's does, so LibreChat records it.

### Reverted — Google sign-in for testers (#202) withdrawn by the owner (#201, ADR-0019 deprecated)

- **Back to the default:** self-registration and social login are off again. Only accounts an administrator creates
  (`create-user`) sign in, with email and password. No Google button, no Google secrets.
- **Timing:** withdrawn on 2026-10-25, before any Google client was set on Railway and before any tester signed in.
- **Restored:** the configuration, the checks (N34, N35 and R47 removed; T13 and R16 expect social login off again) and
  the docs, as they were before #202. ADR-0019 stays in the register as Deprecated.

### Changed — Sidebar v4: a rail and a full-height chats panel (#204, owner-approved Concept 2)

- **Why:** in v3 the chat history started about 610 px down the column and had about 30% of its height (15% with
  «More» open). Now the first chat sits about 196 px from the top.
- **Desktop rail (76 px), always shown:** the «Baseer» icon, «New chat», «Chats» (opens and closes the chats panel, also
  Ctrl/⌘ ⇧ S), Projects, Skills, Documents, «More» and the account.
- **Chats panel (300 px, resizable, remembered):**
  - header «Chats» with LibreChat's sort and filter menu, and a collapse button;
  - the chat search;
  - the chips «All», «Pinned» and «Project ▾» (one project, or «No project»; the server filters);
  - the history, pinned first.
- **Pages never replace the panel.** Projects, Skills, Documents and the «More» pages open in the main area. The admin
  tools (builder, parameters) keep the panel with «Back to chats».
- **Phone:** the drawer is the chats screen, with a floating «New chat» and a bottom tab bar (Chats, Projects, Skills,
  Documents, More).
- **Changed from the canvas:** grouping by project became a project filter (the server filters but cannot group); the
  chips carry no counts.
- **Build:** patch 0035, `brand.css`, `ef-chat.css`, `ar.json` (13 new keys, `com_efaiw_rail_search` removed).

### Changed — Sidebar v3: sections open as pages in the main area; the collapsed rail mirrors the column (#198)

- **Pages:** Projects, Skills, Documents, and from «More» memory, bookmarks and ready commands open as pages in the main
  area (`/files`, `/memories`, `/bookmarks` and `/prompts` are new). The sidebar keeps the chat search and history;
  the open page's row is marked. The admin's assistant builder and parameters stay panels (they belong to the open chat).
- **Collapsed rail:** the same order as the column (new chat, search, Projects, Skills, Documents, «More»); «More» is a
  small menu, with the admin tools under «Admins only».
- **Phone:** choosing a row closes the drawer and opens the page full screen; skills and ready commands show the list,
  then the chosen item with a way back.
- **Documents:** choosing a document attaches it to the open chat and goes back to it, as LibreChat's files panel did.
- **Focus ring:** a thin ring in the EF light blue instead of the heavy black or blue frame, for keyboard users only.

### Security — S1 engineering stabilization: SC-18 scan, R-09, agent push guard (#196)

- **SC-18 scan 2026-10-25** (Trivy 0.76.0, pinned digests; derived Railway images not rescanned). There is a **new
  CRITICAL, R-09**: dompurify 3.4.16 (GHSA-cg2g-xh64-v4q7). It is also in the public Railway image, and the ADR-0012 layer
  does not cover it. Assessed not reachable, because no LibreChat code or patch sets `SAFE_FOR_TEMPLATES`/`IN_PLACE`;
  the disposition is the owner's (#16). New HIGH findings are summarised in the register (§4). `image-scan.yml` has never
  run (D2), so the weekly scan happens in agent sessions.
- **Dependabot:** `mongo` now gets only 8.0.x patches (ADR-0007). Minor moves such as 8.3 (#177) go through #62.
- **Claude Code settings:** `git push … refs/heads/main` is denied. The GitHub MCP direct file-write tools need
  confirmation, because they could commit to `main` through the API while #3 is not enforced.
- **State:** `CURRENT_STATE.md` no longer lists the closed #37 as a blocker; R0.2 closure is tracked on #41. The S1
  findings are in #193 (patch stack), #194 (client tests) and #195 (Compose parity).

### Changed — Sidebar v2: Projects, Skills and Documents on top; admin tools in «More» (#189)

- **Top of the column, for everyone:** «New chat», then Projects, Skills and Documents (the files panel), and «More»
  with memory, bookmarks and ready commands (LibreChat prompts). Under a line: the chat search, Pinned, then the chats
  with their sort and filter.
- **Projects** open as a panel in the sidebar: «New project», the projects with their chats, «All projects», and back
  to the chats. On phones, inside the drawer.
- **Admins only (owner decision while the owner learns them):** the assistants marketplace, the assistant builder and
  the parameters, in «More» with a «للمسؤول» badge. Display only: role permissions are unchanged.
- **Composer hint:** «اسأل بصير لايت أو اكتب / لأمر جاهز».
- **Fixed:** an English chat title in the Arabic interface lost its first letters to the overflow fade (and an Arabic
  title in the English one); the «auto-send» button of the ready commands panel nested a hidden checkbox (axe).
- **Wording:** «النصوص الجاهزة» is now «الأوامر الجاهزة», and «الوكلاء» is «المساعدون».

### Added — Eight official ready commands for everyone; only admins publish to everyone (#189, ADR-0018)

- **Ready commands** (`ai/prompts/ef-templates.json`): official letter, document summary, email, meeting minutes,
  formal translation, proofreading, measurable goals and business requirements draft. Every employee finds them in
  «More → ready commands» and by typing «/» in the composer; templates with fields ask for them first.
- **Created once** by `infrastructure/common/prompts-seed.js` in the background of the LibreChat start (Railway start
  script; Compose `command`), owned by the first admin and shown as «صندوق البيئة». An admin's edit or deletion is kept.
- **Publishing:** agents, prompts and skills drop `public: false`: employees share with chosen colleagues, admins can
  publish to everyone. Shared links still need a signed-in account.
- **Tests:** `mock_chat.py` M87–M90 and M22 (per role). Known v0.8.8 gap: the lists do not return the `/command`, so
  the «/» list shows the names (fixed upstream after v0.8.8).

### Changed — The welcome screen greets the employee by first name (#186)

- **Greeting:** «صباح الخير، نورة» from 04:00 and «مساء الخير، نورة» from 12:00 on the employee's device, with «كيف أساعدك
  اليوم؟» (`customWelcome`) as the second line. Compound first names stay whole («عبد الله»); English says Good morning,
  afternoon or evening. Owner-approved option B (no starter cards).
- **Fixed — composer direction:** with Settings → Chat direction set to right to left, the Arabic composer showed Send
  on the start side and + on the end side (the rows were reversed twice). The setting now only reverses them on
  English pages, and the empty box's hint («اسأل بصير») starts on the right.
- **Tested** on 1440, 1366, 390 and 360 px in Arabic and English: 18 new cases and the 131-case interface suite
  (`docs/quality/concept1-interface-test-cases.md`).

### Changed — The owner-approved interface: sidebar, composer, welcome, phone drawer and EF favicon (#181)

- **Sidebar:** one column: the EF logo, «New chat» in the primary blue, the chat search, the agents marketplace, «More»
  with every other panel (agent builder, skills, prompts, memory, bookmarks, files, parameters), the chat history and
  the account. Collapsed, the labelled rail stays. Nothing LibreChat offers is removed, and the panel shortcuts work.
- **Phone:** the same column in the drawer (X, Escape or a tap outside closes it), a menu icon opens it, the open
  chat's title is centred in the bar, and the model menu is a bottom sheet.
- **Composer:** a 28 px card; the model in use is named («بصير لايت») beside Send, and its menu lists the three specs
  with their descriptions. «البحث في الويب» replaces «الإنترنت». Voice input, attachments and the + menu stay.
- **Chat:** the employee's message on the lightest primary blue with dark text (it was white on the primary blue).
- **Welcome:** the Baseer emblem above «كيف أساعدك اليوم؟» in the primary blue, the notice right under the composer and
  a quarter of the EF radial graphic in the end corner; on phones the EF logo heads it.
- **Favicon:** the EF symbol fills the tile so it reads at 16–48 px, `/favicon.ico` is served (it returned 404) and an
  SVG icon is linked.
- **Specification:** `docs/design/concept1-interface.md`.
- **Tested** on 1440, 1366, 390 and 360 px in Arabic and English with Playwright and axe: 131 cases pass with no axe
  violations (`docs/quality/concept1-interface-test-cases.md`).

### Fixed — The employee's chat journey on a laptop and a phone (#175)

- **Tested end to end** (new chat → talk to «بصير» → open, switch, rename, search, pin, share, archive, delete) on
  1366, 1440, 390 and 360 px with Playwright and axe: 25 cases in `docs/quality/chat-journey-test-cases.md`.
- **Chat list order:** a chat continued now goes to the top at once. Chats started in the session used to stay above
  it until a reload (upstream defect: an empty date read as "now").
- **Phone composer:** stays one row after the first reply; the send and stop button no longer jumps to a second row,
  and an opened chat's last reply is no longer hidden behind the composer. The context gauge shows on phones from half
  the context, with a lighter track that no longer looks like a spinner.
- **Phone keyboard:** on touch screens Return starts a new line and the send button sends (Settings → Chat keeps the
  switch). The share dialog opens without an info card over it.
- **Screen readers:** the side-menu rail and the phone drawer's panel button are announced with their visible names;
  «فتح القائمة الجانبية» replaces «افتح القائمة الجانبية».

### Changed — Live provider limits measured; a stalled reply ends after 60 s (#39)

- **Measured on live Qwen Cloud** (38 synthetic streamed calls over the six chat endpoints): headers arrive with the
  first token after 1.4–3.1 s; chunks then come at most 3.1 s apart; full replies take up to 18.7 s (Lite), 25.9 s
  (Plus) and 47.9 s (Pro). The 20 s per-attempt timeout and one retry stay.
- **Transport limits** (`endpoints.agents`): a reply that stops streaming now fails after 60 s of silence instead of
  15 min; the header limit is 60 s (was 5 min). New check M86.
- **Documented** in `ai-safe-defaults.md`: no message or concurrency limits are set today; usage is recorded per call
  in MongoDB `transactions`; per-user limits, cost and provider retention stay owner decisions.

### Security — Admin Panel: zod and the YAML import (#165)

- **zod 4.4.3 → 4.6.7** in the Railway panel build (patch `0001`, `bun.lock` regenerated with Bun 1.3.11): every server
  function validates its input with it before any session check (CVE-2023-54404, memory exhaustion by a large array).
- **YAML import needs an admin session** (new patch `0003`): it was the one function that never called LibreChat, so
  anyone could post YAML to it, and that YAML reached zod 3 inside `librechat-data-provider`, which has no fixed 3.x.
- Trivy: 0 CRITICAL, 16 HIGH (was 17). The remaining zod 3 copy is reachable only by a signed-in admin.

### Fixed — Chat titles in the user's language (#169)

- LibreChat's default title instruction asks for an English title in title case, so Arabic chats got English titles.
- The six chat endpoints now share one Arabic `titlePrompt`: an Arabic title for an Arabic chat, an English one for an
  English chat, five words or less, no punctuation. Titles still run on `Qwen Tasks` (fast model, no thinking or search).
- Measured on live Qwen (9 synthetic first exchanges): Arabic titles 5/5 (0/5 before), English stays English 4/4;
  about 1.5 s and 35 more tokens per title. Through a local LibreChat stack (Lite and Pro): 4/4 in the chat's language.
  M42 checks that the instruction reaches each title call.

### Fixed — Artifacts with the live model; question cards off (#167)

- **Found by a live QA run** (synthetic prompts on Qwen Cloud, with the owner's approval):
  - Qwen wrote web pages inline and said the "documents tool" was not available.
  - It asked 2–6 questions before writing a letter, page, script, logo or deck.
  - Every document reached the panel with its words run together (no fenced block).
  - With the question tool offered, Qwen's built-in internet search never ran, and the model called a `web_search` tool
    that does not exist, sometimes until the reply failed.
- **Instructions:** one Arabic instruction set explains the artifact format, says it is written in the reply and is not
  a tool, when to create one without being asked, and the rules per type. LibreChat's English artifact text is off
  (`artifacts: 'custom'`). Search is not a tool either. A creation request gets a full draft with its assumptions.
- **Question cards off** in the three models (owner decision 2026-10-24). Baseer asks in plain text only when a request
  cannot be done; agents can still use the cards.
- **Panel:** the document is taken exactly as written, fenced or not. Documents, pages, drawings and code preview in a
  local sandboxed frame, at once and without codesandbox.io; React still uses it. No «مستندات» switch: artifacts are
  always on.

### Fixed — EF logo at its full minimum size (#163)

- The blue logo was drawn about 5% smaller than set: the logo file's width and height do not follow its own artwork.
  It is now drawn at the full size, keeping the guide's minimums:
  - 40 px in the side panels, shared chats, help and offline pages;
  - 1.5 cm in the PDF.
- The logo file is unchanged.

### Changed — Admin Panel in the EF brand (#160)

- **Font:** Aktiv Grotesk across the admin panel.
- **Colours:** primary buttons, switches and checkboxes in EF primary blue; links and focus in EF link blue. The panel's
  optional dark theme uses the guide's light blue instead of the ClickHouse yellow.
- **Logo:** the EF app icon in the sidebar, the EF logo above the login form, the EF favicon, and the tab title
  "Baseer Admin Panel".
- The panel stays in English. Railway only: the Compose panel keeps the official image.

### Changed — Word and PowerPoint in the EF font, with the logo (#157)

- **Font:** Word and PowerPoint downloads carry Aktiv Grotesk inside the file (Regular and Bold), so they show it on any
  computer. Owner decision 2026-10-23:
  - Where the font is not installed, Word and PowerPoint open the file read-only: the font's licence allows preview and
    print only. LibreOffice does not use such an embedded font and shows its own.
  - Each file is about 2 MB larger.
  - Excel stays in Tahoma: the format cannot carry a font.
- **Logo:** the blue logo at the top right of a Word document's first page, as in the PDF, and the white logo at the
  top right of the PowerPoint title slide. The letterhead and date format stay open (#145).
- If the font or the logo cannot be loaded, the file is written as before: Tahoma, no logo.

### Added — artifacts that work like Claude's (#153)

- **Versions:**
  - A change to an artifact becomes a new version of it. The panel shows «الإصدار 2 من 3» and lists that artifact's versions only.
  - Before, the menu listed every artifact of the chat.
- **«المخرجات في هذه المحادثة»** switches between the chat's artifacts.
- **«حاول الإصلاح»:** when a preview fails, one press sends the error to Baseer. Files staged in the message box are not
  attached to it.
- **«فتح في علامة تبويب جديدة»:**
  - A page, drawing or document opens in its own tab, in the EF font.
  - It runs isolated, in a sandboxed frame with no access to the platform.
- **Code files:**
  - The language is kept.
  - Claude's `application/vnd.ant.code` opens as code.
- **Instructions:**
  - Reuse the identifier when changing an artifact.
  - Code files carry their language.
  - React roots are right to left.
  - Never use `/api/placeholder`.
- **Panel motion** follows the reading direction.
- **Tests:** the download tests that had failed since patch 0024 now follow the document menu.

### Changed — EF font on every screen and preview (#152)

- **Artifact previews:**
  - Every preview in the side panel now loads Aktiv Grotesk from the platform: Markdown document, HTML page, React
    component, SVG and code. Before, it showed only where the font was installed.
  - A font the model sets itself still wins.
- **Diagrams:**
  - Mermaid diagrams in chat and in the panel are drawn inline in the page font, so labels no longer overflow.
  - SVG and PNG exports carry the font.
  - A diagram's own `%%{init}%%` can no longer change its theme, CSS or font.
  - Diagram CSS cannot fetch outside URLs.
- **High contrast** keeps Aktiv Grotesk; it used to switch chat text to Inter.
- **Arabic text:**
  - Arabic in code falls back to the brand face.
  - Arabic emphasis is SemiBold instead of a fake slant.
- **Logo:**
  - The PDF view carries the blue logo at the top right, at the guide's print minimum, and waits for the fonts before printing.
  - The shared chat, help page and offline page show the logo.
- **Tab titles:** they name «بصير» instead of "LibreChat".

### Added — PowerPoint and Excel downloads in the EF brand (#149, #145 Phase A)

- **«تنزيل» under every reply** now offers Word, PowerPoint, Excel (when the reply has a table), PDF and Markdown. A
  Markdown document in the side panel has the same menu.
  - Every file is built in the browser in the EF palette, with no new dependency, service or spend (patch 0024).
- **PowerPoint (16:9):**
  - An EF-blue title slide from the first `#`, then a slide per `##`.
  - Bullets, numbered lists, quotes, code and tables with a primary-blue header.
  - Long content continues on the next slide under "(تابع)", and long tables repeat their header.
  - Real title placeholders; Arabic right to left; Tahoma.
- **Excel:** one sheet per table, named after the heading above it.
  - Numbers are stored as numbers: Arabic-Indic digits, separators, percentages, units and currencies, and accounting
    negatives in parentheses.
  - Dates and leading-zero codes stay text.
  - The header row is frozen, with a filter. Arabic sheets run right to left.
- **Instructions and the brand Skill:**
  - They say how to write a deck or Excel tables, and not to claim a file was attached.
  - The Skill gains SVG rules.
- **Word:** the Open XML SDK validator found two schema errors that Word may "repair" on opening, the section direction
  order and the quote border. Both are fixed.
- **Arabic menu labels:** the file extension showed as "(docx.)"; a left-to-right mark makes it read "(.docx)".
- **Checks:** every generated Word, Excel and PowerPoint file passes the Open XML SDK validator (Office 2019 schema) with
  0 errors, and was rendered by LibreOffice and read back with python-docx, openpyxl and python-pptx.

### Added — EF brand on every output: platform brand Skill for everyone (#146, ADR-0017)

- **Brand Skill:** `ef-brand-guidelines` in `ai/skills/` is a Baseer version of the EF visual identity guide (v01, Nov 2024).
  - It covers palette roles, type and logo rules, plus rules for Markdown, HTML, React, Mermaid, tables, charts and slide
    outlines.
  - It is installed for every employee from the repository: baked into the Railway image at `/app/skill` (LibreChat's
    deployment Skills) and mounted read-only in Compose.
  - It is read-only, always applied when skills are on, and also reaches agents that use skills.
- **Every chat:** the three specs' instructions carry a short brand block (palette and type), with or without internet. The
  brand therefore holds when the + menu's skills switch is off.
- **Files the platform builds** follow the brand whatever the model writes (client patch 0023):
  - The Word download uses EF blue headings, the EF table header and Tahoma (the guide's secondary typeface). It was Arial
    and `#1F3864`.
  - The PDF / print view loads Aktiv Grotesk from the platform.
  - Markdown document previews and every Mermaid diagram use the EF palette.
- **Check:** `repo_checks.py platform-skills` validates each `SKILL.md` as LibreChat does, because an invalid one stops the
  server from starting. It caught an unquoted `:` in the first draft.
- **Tests:** M83–M85, with M26 updated for the primed Skill. The mock logs line digests of every message.

### Added — admin site: the official LibreChat Admin Panel (#141, ADR-0016)

- New `admin-panel` service on every host. Windows: `http://localhost:3000`. Ubuntu: a second Caddy name. Railway `dev`: a second
  `*.up.railway.app` link, authorised by the owner on 2026-10-23.
  - It manages groups, custom roles and admin grants, and shows the audit log.
  - LibreChat checks admin rights on every request, and admins get «لوحة المسؤول» under Settings.
- Security: the official image ships TanStack Start 1.167.30 (CVE-2026-102989, an unauthenticated XSS; CRITICAL). Railway therefore
  runs a temporary rebuild of the same upstream commit with only dependency versions raised (0 CRITICAL). It has an exit guard
  for the day upstream ships a fix. Compose keeps the official image on loopback or the internal network only.
- Platform settings stay in Git. `scripts/operations/admin-config-drift.sh` fails on any override stored in MongoDB, or on a
  custom role that allows more than `USER` (SC-23).
- Limits of the Preview panel on v0.8.8: English only; no user page; accounts are still created with `create-user`; the audit
  log covers grants only.
- Checks: T42–T49 and O07, R40–R46, M76–M82, N26–N33. `railway_checks.py` now matches compose images by exact repository name.

### Changed — message box like ChatGPT, Claude and Qwen Chat (#138)

- From the owner-approved comparison of ChatGPT, Claude, Qwen and DeepSeek: one «+» button holds «إرفاق ملف»,
  «مستندات», «الإنترنت», skills and memory, each with a check mark; a tool that is on shows as a chip. The
  shadcn/ui and custom-prompt artifact options are gone.
- «سريع / متأنٍّ / عميق» replaces the model button and the «تفكير» switch (Lite, Plus, Pro; the chat switches in place).
- «الإنترنت» can now be turned off per chat: the chat moves to a hidden no-search twin of its spec on one of three new
  endpoints (`Qwen NoWeb`, `Qwen Thinking NoWeb`, `DeepSeek NoWeb`; [ADR-0015](docs/architecture/adr/0015-web-search-through-provider-built-in-search.md) §5; M73–M75).
- «PDF / طباعة» under «تنزيل»: the reply in a right-to-left print view, saved as PDF from the print dialog.
- A document the reply is writing opens in the side panel by itself. Patch 0022; help page updated.

### Added / Fixed — owner feedback: phone menu, search, internet, thinking switch, better outputs (#135)

- Phone side menu opens from the right in Arabic (from the left in English), and the swipe follows: patch 0021.
- Conversation search found nothing on Railway `dev`: chats saved before Meilisearch was reachable stayed out of the
  index, because upstream skips the start-up sync below 1000 unindexed messages. `MEILI_SYNC_THRESHOLD=0`: every start
  indexes what is missing (M70). The phone drawer's search placeholder is no longer cut off.
- Internet: Qwen Cloud's built-in web search on «بصير لايت/بلس/برو» (owner decision, [ADR-0015](docs/architecture/adr/0015-web-search-through-provider-built-in-search.md));
  titles, memories and summaries move to a new `Qwen Tasks` endpoint without search. Each search is billed on the same
  Qwen account. The model is told to name its sources (M41, M42, M69, M71).
- «تفكير» switch in the message box: moves the chat between Lite and Plus in place; Pro always thinks.
- Outputs: Arabic instructions for the reply format and sources; every spec starts in artifacts mode (long documents,
  code, HTML, diagrams in the side panel; M72); Markdown artifacts read right to left; a «تنزيل» button under every
  reply saves it as a Word document (.docx, right to left) or Markdown. Help page updated.

### Fixed — chat page QA: 50 test cases, 4 defects fixed (#133)

- A Senior QA pass on the chat page only: [docs/quality/chat-page-test-cases.md](docs/quality/chat-page-test-cases.md)
  holds 50 cases (composer, models and thinking, streaming and stop, rendering, message actions, errors, files,
  questions, the sensitive-data filter, keyboard, accessibility, HTML injection). All ran with Playwright on desktop,
  phone and a 320 px phone against the mock model: 95/105 checks before, 105/105 after.
- Patch 0020: the model button's screen-reader name did not include the model it shows (WCAG 2.5.3); the toast region
  was announced in English («Notifications (F8)»); an untitled chat was announced as «محادثة New Chat».
- `ar.json`: the two buttons that switch between versions of a message now share one wording.

### Changed — trial model lineup: «بصير بلس» thinks, «بصير برو» runs on DeepSeek V4.1 Flash (#131)

- Owner decision 2026-10-21 for the test period before an on-premises or in-Kingdom model: the best results per
  dollar (the owner pays; no vendor preference), on the same Qwen Cloud account, key and base URL.
- «بصير بلس» is `qwen3.8-flash` with thinking at `medium`. It replaces `qwen3.7-plus`, which scored 25 on the
  Artificial Analysis index against 40 for Lite, at a higher price.
- «بصير برو» is `deepseek-v4.1-flash-1017` with thinking at `high`, served by Qwen Cloud. It replaces `qwen3.8-max`:
  the same index score (45) for about a fifth of the cost. Both new models also ship open weights.
- Thinking and its depth are set by the server (`addParams`): the parameters panel cannot change them, and Lite drops
  the panel's reasoning-effort setting. With thinking on, the model's reasoning goes back with the answer to its
  question, as Qwen Cloud asks for tool turns (`customParams.includeReasoningContent`; built in for DeepSeek).
- `qwen3.7-plus` and `qwen3.8-max` are no longer accepted and the «Qwen Max» endpoint is gone. Titles, memories and
  summaries stay on `qwen3.8-flash` without thinking. Help page and docs follow.
- Mock LLM: DeepSeek ids, reasoning before a tool call, and the effort, output limit and returned reasoning in its
  log; `mock_chat.py` M66–M68.

### Added — LibreChat batch 2: clarifying questions, file reading, long-chat summaries, sensitive-data filter (#129)

- Clarifying questions: the three Baseer specs get LibreChat's `ask_user_question` tool and a short instruction on
  when to ask. An unclear request pauses on a card with one to four questions and options; the employee picks an
  option, types an own answer or skips, and the reply resumes.
- Files: PDF, Word and Excel are read as text by the built-in parser (no RAG or OCR service). Upstream sent a PDF as
  a base64 file that the filter could not read; PDFs now go as text. Limits: 20 MB per file, 50 MB per message,
  10 files (upstream: 512 MB), also for the Qwen endpoints, which take the `agents` entry.
- Long chats: when the history overflows the context window it is summarized in Arabic on `qwen3.8-flash` without
  thinking instead of dropping the oldest messages; «ضغط السياق» in the context gauge does it on request.
- Sensitive data: a message, an answer or a file's text with a Saudi national ID or iqama number, a Saudi IBAN, an API
  key or a bearer token is refused before the model and the database, naming what to remove (SC-22). Upstream's
  starter patterns are off: they matched ordinary text («To the bearer of this letter»).
- Patch 0019: the question record shows «تخطّيت هذا السؤال» instead of the model's English notice and its answer
  rule sits on the start side; the filter's refusal has its own Arabic message instead of «تعذّر على Qwen…»; upload
  errors and file kinds are translated; the summary box no longer names «openAI/qwen3.8-flash».
- Mock LLM: question, summary and file-marker scenarios; `mock_chat.py` M57–M65. Help page updated.

### Fixed — full Arabic RTL test of the web client (#127)

- Every screen tested in Arabic on desktop and phone (Playwright, axe, mock model); report with before/after checks in
  `docs/design/audits/arabic-rtl-full-test.md`. 13 defects found and fixed; the fix checks went from 5/21 to 21/21.
- Patch 0018: logical CSS properties stay logical in the client build (PostCSS had turned `start-3`, `text-start`,
  `me-2` into left-to-right values, e.g. the sign-in labels sat on the left); sliders follow the page direction; the
  side-panel search labels sit on the start side; /reset-password returns to sign-in while reset is off; the hidden
  heading of a user message no longer reads «نص جاهز»; the phone drawer's close button no longer throws a TypeError.
- `ef-chat.css`: Arabic comments in code blocks no longer flip the line, math reads left to right, search results are
  RTL, text fields follow their text (sidebar rename, e-mail), negative numbers keep their sign, labels do not split
  Arabic words.
- `ar.json`: share dialog title, memory setting, rate-limit message, and language names in their own language.

### Added — LibreChat batch 1: conversation search, internal shared links, side-by-side compare, context gauge (#125)

- Conversation search on a private Meilisearch v1.54.3 service in every environment (ADR-0014): Compose and a third
  Railway service (`meilisearch`, own volume, 1 vCPU / 1 GB, no domain), master key per environment, `SEARCH=true`.
  Upstream's v1.35.1 pin was not used (2 CRITICAL findings). `search-reindex.sh` rebuilds the index after a restore;
  `restore.sh` runs it.
- Shared links for signed-in employees only: `ALLOW_SHARED_LINKS=true`, `ALLOW_SHARED_LINKS_PUBLIC=false` stays.
- `interface.multiConvo` and `interface.contextUsage` on: two models answer one message; the context gauge under the
  composer. The token balance was dropped by the owner.
- Patch 0017: the search box mirrors in RTL, the compare bar names the picked model and its remove button is translated,
  the gauge uses Western digits. `brand.css`: white text in the user bubbles of search results.
- Checks: `mock_chat.py` M49–M56, `compose-stack.sh` T38–T41, `railway-emulation.sh` R34–R39, negative N21–N25,
  `compose_checks.py`/`railway_checks.py` for the third service.

### Changed — principal UX/UI audit and its implementation (#123)

- Audit of every screen in Arabic and English on phone, tablet and desktop, written as a frontend handoff
  (`docs/design/audits/ux-ui-principal-audit.md`, 21 findings with acceptance criteria).
- Patch 0016: a saved chat opens on its newest message; the chat notice follows the interface language; the sign-in page
  says «تسجيل الدخول إلى بصير», offers a language switch and tells users without password reset to contact the
  administrator; Arabic dates are numeric.
- `brand.css`/`ef-chat.css`: Arabic alignment (model menu, marketplace, history groups), inline code direction, sign-in
  notice on phones, 48rem reading width, EF temporary-chat colour, 44 px composer targets, 12 px minimum text, red
  delete, EF focus ring, files date column; misleading settings, the message navigator and history icons hidden.
- `ar.json`: clearer sign-in and provider errors, «اسأل بصير لايت» in the composer, consistent search labels.

### Fixed — full platform audit: functional, performance and UX (#120)

- Audit of the built platform (API 48 checks, every UI feature in Arabic/English on phone and desktop, 10–60 concurrent
  users, 414 chats, 200-message threads, axe on every screen); ranked findings and owner decisions on #120.
- The parameters panel's web search and Responses API switches no longer break every reply of a chat (`dropParams` for
  both Qwen endpoints; `mock_chat.py` M48).
- Patch 0015: /register and /forgot-password return to sign-in while both are off (the reset page claimed an e-mail
  was sent); unknown addresses open a new chat instead of the technical error page; Arabic messages are edited right to
  left; agent chats name the agent on the model button; dialogs mirror in Arabic with a translated close label; dates
  in Arabic. The parameters panel no longer mentions ChatGPT.

### Changed — speed and weight measured; branded first paint; three font weights; LibreChat upgrade check (#118)

- Measured on the built Railway client, locally: Lighthouse accessibility and best practices 100, performance 54
  (slow-4G phone) / 77 (desktop); repeat visits load from the service worker (18 KB from the network).
- A «بصير» loading screen replaces the blank page while the app loads (first paint on a slow phone 12.1 → 6.8 s,
  desktop 2.3 → 1.2 s, repeat visit 2.0 → 0.3 s; patch 0014). Aktiv Grotesk loads the guide's three weights, not four
  (about 420 KB less): sign-in to composer on a slow phone 4.9 → 3.6 s.
- `scripts/upgrade/librechat-upgrade-check.sh` checks any upstream tag or commit (patches, translation keys, assets,
  Node image, config version, ADR-0012) without changing the repository; runbook `docs/operations/librechat-upgrade.md`.

### Changed — phone chat like ChatGPT: coloured user bubble, EF-branded replies, solid top bar, PWA bar (#115)

- The user's message is an EF blue bubble on the end side (left in Arabic); on touch screens its actions appear on tap.
- Replies carry the EF identity: blue model name and headings, EF link blue, blue list markers, warm-grey quotes with a
  green bar, blue-tinted inline code and table headers. Fixed: list numbers and bullets were missing in Arabic replies.
- Phone shell: a solid white top bar with borderless buttons, a floating rounded composer, and a drawer that leaves a strip
  to tap closed; the system bar is white (theme colour, iOS status bar). Patch 0013, `assets/ef-chat.css`.
- Accessibility: code blocks that scroll sideways take keyboard focus; the collapsed desktop side panel is inert.

### Changed — model names: «بصير لايت» by default, then «بصير بلس» and «بصير برو» (#112)

- Owner decision: the fast model `qwen3.8-flash` is the default as «بصير لايت»; `qwen3.7-plus` is «بصير بلس» and
  `qwen3.8-max` with thinking is «بصير برو», listed lightest first. Spec ids `baseer-lite`, `baseer-plus`,
  `baseer-pro`; older chats keep their model. Help page, docs and `mock_chat.py` M39/M41 follow.

### Changed — production home page, full side menu, light mode only, friendlier EF colors (#108)

- Home page like ChatGPT/Claude: greeting and a centred composer, no starter cards and no line under the greeting;
  production wording («لا تُدخل معلومات سرية أو بيانات شخصية») instead of "development/synthetic" lines.
- Side menu (owner decision): agents with their marketplace, skills, memories (automatic memory agent on `qwen3.8-flash`,
  `mock_chat.py` M47) and
  model parameters are back, shared inside the platform, never public; a short label under each icon. MCP, web search,
  code, file search and actions stay off (each needs its own decision). `mock_chat.py` policy checks follow, plus M46.
- One light appearance (dark and system modes open light; high contrast stays); cool EF-blue tints for side surfaces,
  user messages in the lightest primary blue, a blue focus outline (patch 0012).
- Accessibility fixes found by the QA (axe 0 violations): composer tools button name, marketplace tabs and cards,
  memory switch; Arabic: «الوكيل» instead of «العميل», «الذاكرة», «منشئ الوكلاء».

### Changed — QA round: faster first load, offline page, PWA manifest, short screens (#105)

- Full QA of the web client: accessibility (axe, WCAG 2.2 AA), 320–1920 px, task flows, PWA and throttled phone loads.
- First load: the diagram library no longer loads on every page (a chunking defect pulled shared modules into it);
  initial JavaScript −33%, first paint on a slow phone 16.5 s → 11.6 s. Pre-built brotli files are served.
- The service worker caches large on-demand chunks on first use; an Arabic/English offline page replaces the browser
  error (PROVISIONAL text); the manifest gets a description, a 512 px icon and a «محادثة جديدة» shortcut (patch 0011).
- Short phone screens and an open keyboard keep the composer in view; dark-mode code contrast meets 4.5:1.

### Changed — UX audit wave 2: settings that work, retry on errors, help page, prompt wording (#103)

- Settings show only what works here: no memory switch with memories off, no shared links, no key revocation, no
  agent-tool switches (patch 0010).
- A failed reply gets a labelled «إعادة المحاولة» button instead of feedback, fork and read-aloud actions.
- Phones: the trust notice now shows on the welcome screen (upstream hides the footer below 640 px).
- «المساعدة» ← «دليل الاستخدام» opens an EF help page «كيف أستخدم بصير» on the same origin (`HELP_AND_FAQ_URL`, PROVISIONAL
  text).
- Prompt library renamed «النصوص الجاهزة» (glossary updated); «بادئة الأمر» becomes «تعليمات مخصصة».

### Changed — UX audit wave 1: mixed-direction replies, RTL tables, trust notice (#100)

- UX audit against ChatGPT, Claude, Qwen and DeepSeek (18 findings); wave 1 fixes what needs no owner decision.
- Replies: each paragraph, heading and cell takes its own direction, so English lines inside Arabic replies keep their
  punctuation; tables have one continuous border in both directions and their own direction (patch 0009).
- Trust notice under the composer (`CUSTOM_FOOTER`, PROVISIONAL wording); `mock_chat.py` M37 checks it.
- Translation fix: «حفظ المسودات محلياً»; RTL menu icon spacing.

### Changed — model selector in the composer, panel open by default, RTL sign-in and titles (#97)

- The model selector moves from the header into the composer («بصير ▾», menu opens upward, no search box).
- The conversation panel opens by default on desktop, also for browsers that had saved a collapsed state.
- Sign-in in RTL: brand panel on the left, form on the right; conversation titles no longer lose their start in RTL
  (the build compiled `text-align: start` to `left`).
- Investigation against upstream defaults: the only hidden sidebar or header items are Memories (#39), Presets and
  multi-conversation (#87), all by earlier decisions. Patch 0008.

### Changed — EF brand across the whole platform (#94)

- Sign-in: an EF brand panel in primary blue with the white logo, «بصير», a tagline and the synthetic-data note, and the
  guide's original radial graphic; a side panel from 1024 px, a band on smaller screens.
- Aktiv Grotesk SemiBold added (original file) for weight 600; headings use Bold.
- Primary actions in brand blue in light and dark: send button, default buttons, switches, checkboxes, confirm
  dialogs and the active-chat marker. Generated avatars use EF blues.
- The EF logo heads every side panel; starter cards are white with a brand-blue hover; dark-mode sign-in fields no
  longer show their labels in a darker box.
- Patch 0007; the Railway Dockerfile now applies patches in order and fails on the first one that does not apply.

### Changed — UX phase 3: Environment Fund brand in the web client (#92, D-04 #7)

- Owner decision on 2026-10-20: use the EF brand guideline assets (version 01, November 2024) on the owner's responsibility.
- New `infrastructure/common/client/brand/`, applied by `build.sh`:
  - `brand.css`: palette colors in light and dark mode, every text pair ≥ 4.5:1;
  - Aktiv Grotesk, original OTF files unmodified because the files forbid modification; the hosting licence is an
    owner exception still to be confirmed;
  - logos: horizontal blue and white;
  - icons: the white symbol centered on the primary blue for the favicon, app and PWA icons, and «بصير».
- Patch 0006: a dark-mode login logo at 64 px; Aktiv Grotesk leads the font stack; app name, title and description
  «بصير | صندوق البيئة».
- `librechat.yaml`: the three model options show the «بصير» icon (`iconURL`).
- Checks: `mock_chat.py` 45/45; Playwright screenshots in AR light and dark, phone and desktop, and EN.

### Changed — UX phase 2: fully Arabic web client on Railway (#89, ADR-0013)

- The Railway image builds the LibreChat web client from the pinned upstream commit (tag v0.8.8) and replaces
  `/app/client/dist` only; the server stays the official image. New `infrastructure/common/client/`:
  - `ar.json`: the 2,367 missing strings, Arabic plural forms, and 32 corrected upstream strings (Upload «رفع», Prompt «أمر»,
    Fork «تفريع», five stale translations, a placeholder text);
  - five patches (42 added and 20 removed lines): joined letters in the greeting (B-04), `dir=auto` message box, LTR code
    blocks, RTL marker and switches, localized «New Chat» and ARIA names, Arabic as the default language, settings by
    name and mirrored;
  - `merge-locale.mjs`, which fails the build on stale keys, mismatched placeholders or less than 100% coverage.
- Proof and checks:
  - without our changes the build reproduces the official client byte for byte (366/366 files);
  - `railway_checks.py` accepts digest-pinned named build stages (new negative test N20, 20/20);
  - `railway-emulation.sh` gains `RAILWAY_EMULATION_LIBRECHAT_IMAGE` and passes 31/31 on the new image;
  - Playwright before/after: visible English UI text goes from 189 strings to 0, and the first visit opens in `ar/rtl`.
- The glossary becomes the terminology and style guide; the translation values live only in `ar.json`.

### Changed — UX phase 1: ChatGPT-style simplified chat shell by configuration (#87)

- `librechat.yaml` only, no brand assets (#7). Flat model menu (no spec `group`) and a landing screen with
  «كيف أساعدك اليوم؟», a per-option line carrying «استخدم بيانات اصطناعية فقط» and four Arabic starters per option
  (self-contained, ≤ 56 characters to fit two lines at 320 px). Hidden: model parameters, presets, multi-conversation
  compare (`MULTI_CONVO` role permission) and the context-usage indicator. Checked by `mock_chat.py` M45 (45/45) and
  Playwright screenshots of a local stack (Arabic RTL, 390/320 px and desktop). Upstream English strings remain (phase 2).

### Changed — employee model lineup: three named Qwen Cloud models (#37, #5)

- Owner-approved recommendation 2026-10-20, replacing "every model of the account": «بصير» `qwen3.7-plus` (default),
  «بصير السريع» `qwen3.8-flash` and «بصير للتحليل العميق» `qwen3.8-max`. Two endpoints on the same account because
  `enable_thinking` is per endpoint (off for the first two, on for Max, whose titles go to the fast model via
  `titleEndpoint`); fixed lists (`fetch: false`); `interface.modelSelect: false` shows only the three specs. Legacy
  aliases (`qwen-plus`) and models with retirement notices are not offered. `mock_chat.py` now points the real Qwen
  endpoints at the mock and checks the lineup (M39–M44).

### Changed — Qwen Cloud endpoint and every model of the account (#37, #5)

- Owner decision 2026-10-20: the owner's Qwen Cloud pay-as-you-go account (`sk-ws-` key, set in Railway by the owner)
  with all of its models. `librechat.yaml`: base URL `https://maas.qwencloudapi.com/compatible-mode/v1` (Qwen Cloud
  docs for `sk-ws-` keys) and `models.fetch: true`, so the model menu lists what the account offers; a five-model
  `default` list is the fallback. `qwen-plus` stays the default spec «بصير». Subscription keys (`sk-sp-`, Coding/Token
  Plan) are not usable: their terms exclude application backends. Watched path: merging redeploys Railway `dev`.

### Added — Qwen `qwen-plus` as the first approved provider, by configuration only (#37, R0.2)

- Owner decision OD-01 (#5, 2026-10-20): Qwen via Alibaba Cloud Model Studio, model `qwen-plus`, synthetic data only.
  `librechat.yaml`: custom endpoint `Qwen` with `apiKey: '${QWEN_API_KEY}'`, a static model list (`fetch: false`),
  initial `maxRetries: 1` / `timeout: 20000`, and a single model spec «بصير» (`enforce: false`). `railway.ts` declares
  `QWEN_API_KEY: preserve()` (the owner sets it in the Railway dashboard); Compose takes it as an optional `.env` value.
  `railway_checks.py` requires it as a secret (negative test N19); `mock_chat.py` merges its mock endpoints into the
  new `endpoints.custom` list. Watched path: merging redeploys Railway `dev`; the live chat waits for the key.

### Changed — repository slimming closed: before → after (#75, PRs #76–#82)

- Tracked files 149 → 131 (working tree 2.2 MB → 0.85 MB); screenshots 28 → 0; `project/` 12 files → 3; mandatory
  reading per agent session ~106 KB (7 docs) → 24 KB (AGENTS, CURRENT_STATE, START_HERE); CURRENT_STATE 40 KB /
  163 lines → 8.3 KB / 60 lines (budget-enforced); Markdown lines over 400 characters outside history/ADRs 111 → 0
  (`prose`-enforced); files to touch for a state change 10–26 → 1–3; the ten documented contradictions fixed.
  Markdown total 598 KB / 66 files → 605 KB / 71 files because history was moved, not deleted (live docs 431 KB,
  `docs/history/` 174 KB): the ≤ 450 KB target was not met. No watched Railway path changed; no deployment.

### Changed — test harness: shared `tests/lib.sh` and a `mockchat` package (#75)

- `tests/lib.sh` (log/check/summary and the PASS/FAIL counters) is sourced by `compose-stack.sh`,
  `railway-manual-deploy.sh` and `negative-checks.sh` instead of three copies; `railway-emulation.sh` is unchanged.
  `tests/integration/mock_chat.py` stays the entry point and now runs the `tests/integration/mockchat/` package
  (harness, client, checks_chat, checks_policy, checks_failures); check ids, descriptions and order are unchanged.
  Verified by running every suite before and after with byte-identical PASS lines (`smoke.yml` watches `tests/lib.sh`).

### Changed — one owning document per fact, phone-readable lines, `prose` check (#75)

- `delivery-governance.md` archived to `docs/history/planning-2026-10-19/`; its living rules (planning chain, Definition of
  Ready, Issue states, responsibilities, reporting) merged into `definition-of-done.md`. ADR-0009/0010/0011/0012 are explained
  only in their ADRs; README, CONTRIBUTING, SECURITY, the validation README, `run-all.sh` and the testing strategy cite them.
- `railway.md` §3 first-deploy log moved to `docs/history/railway-first-deploy-2026-10-19.md`; §6 and the README status
  tables now point at `CURRENT_STATE.md`. Every Markdown line over 400 characters outside code was split or turned into a
  list (28 lines in 11 docs; the vulnerability register §2 is one section per finding); `repo_checks.py prose` enforces it
  (history and ADRs exempt). This CHANGELOG is condensed to a few lines per entry; details stay in the PRs.

### Changed — agent policy files carry no live status; documentation rules extended (#75, PR #80)

- `AGENTS.md`: no Issue statuses in the session protocol or release governance; five documentation rules added (no live
  status in policy/reference docs, history only in Git/CHANGELOG/Issues/`docs/history/`, one owning document per fact,
  400-character lines, no screenshots in the tree, size budgets). `CLAUDE.md` keeps only the entry pointer; the PR template
  and `scripts/validate/README.md` updated.

### Changed — `project/` consolidated to three documents; history archived (#75, PR #79)

- `project/` = `START_HERE.md`, `CURRENT_STATE.md` (snapshot, budget-enforced) and `ROADMAP.md` (R0.x outcomes and exit
  gates, M0–M8, tag policy, execution order). The old state ledger, `PRODUCT_ROADMAP`/`DELIVERY_PLAN`/`ISSUE_MAP`/
  `RELEASE_PLAN` (PR #61), the five delivery reports, the closed M0/M1/M1.1 checklists and DoD §4 moved with `git mv` to
  `docs/history/` behind an index. `repo_checks.py budgets` (CURRENT_STATE ≤ 10 KiB / 80 lines, START_HERE ≤ 6 KiB / 60 lines).

### Changed — design audits separated from standards; screenshots leave the tree (owner decision, #75, PR #78)

- `docs/design/audits/` holds the two audit reports (matrix §4 now one subsection per surface); standards and glossary stay
  in `docs/design/`. All 28 screenshots (1.05 MB) removed; every reference is a permalink to commit `86d6546`.
  `ux-standards.md` §6: screenshots go into the PR or Issue, never the tree.

### Removed — Windows Docker Desktop path (owner decision, #75, PR #77)

- `scripts/windows/efaiw.ps1`, `tests/smoke/windows-helper.sh` and the Docker Desktop section of `windows-local.md` removed:
  the approved Windows path (D4) is Ubuntu WSL2 + Docker Engine (`compose-stack.sh local`). Owner-approved exception to
  ADR-0011 item 5, recorded in ADR-0008 and ADR-0011.

### Fixed — stale and contradictory statements after ADR-0010/ADR-0012 (#75, PR #76)

- `deployment.md`, `railway.md`, `vulnerability-register.md`, `cve-remediation-plan.md`, `data-flow.md` and the headers of
  `railway-deploy.sh`/`railway.ts` describe the current state (autodeploy, R-01–R-04 remediated, no temporary acceptance);
  the "manual-only" path is named "emergency/rollback"; unmaintained "آخر مراجعة" rows removed from 14 docs.

### Verified — ADR-0012 deployed on Railway `dev` (#16, PR #73)

- `main@6ffb954` auto-deployed librechat `afccdaa6` SUCCESS (2026-10-19T21:55Z): tarballs OK by sha256, both guards passed,
  start log healthy. R-01–R-04 Remediated on Railway `dev`, R-05 Not affected; no temporary SC-18 acceptance remains.

### Security — ADR-0012 patch layer in the Railway LibreChat image; R-05 Not affected (#16)

- Owner decisions 2026-10-19: ADR-0012 Accepted; R-05 (CVE-2025-68121, gosu) Not affected (`crypto/tls` not linked).
- `librechat.Dockerfile`: one `RUN` layer updates handlebars 4.7.10 (R-01/R-02), proxy-addr 2.0.8 (R-03) and npm 11.19.1
  (R-04) from sha256-pinned tarballs with a build-time exit guard; Compose images unchanged (upstream as is).

### Added — remediation plan for the five CRITICAL findings (#16, SC-18)

- `docs/security/cve-remediation-plan.md` and ADR-0012 (then Proposed): upstream status verified 2026-10-19 (R-01–R-03 fixed
  only in LibreChat `main`, R-04 unfixed, R-05 will not be fixed upstream). Spike: Trivy 0 CRITICAL / 22 HIGH on the patched
  image, `mock_chat.py` 38/38, `railway-emulation.sh` 31/31.

### Added — Arabic/RTL/accessibility audit, glossary and tested upstream fixes (#44, R0.3, PR #70)

- `arabic-rtl-audit.md`: 70 screenshots + axe-core on the configured stack; 13 defects rooted in upstream source (B-04
  unjoined Arabic greeting, B-07 LTR composer, B-13 RTL code blocks, B-17 settings, ARIA). Proposed L4 fix set (21 lines in
  6 files) verified locally only. `arabic-glossary.md`: 158 proposed strings. `mock_chat.py` M38.

### Changed — no upstream branding leaks in the UI (#43 part A, PR #69)

- `CUSTOM_FOOTER=` (empty) and `HELP_AND_FAQ_URL=/` in `librechat.env`/`railway.ts`; `interface.buildInfo: false` in
  `librechat.yaml` (also hides build info from unauthenticated `/api/config`). Hidden, not replaced (#7).
  `compose_checks.py` accepts exactly `HELP_AND_FAQ_URL=/` (negative test N18); `mock_chat.py` M37.

### Changed — least-privilege AI defaults and fast provider failures (#39, R0.2, PR #68)

- `librechat.yaml`: `interface` permissions (object form, USER and ADMIN) switch off agents/builder/actions, MCP, skills,
  memories, web search, code execution, file search, API keys, marketplace, sharing and schedules; `endpoints.agents`
  `capabilities: []`, `disableBuilder: true`, `maxProviderErrorChars: 0`. Watched input: Railway `dev` redeployed.
- `mock_chat.py` 36 checks (M22–M36: 403 on guarded routes, smuggled tools dropped, 503/429/401/404/timeout timings,
  Stop during retry, policy re-applied after restart). `docs/architecture/ai-safe-defaults.md`; SC-21 added.

### Added — LibreChat v0.8.8 branding surface audit (#42, R0.3, PR #66)

- `brand-implementation-matrix.md`: 14 surfaces with current behaviour, ADR-0006 level, upstream source, upgrade risk and
  acceptance criteria; Arabic coverage 22.6%; no surface requires a fork; 12 upstream-PR gaps. Visual baseline of 12
  screenshots (then in the tree) with defects B-04..B-08. Analysis only; official identity #7.

### Added — deterministic mock-LLM chat regression (#38, R0.2, PR #65)

- `tests/integration/mock_chat.py` (21 checks): real Compose stack + test overlay with a deterministic OpenAI-compatible
  mock on the internal network — closed registration, login, model listing, streamed AR/EN replies, determinism, history,
  persistence, cancellation, provider/network errors, isolation, secret hygiene. 21/21 on `f4a21fb`; not a live provider.

### Governance — formal quality gates are production-only (ADR-0011, 2026-10-19, PR #64)

- Owner decision: no mandatory per-PR quality gate during development, testing and demo; verification is task-appropriate.
  Formal gates, independent review and approvals are enforced before Production (DoD §2, #58). Secrets, synthetic-only
  Railway, SC-18, exposure, spend, Entra and production approval unchanged; no workflow or test removed. #60 superseded
  (`run-all.sh` for PRs #61/#63 stays NOT RUN). `main` protection re-checked: rulesets `[]` → owner action (#3).

### Quality / governance — foundation milestone closure audit (2026-10-19, PR #63)

- Source-level audit: M0/M1 merged with historical cloud-session evidence; M1.1 and R0.1 acceptance remain partial (report
  now in `docs/history/reports/`). Dependabot PR #19 closed unmerged (a Compose-only MongoDB bump breaks image/digest
  parity) → #62. No new deployment; final-SHA `run-all.sh` for PR #61 NOT RUN.

### Approved planning — Baseer product delivery roadmap v1.0 (#60, PR #61)

- Owner approved R0.1 → R0.2 → R0.3 → R0.4 → R0.5 → R0.6 → R1.0 (planning IDs, not tags or deployed features). Added
  `PRODUCT_ROADMAP`, `DELIVERY_PLAN`, `ISSUE_MAP`, `START_HERE` and delivery governance (since archived to `docs/history/`);
  Epics #31–#36, execution Issues #37–#58, native Project/Milestones tracked as #59. Documentation only.

### Changed — Railway `dev` autodeploys from `main` (ADR-0010)

- Both services track `faenazi/ef-ai-workspace` `main` (Wait for CI off; watch paths = each Dockerfile and its COPY sources),
  replacing manual-only deploys (#16 D2). Variables still need `railway config apply`; `railway-deploy.sh` is the fallback.
  Applied on Railway `dev` 2026-10-19: first autodeploy of `60b93e0` SUCCESS for both services (#15).

### Deployed — working name on Railway `dev` (#27, #15)

- `APP_TITLE` «بصير | صندوق البيئة» applied with `config plan/apply` (2026-10-19); both services redeployed SUCCESS (RW13).

### Changed — provisional product name (D-04, #7, PR #27)

- Shared `APP_TITLE` set to «بصير | صندوق البيئة» (the owner's changeable working name, 2026-10-19); what it does and does
  not change in v0.8.8 documented. Institutional name and identity approval remain open.

### Added — public link and first local admin on Railway `dev` (#15)

- `https://librechat-dev-3477.up.railway.app` generated under the then temporary SC-18 acceptance; registration opened
  briefly for the owner's first (ADMIN) account, then closed again with `config apply`.

### Security — temporary owner acceptance of the five CRITICAL findings (SC-18, #16)

- Fresh Trivy scan before exposure (same results as 2026-10-18); the owner accepted R-01–R-05 separately for Railway `dev`
  until 2026-11-18 or an upstream fix (later superseded by ADR-0012 and the R-05 classification).

### Changed — development-phase delegation to the agent (ADR-0009)

- Owner instruction 2026-10-19: the agent merges its own PRs and runs `config apply`, secrets and deploys in Railway `dev`
  only, recording each on the Issue; exposure, other environments, spend, DNS, real data and production stay with the owner.

### Verified / Fixed — LibreChat and MongoDB on Railway `dev` without a public domain (#15, PR #22)

- First authorized run: `apply`, secrets and the mongodb deploy succeeded; librechat failed its healthcheck (`DOMAIN_*` =
  `https://` without a domain → `Invalid URL`). `librechat-start.sh` now falls back to the private address (emulation R33);
  `a9fcacf` then deployed SUCCESS with `/health` passing; RW1, RW3, RW4, RW10, RW11 verified on target.

### Added — first read-only `railway config plan` evidence (#15)

- Owner set up the Railway account, spending limits, an empty project and a `dev` environment (owner-reported); the first
  `railway config plan` (CLI 5.70.0): `4 to add, 0 to change, 0 to destroy`; nothing applied.

### Changed — D2 revised: no GitHub Actions; Railway deploys manual-only (#16, PR #18 comment)

- GitHub Actions not used (owner decision); the DoD then required a manual quality gate per PR (replaced by ADR-0011) and
  `railway.ts` services had no deployment source (replaced by ADR-0010). Added `railway-deploy.sh` with
  `railway-manual-deploy.sh` (D01–D08) and `tests/policy/negative-checks.sh` (16 cases); CI-EX-03 superseded; workflows kept.

### Changed — owner decisions D1–D5 implemented (#16)

- ADR-0008 Accepted (architecture only); SC-18 container-security policy approved with the five CRITICAL findings open;
  `railway_checks.py` enforces D3 (region `europe-west4-drams3a`, 2 vCPU/2 GB and 1 vCPU/1 GB, 5 GB per volume);
  `windows-local.md`: Ubuntu WSL2 + Docker Engine preferred (D4).

### Changed — owner review of PR #18

- `vulnerability-register.md`: every CRITICAL with reachability evidence and a proposed disposition. `railway-secrets.sh`:
  verified AES-256 recovery copy, `--from-recovery`, `--prompt`, explicit `--accept-no-recovery`; the emulation rehearses
  restore and key-drift detection (R26–R32). Railway volumes 5 GB each; config propagation via plan/apply (RW13).

### Changed / Added — M1.1 multi-environment hosting (ADR-0008, #15, PR #18)

- Coolify superseded (ADR-0004 → Superseded; #6, #13 closed). `infrastructure/coolify/` split into `infrastructure/common/`
  (`librechat.yaml`, `mongo-init/`, `librechat.env`) and `infrastructure/compose/` (`compose.yaml`, `compose.local.yaml`,
  `compose.onprem.yaml` + Caddy 2.11.7 HTTPS). Images and digests unchanged; file logs fixed to `/app/logs`.
- Railway IaC `.railway/railway.ts` (SDK `railway@3.16.0`): private MongoDB, one volume per service, `/health`, secrets as
  `preserve()`; derived images in `infrastructure/railway/` with start guards and privilege drop. Scripts `new-env.sh` and
  `railway-secrets.sh`; checks `railway_checks.py` and `image-scan.sh` (Trivy, report-only); smoke `compose-stack.sh
  local|onprem` (37/43) and `railway-emulation.sh`; docs for the three environments; SC-18–SC-20.

### Added / Fixed — M1 LibreChat Platform Foundation (#2, PR #12)

- Compose stack: LibreChat v0.8.8 + MongoDB 8.0.34 pinned by digest, no published ports, MongoDB `--auth` with a
  least-privilege user, healthchecks, named volumes, `${VAR:?}` secrets, registration/social login/password reset/shared
  links disabled, `SEARCH=false` (OD-02), scheduled chats off, `cap_drop: ALL`; `librechat.yaml` 1.3.17 with no endpoint.
- `backup.sh`/`restore.sh` (SHA-256 verified), `compose_checks.py`, a 35-check smoke test, ADR-0007 Accepted (#11),
  CI-EX-02 approved for PR #12 only. Owner review: repository bind-mount preservation, `/app/data` in backups.

### Added / Fixed — M0 Repository Foundation & Governance (PR #9)

- `AGENTS.md` shared policy (imported by `CLAUDE.md`); product, architecture, design, security, operations and quality
  docs; ADR-0001…0006; ROADMAP/CURRENT_STATE/RELEASE_PLAN; development skills; GitHub governance (issue forms, PR template,
  CODEOWNERS, Dependabot); CI/Security workflows (SHA-pinned, least privilege); `.claude/settings.json` secret-read denies;
  `run-all.sh`; CI-EX-01. Review fixes: `.env.example` readable, push-deny rules, `.gitignore`, `repo_checks.py` link checks.

### LibreChat baseline

- Reference version documented: v0.8.8.
