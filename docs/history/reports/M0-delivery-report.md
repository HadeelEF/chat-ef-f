# تقرير تسليم M0 — Repository Foundation & Governance

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس حالة حالية ولا سياسة.** الحالة الحية: [project/CURRENT_STATE.md](../../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](../README.md).

| الحقل | القيمة |
|---|---|
| التاريخ | 2026-10-17 |
| الفرع | `feature/m0-repository-foundation` (من `main` @ `11e80e2`) |
| المنفّذ | Claude Code Cloud |
| النتيجة | التنفيذ مكتمل في الـ PR ومُختبر في جلسة السحابة. التحقق المستقل عبر GitHub CI غير متاح، ومقبول بديله لـ M0 فقط وفق الاستثناء المعتمد **CI-EX-01**. **M0 لا يُغلق قبل اعتماد مالك المشروع ودمج PR #9** |
| مراجعة ثانية | 2026-10-17 — إعادة فحص كاملة، مراجعة مستقلة، إصلاح العيوب، وتوثيق CI-EX-01 (القسم 7) |

## 1. تحليل الفجوات (Gap Analysis)

### 1.1 حالة المستودع الأصلية (متحقق منها)

| البند | الدليل |
|---|---|
| ملفان فقط: `README.md` (سطر عنوان) و`CLAUDE.md` (ميثاق المشروع، 48 سطراً) | `git ls-files` على `11e80e2` |
| commitان: "Initial commit" و"docs: establish Claude Code project charter" | `git log` |
| فرع واحد `main`، **غير محمي** | GitHub API `list_branches` → `protected: false` |
| لا Issues، لا Pull Requests، لا GitHub Actions | GitHub API |
| تعارض: الميثاق يشير إلى `docs/ROADMAP.md` غير الموجود، وترقيم مراحل (M1–M5) يختلف عن موجّه M0 (M0–M8) | `CLAUDE.md` الأصلي |
| معلومات مهمة يجب الحفاظ عليها: المهمة، القيود التشغيلية، 8 مبادئ معمارية، بوابات الجودة، نطاق M1 | `CLAUDE.md` الأصلي |

### 1.2 مقابل الهدف

| المجال | قبل M0 | بعد M0 | ملاحظات |
|---|---|---|---|
| README احترافي | MISSING | COMPLETE | عربي، حالة صادقة، تنقل |
| سياسة وكلاء مشتركة (AGENTS.md) | MISSING | COMPLETE | محتوى الميثاق محفوظ ومنقول إليها |
| CLAUDE.md | EXISTING (ميثاق) | COMPLETE | `@AGENTS.md` + تعليمات Claude فقط |
| توثيق المنتج (رؤية، نطاق، BRD، FR، NFR) | MISSING | PARTIAL (Draft) | معايير القبول والأهداف الكمية تحتاج اعتماداً |
| المعمارية و ADRs | MISSING | COMPLETE (baseline) | 6 ADRs مقبولة؛ HLD مقترح |
| التصميم والهوية | MISSING | PARTIAL | **BLOCKED** على الأصول الرسمية (#7) |
| الأمن | MISSING | PARTIAL | خط أساس + سجل ضوابط؛ الاعتماد الرسمي غير متوفر |
| التشغيل | MISSING | PLANNED | خطة + هيكل runbook غير مختبر |
| الجودة (DoD، الاختبار، AI evals) | MISSING | COMPLETE (baseline) | — |
| إدارة المشروع (ROADMAP، CURRENT_STATE، RELEASE_PLAN) | MISSING | COMPLETE | — |
| Backlog في GitHub Issues | MISSING | COMPLETE | Issues #1–#8، #10 (PR #9) |
| قوالب GitHub، CODEOWNERS، Dependabot | MISSING | COMPLETE | — |
| CI وفحص الأسرار | MISSING | PARTIAL | مُنفّذ و Tested (cloud session)؛ تشغيل GitHub **NOT VERIFIED** (#10، CI-EX-01) |
| مهارات التطوير | MISSING | COMPLETE | 3 مهارات، محمولة لـ Codex |
| فصل مهارات المنصّة | MISSING | COMPLETE (هيكل) | `ai/README.md`؛ لا أصول بعد (M5) |
| حماية الفرع | MISSING | BLOCKED | إجراء مالك المشروع (#3) |
| Compose / LibreChat | MISSING | PLANNED | M1 (#2) |

## 2. الهيكل المنفّذ والفروقات عن المقترح

```text
.
├── README.md  AGENTS.md  CLAUDE.md  CONTRIBUTING.md  SECURITY.md  CHANGELOG.md
├── .gitignore  .gitattributes  .editorconfig  .yamllint.yaml
├── .agents/skills -> ../.claude/skills        (رابط رمزي لاكتشاف Codex)
├── .claude/settings.json
├── .claude/skills/{implement-feature,review-changes,verify-release}/SKILL.md
├── .github/CODEOWNERS  PULL_REQUEST_TEMPLATE.md  dependabot.yml
├── .github/ISSUE_TEMPLATE/{feature.yml,bug.yml,config.yml}
├── .github/workflows/{ci.yml,security.yml}
├── ai/README.md
├── docs/README.md
├── docs/product/{vision,scope,BRD,functional-requirements,non-functional-requirements}.md
├── docs/architecture/{overview,HLD,data-flow}.md + adr/{README,0001…0006}.md
├── docs/design/{brand-guidelines,design-system,ux-standards}.md
├── docs/security/{security-baseline,data-handling}.md
├── docs/operations/{deployment,runbook}.md
├── docs/quality/{definition-of-done,testing-strategy}.md
├── project/{ROADMAP,CURRENT_STATE,RELEASE_PLAN}.md + reports/M0-delivery-report.md
└── scripts/validate/{repo_checks.py,requirements.in,requirements.txt,README.md}
```

| الفرق عن الشجرة المقترحة | السبب |
|---|---|
| `.agents/skills` (إضافة) | Codex يكتشف مهارات المستودع هناك فقط، ويتبع الروابط الرمزية (مصدر `codex-rs`) — نسخة واحدة بلا تكرار |
| `.yamllint.yaml` (إضافة) | إعداد صريح لفحص YAML الصارم |
| `docs/security/*`, `docs/operations/*` بأسماء محددة | ملفان مركّزان لكل مجال بدلاً من ملفات متعددة صغيرة |
| `project/reports/` (إضافة) | موقع دائم لأدلة التسليم والتحقق (سيناريو الاستمرارية) |
| `ISSUE_TEMPLATE/config.yml` (إضافة) | تعطيل Issues الفارغة وتوجيه البلاغات الأمنية |
| لم تُنشأ: `.claude/rules/`, `ai/{agents,skills,prompts,knowledge,evals}/`, `config/`, `integrations/`, `infrastructure/`, `scripts/operations/`, `tests/`, `assets/` | لا محتوى فعلي لها بعد — تُنشأ تدريجياً (الجدول في [docs/README.md](../../../docs/README.md#هيكل-المستودع-المستهدف-تدريجي)) |
| لا LICENSE | بتوجيه صريح — مستودع خاص |

## 3. نتائج التحقق (Validation Results)

> **مستوى الأدلة:** كل النتائج أدناه **Tested (cloud session)** — نفّذها الوكيل المنفّذ نفسه في جلسة Claude Code Cloud.
> هي **ليست** تحققاً مستقلاً عبر GitHub CI (انظر [مستويات الأدلة](../../../docs/quality/definition-of-done.md#مستويات-أدلة-التحقق)
> والاستثناء المعتمد [CI-EX-01](../ci-exceptions-2026-10.md#ci-ex-01--github-actions-غير-متاح-لمرحلة-m0)).

### 3.1 أدلة جلسة السحابة (Cloud-session evidence)

التشغيل: `scripts/validate/run-all.sh` (يكرر كل فحوصات `ci.yml` و`security.yml`)، Python **3.12.13** (نفس إصدار CI)،
أدوات بالـ hash من `requirements.txt`، actionlint 1.7.12 و gitleaks 8.30.1 مُنزّلة من روابط الـ workflows ومُتحقق من sha256.
commit المختبر: `681bfe19c5b2` (محتوى PR كامل)؛ إعادة التشغيل على رأس الـ PR النهائي مسجلة في تعليق على PR #9.

| الفحص | النتيجة | الدليل |
|---|---|---|
| `repo_checks.py`: required, forbidden, links (روابط + صور + مراسي), skills, agents, settings, requirements, adr, syntax | PASS (9/9) | مخرجات `run-all.sh` |
| `yamllint --strict .` (يتجاهل مسارات `.gitignore`) | PASS | — |
| `check-jsonschema 0.38.2`: workflows، dependabot، issue forms، issue config | PASS | built-in vendor schemas |
| مخطط `.claude/settings.json` | PASS | schemastore `claude-code-settings.json` |
| `actionlint 1.7.12` | PASS | sha256 مطابق لملف checksums الرسمي |
| `zizmor 1.31.1 --offline` | PASS | "No findings" |
| `gitleaks 8.30.1` — تاريخ git كامل + شجرة العمل | PASS | no leaks found |
| قواعد قراءة الأسرار (`.claude/settings.json`) — اختبار سلوكي | PASS | Claude Code **2.1.302** headless على fixture اصطناعي: `.env`, `.env.local`, `.env.production`, `sub/.env`, `sub/.env.staging`, `secrets/token.txt`, `tls.key`, `cert.p12` → DENIED؛ `.env.example` و`sub/.env.example` → READ_OK. الإعداد السابق في الـ PR أعاد `.env.example: DENIED` (العيب مُعاد إنتاجه ثم مُصلح) |
| قواعد منع الدفع الخطِر — اختبار سلوكي | PASS | نفس الأسلوب، 12 أمراً: كل force push (`--force`, `-f`, `--force-with-lease`, `+ref`) وكل دفع إلى `main` (`origin main`, `-u origin main`, `HEAD:main`) → BLOCKED؛ `git push -u origin feature/...` و`feature/main` → مسموح |
| تحميل `AGENTS.md` عبر `@AGENTS.md` واكتشاف المهارات الثلاث | PASS | جلسة Claude Code الحالية حمّلت التعليمات والمهارات |
| اختبارات سلبية (الفحوصات تفشل فعلاً) | PASS | رابط/مرسى/صورة مكسورة، رابط بعد fence متداخل، اسم مهارة خاطئ، FR مكرر، ADR ناقص، غياب `@AGENTS.md`، `.env.production` و`secrets/token` متتبعان، YAML تالف، إعداد يمنع `.env.example` → exit 1؛ token عشوائي → gitleaks exit 1؛ workflow غير آمن → zizmor exit 14 و actionlint exit 1 |

### 3.2 التحقق المستقل (Independent GitHub CI)

| الفحص | النتيجة | الدليل |
|---|---|---|
| `CI` و`Security` workflows على GitHub Actions | **NOT VERIFIED** | بعد آخر الدفعات يُرجع GitHub API صفر workflows/تشغيلات للمستودع (السبب غير قابل للتأكيد من بيئة التطوير). قبلها: الوظائف لم تبدأ (`runner_id: 0`)؛ annotation: "The job was not started because an Actions budget is preventing further use." — #10. مقبول لـ M0 فقط وفق CI-EX-01 |
| توافق Codex الفعلي | NOT RUN | لا بيئة Codex — #8 |
| Compose / حاويات | NOT APPLICABLE | لا بنية تحتية في M0 |

## 4. جاهزية التطوير بالذكاء الاصطناعي (سيناريو الاستمرارية)

**جلسة Claude Code جديدة:** تُحمّل `CLAUDE.md` ← `@AGENTS.md` تلقائياً؛ تتبع *Session start protocol*: `git status/log` ←
`project/CURRENT_STATE.md` (المرحلة، العوائق، **الأولوية التالية #2**) ← Issues/PRs المفتوحة ← Issue #2 ومتطلباته ←
مهارة `implement-feature` ← تحقق ← PR مسودة.

**جلسة Codex جديدة:** تقرأ `AGENTS.md` أصلياً (لا تقرأ `CLAUDE.md`)؛ نفس البروتوكول؛ المهارات عبر `.agents/skills`.
البديل إن لم تُكتشف المهارات: `AGENTS.md` يسمّي المهارات ومساراتها، فيقرأ Codex `SKILL.md` مباشرة.

## 5. الأعمال المؤجلة والمخاطر

| البند | النوع | المتابعة |
|---|---|---|
| ميزانية GitHub Actions تمنع تشغيل أي CI | عائق | #10 |
| حماية `main` غير مفعّلة — يمكن الدفع المباشر أو الدمج دون فحوصات | خطر | #3 |
| أدلة CI-EX-01 غير مستقلة (الوكيل نفسه كتب واختبر)، وسلوك GitHub الفعلي للـ workflows غير متحقق | خطر | #10 — تشغيل على `main` عند الاستعادة |
| قواعد منع الدفع في `.claude/settings.json` best-effort (مطابقة نصية لأوامر Bash؛ لا تمنع `git push` بدون وسائط على `main`) | خطر | الضابط الحقيقي حماية الفرع #3 |
| أهداف NFR الكمية، الأدوار، الاحتفاظ، الإطار التنظيمي غير معتمدة | قرار | OD-03/04/07، UR-06 |
| digests الصور سُجلت في 2026-10-17 وقد تتغير | خطر | إعادة التحقق في #2 |
| `validations.required` في نماذج Issues لا تُفرض في المستودعات الخاصة (توثيق GitHub) | قيد | موثق داخل النماذج |
| GitHub Advanced Security (dependency review، secret scanning المدمج) غير متاح/غير مفعّل للمستودع الخاص | قيد | gitleaks يغطي فحص الأسرار |
| فجوات LibreChat upstream (العربية، الهوية، التدقيق، CDN للـ Artifacts) | خطر منتج | M2/M4/M6 |

## 6. التراجع (Rollback)

M0 توثيق وإعدادات GitHub فقط، دون بنية تحتية: إغلاق الـ PR دون دمج، أو بعد الدمج `git revert` لـ merge commit عبر PR جديد.
Issues المنشأة (#1–#8، #10) يمكن إغلاقها بـ `not_planned`. استثناء CI-EX-01 ينتهي بإغلاق PR #9 دون دمج. لا بيانات ولا خدمات تتأثر.

## 7. المراجعة الثانية والاستثناء CI-EX-01

**القرار:** قرر مالك المشروع (2026-10-17) استخدام Claude Code Cloud مؤقتاً للتطوير والاختبار والتحقق دون اشتراط GitHub Actions
في المرحلة الأولى. سُجّل في #10 ووُثّق كاستثناء محدود النطاق (PR #9 فقط) في
[definition-of-done.md](../ci-exceptions-2026-10.md#ci-ex-01--github-actions-غير-متاح-لمرحلة-m0).
الـ workflows باقية دون تغيير؛ لا يُعطّل أو يُتخطى أي فحص؛ لا ينطبق على النشر أو وسم الإصدارات أو المراحل اللاحقة.

**مراجعة مستقلة** (وكيل مراجعة منفصل، قراءة فقط) — 0 Blocker، 3 Major، وعدة Minor/Nit. المعالجة:

| الملاحظة | الخطورة | المعالجة |
|---|---|---|
| `.claude/settings.json` يمنع قراءة `.env.example` | Major | مُصلح ومُختبر سلوكياً؛ فحص `repo_checks.py settings` يمنع التراجع |
| `.gitignore` يتجاهل مجلدات مخططة (`assets/brand/images/`, `tests/fixtures/data/`, `*.sql`) | Major | تثبيت مسارات بيانات التشغيل في الجذر و`infrastructure/`؛ حذف `*.sql`؛ إصلاح استثناء `secrets/README.md`؛ السماح بـ `.env.*.example` — مُتحقق بـ `git check-ignore` (12 مساراً) |
| قواعد منع الدفع قابلة للتجاوز (`-u origin main`, `HEAD:main`, `+ref`) | Major | قواعد wildcard موثقة ومُختبرة سلوكياً (12 أمراً)؛ موسومة best-effort حتى #3 |
| اعتماد CI-EX-01 بصياغة الوكيل | Major | تحديث نص #10؛ **تأكيد المالك النهائي = موافقته على PR #9** (مذكور في DoD) |
| yamllint يفحص مسارات متجاهلة (`.venv`) | Minor | `ignore-from-file: .gitignore` |
| تعليمات التثبيت على Python النظام (PEP 668) | Minor | venv في AGENTS.md و CONTRIBUTING.md و README التحقق |
| `repo_checks.py`: صور غير مفحوصة، fence متداخل، روابط `%20` | Minor | مُصلحة ومُختبرة سلبياً؛ الروابط المرجعية و HTML و setext headings غير مدعومة (موثق في الكود) |
| ادعاءات حالة مبالغ فيها (SECURITY.md، SC-01/02/03) | Minor | وسم `Tested (cloud session)` و"تشغيل GitHub غير متحقق" |
| قوائم Issues قديمة في التقرير؛ تنبيه نماذج Issues ناقص في `bug.yml` | Minor/Nit | مُصلحة |
| اختلاف مفردات الحالة في `security-baseline.md` | Nit | **مُبقى عمداً:** مقياس حالة الضوابط (Requirement → Planned → Implemented → Tested → Approved) مطلوب صراحة في موجّه M0 ومختلف الغرض عن حالة التنفيذ |

