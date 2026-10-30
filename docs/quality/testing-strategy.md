# استراتيجية الاختبار والتقييم (Testing & AI Evaluation Strategy)

| الحقل | القيمة |
|---|---|
| الحالة | الفحوصات الآلية في §1 منفّذة؛ المستويات اللاحقة Planned (§2)؛ نتائج التشغيل في [CURRENT_STATE](../../project/CURRENT_STATE.md) |

## 1. الفحوصات الآلية الحالية (M0 + M1 + M1.1)

| الفحص | الأداة | أين | يفشل عند |
|---|---|---|---|
| الملفات الإلزامية، ميزانيات الحجم، الروابط والمراسي، صحة JSON/YAML، طول الأسطر | `scripts/validate/repo_checks.py` | `ci.yml` | ملف ناقص، تجاوز ميزانية، رابط/مرسى مكسور، صيغة خاطئة، سطر > 400 حرف |
| بيانات المهارات (portable Agent Skills profile) والرابط الرمزي لـ Codex | `repo_checks.py skills` | `ci.yml` | name/description غير صالح، مفاتيح غير محمولة |
| قيود ملفات الوكلاء | `repo_checks.py agents` | `ci.yml` | غياب `@AGENTS.md`، تجاوز الحجم |
| تفرّد معرّفات المتطلبات وفهرسة ADR | `repo_checks.py requirements adr` | `ci.yml` | تكرار FR/NFR، ADR غير مفهرس أو ناقص الأقسام |
| ملفات ممنوعة (`.env`، مفاتيح، dumps) | `repo_checks.py forbidden` | `ci.yml` | تتبّع ملف ممنوع |
| قواعد قراءة الأسرار لوكلاء Claude Code (`.env.example` مسموح) | `repo_checks.py settings` | `ci.yml` | ملف سري غير ممنوع أو `.env.example` ممنوع |
| سياسة Compose (Windows + Ubuntu) — التفاصيل أدناه | `scripts/validate/compose_checks.py` | `ci.yml` (`compose-validation`) | أي خرق للسياسة |
| Railway IaC offline — التفاصيل أدناه | `scripts/validate/railway_checks.py` | `ci.yml` (`railway-iac`) | أي انحراف |
| اختبارات سلبية (25) — التفاصيل أدناه | `tests/policy/negative-checks.sh` | `ci.yml` (`railway-iac`) + `run-all.sh` | قبول أي إعداد مُضعَف |
| مسار نشر Railway للطوارئ والرجوع (8) — التفاصيل أدناه | `tests/smoke/railway-manual-deploy.sh` (CLI وهمي، بلا token) | `ci.yml` (`railway-iac`) + `run-all.sh` | أي فحص |
| Smoke — Compose local، Windows profile (37) — التفاصيل أدناه | `tests/smoke/compose-stack.sh local` | `smoke.yml` + جلسة السحابة | أي فحص |
| Smoke — Compose on-prem، Ubuntu profile (43) — التفاصيل أدناه | `tests/smoke/compose-stack.sh onprem` | `smoke.yml` + جلسة السحابة | أي فحص |
| محاكاة Railway (31 + 2 IPv6-only) — التفاصيل أدناه | `tests/smoke/railway-emulation.sh` | `smoke.yml` + جلسة السحابة | أي فحص |
| Integration — محادثة بنموذج وهمي حتمي (38) — التفاصيل أدناه | `python3 tests/integration/mock_chat.py [results-file]` | جلسة السحابة (Docker) | أي فحص |
| واجهة القائمة الجانبية v5 في المتصفح (135 فحصاً، [§11](concept1-interface-test-cases.md#11-القائمة-الجانبية-الخامسة-التخصيص-221)): حزمة الاختبار بالواجهة المبنية من `librechat.Dockerfile`، Playwright وaxe | `tests/ui/ui_stack.py up --image <tag>` ثم `node tests/ui/sidebar_v5.cjs <state.json>` | جلسة السحابة (Docker، Chromium) | أي فحص |
| معيار الأوضاع الثلاثة (33 سيناريو اصطناعي): offline بلا شبكة، وlive على Qwen Cloud ([model-benchmark.md](model-benchmark.md)) | `python3 tests/benchmark/model_benchmark.py [--live --key-file F]` (venv التحقق) | جلسة السحابة | offline: سيناريو أو طلب غير صالح أو انحراف عن التشكيلة المعتمدة؛ live: فشل استدعاء |
| فحص ثغرات الصور المثبتة (report-only) | `scripts/validate/image-scan.sh` (Trivy مثبت بـ sha256) | `image-scan.yml` | لا يفشل افتراضياً؛ `--fail-on` عند اعتماد سياسة |
| أسلوب YAML | `yamllint --strict` (`.yamllint.yaml`) | `ci.yml` | أي تحذير |
| مخططات إعداد GitHub | `check-jsonschema` (workflows، dependabot، issue forms) | `ci.yml` | مخالفة المخطط |
| سلامة الـ workflows | `actionlint` (binary مُتحقق بـ sha256) | `ci.yml` | خطأ في workflow |
| أمن الـ workflows | `zizmor --offline` | `security.yml` | ثغرة/سوء إعداد |
| فحص الأسرار (تاريخ كامل + شجرة العمل) | `gitleaks` (binary مُتحقق بـ sha256) | `security.yml` | اكتشاف سر |

**ما تغطيه الفحوصات الطويلة:**

- **سياسة Compose (`compose_checks.py`):** digest، لا منافذ في الأساس، نقطة دخول واحدة لكل profile (loopback محلياً، Caddy 80/443 في
  الموقع على frontend فقط)، MongoDB `--auth` على شبكة internal، healthchecks، `cap_drop: ALL`، أسرار `:?`، سياسة `librechat.env`
  (التسجيل الذاتي مغلق ADR-0024، روابط المشاركة خلف الدخول، `HELP_AND_FAQ_URL=/` حرفياً…)، Meilisearch على شبكة internal بمفتاح و`MEILI_ENV=production`،
  توافق `librechat.yaml` version، `.env.example` فارغ، `docker compose config`
  لكلا الـ profiles ينجح كاملاً ويفشل بلا أسرار.
- **Railway IaC (`railway_checks.py`، بلا token):** تقييم `.railway/railway.ts` بطريقة Railway CLI وبالـ SDK المثبت + `tsc`؛ ثلاث خدمات
  وvolume واحد لكل خدمة، نسخة واحدة، MongoDB وMeilisearch خاصتان (لا TCP proxy/نطاق؛ مفتاح Meilisearch في librechat مرجع فقط)، لا نطاق عام، `/health`، مصدر النشر = هذا المستودع فرع `main` دون
  Wait for CI وwatch paths = مدخلات الـ Dockerfile (ADR-0010)، أهداف D3، الأسرار `preserve()` فقط، سياسة = `librechat.env`، مساواة digest
  الـ Dockerfiles مع Compose (المرحلة الأخيرة؛ مراحل البناء مسمّاة ومثبّتة بالـ digest، ADR-0013)، منع `railway.json/.toml` (deprecated).
- **واجهة الويب العربية (ADR-0013، وقت البناء):** `merge-locale.mjs` يُفشل البناء على مفتاح غير موجود في الإنجليزية المثبّتة، أو قيمة
  تختلف عنها في المتغيرات/الوسوم/الأسطر، أو تغطية أقل من 100%؛ وتُطبَّق التعديلات بالترتيب ويُفشل البناء أي تعديل لا ينطبق (`git apply --check`).
- **الاختبارات السلبية (33):** كل حالة تُضعف ضابطاً واحداً في نسخة مؤقتة ويجب أن يرفضها الفاحص — فرع غير `main`/Wait for CI/مصدر صورة،
  watch path ناقص، انحراف D3 (المنطقة، 50 GB، الحدود، replicas)، TCP proxy أو نطاق لـ mongodb، نطاق عام لـ librechat، سر حرفي
  (`JWT_SECRET` ومفتاح المزوّد `QWEN_API_KEY`)، انحراف السياسة، Config as Code، إضعاف Compose، `HELP_AND_FAQ_URL` بعنوان خارجي، مرحلة بناء غير مثبّتة بالـ digest (N20)،
  وMeilisearch بمنفذ منشور أو على شبكة غير internal أو دون `production` أو بنسخة حرفية من مفتاحها أو TCP proxy (N21–N25)؛
  ولوحة الإدارة بسر حرفي أو حد مختلف أو اتصال غير خاص أو بلا حارس خروج أو كـ root أو على backend أو بكوكي غير Secure أو منفذ غير loopback (N26–N33).
- **مسار النشر للطوارئ (8):** SHA كامل على `origin/main` فقط، رفض التشغيل غير التفاعلي دون `--yes`، الرفع = شجرة الـ commit بالضبط (لا
  `.env` ولا ملفات غير متتبعة)، mongodb وmeilisearch ثم librechat ثم admin-panel، التوقف عند الفشل، حذف التصدير المؤقت.
- **Smoke local (49):** التشغيل، الـ digest، وصول سياسة `librechat.env`، مصادقة MongoDB وأقل امتياز، `/health`، صفحة الدخول، التسجيل
  المعطّل، أول مسؤول، العزل الشبكي، loopback، السجلات في `/app/logs`، الاستمرارية، النسخ والاستعادة بعد فقدان كل الـ volumes، عدم تسرب الأسرار؛
  و#125 (T38–T41): Meilisearch بلا منفذ وعلى الشبكة الداخلية فقط وبمفتاح ودون خروج للإنترنت، والبحث مفعّل للمستخدم؛
  و#141 (T42–T49): لوحة الإدارة سليمة وصفحة دخولها، frontend فقط وloopback، `/metrics` 401، سياسة الكوكي، دخول المسؤول 200 وUSER 403،
  وصول الخادم إلى LibreChat، وفحص الانحراف نظيف.
- **Smoke on-prem (56):** الـ 49 + 7 للوكيل — المنافذ 80/443 فقط، Caddy على frontend فقط، شهادة صالحة لـ CA المُعدّة واسم المضيف، رفض اسم
  غير مُعدّ، تحويل HTTP→HTTPS، HSTS/nosniff ودون `Server`، والرؤوس والشهادة نفسها لموقع لوحة الإدارة (O07).
- **محاكاة Railway:** بناء الصور المشتقة من جذر المستودع، volume واحد فارغ مملوك لـ root لكل خدمة، لا bind mounts، `mongodb.railway.internal`،
  حارسا البدء، مستخدم غير root، رفع صورة حقيقية تُكتب في الـ volume وتُخدم عبر `/images` بالمصادقة، مسار الصور فارغ في الصورة الرسمية، إعادة
  نشر مع بقاء البيانات، `railway-secrets.sh` (نسخة استرداد مشفّرة، عدم الكتابة فوق القيم، استعادة نفس القيم، إعادة نشر بلا تحذير انحراف
  مفاتيح، اكتشاف مفتاح خاطئ)، الرجوع إلى العنوان الخاص بلا نطاق عام؛ و#125 (R34–R39): حارس مفتاح Meilisearch، والوصول بالمفتاح عبر
  `meilisearch.railway.internal`، والبحث مفعّل، ونسخة استرداد قديمة بلا المفتاح؛ و#141 (R40–R46): حارس بدء اللوحة، تشغيلها بلا volume
  وبنظام ملفات للقراءة فقط وكـ `bun`، `/metrics` 401، دخول المسؤول عبر `librechat.railway.internal` ورفض USER، رابط الإعدادات، وحارس
  الخروج؛ IPv6-only يُشغَّل فقط إن دعمت النواة IPv6 وإلا SKIP.
  `RAILWAY_EMULATION_LIBRECHAT_IMAGE=<tag>` و`RAILWAY_EMULATION_ADMIN_PANEL_IMAGE=<tag>` يستعملان صوراً مبنية مسبقاً (حين لا يصل البناء إلى
  GitHub، كجلسة السحابة)، ويذكر R01 صورة LibreChat.
- **Integration `mock_chat.py` (68):** على الحزمة الحقيقية (Compose local + overlay اختباري) مع نموذج وهمي (`mock-llm.mjs`) يعمل بـ Node في
  نفس صورة LibreChat على شبكة `backend` الداخلية فقط. #38 (M01–M21): رفض التسجيل الذاتي (M06، ADR-0024)، دخول مستخدمَين اصطناعيين، عرض/اختيار النموذج، ردود
  متدفقة AR/EN مطابقة حرفياً، الحتمية، تمرير السجل للنموذج، الحفظ وإعادة الفتح بعد إعادة التشغيل، الإيقاف أثناء التدفق، خطأ المزوّد
  (HTTP 400) وخطأ الشبكة، عزل المستخدمين (قراءة/تدفق/إيقاف/كتابة)، لا أسرار في السجلات أو الاستجابات أو MongoDB. #39 (M22–M36): سياسة
  `interface`/`endpoints.agents` مخزّنة للدورين ومفروضة في الخادم (403 للوكلاء وMCP وSkills والذاكرة والجدولة وتشغيل الكود لـ USER وADMIN؛
  MCP للمسؤول فقط منذ #218: M92–M93)،
  إسقاط الأدوات المُصطنعة، رفض نموذج خارج القائمة، فشل المزوّد 503/429/401/404/المهلة بسرعة وبرسالة عامة دون نص المزوّد (canary)، «إيقاف»
  أثناء إعادة المحاولة، استمرار المحادثة بعد الخطأ، إعادة تطبيق الملف بعد إعادة التشغيل ([ai-safe-defaults](../architecture/ai-safe-defaults.md)).
  #43 الجزء A (M37) و#44 Markdown مختلط (M38). #37 (M39–M44): مواصفات النماذج الثلاث وقوائمها الثابتة وعلم التفكير لكل endpoint
  وعرض كتلة التفكير ونموذج العناوين ورفض النموذج القديم، بتوجيه endpoints Qwen Cloud الثلاثة إلى الوهمي. #131 (M66–M68): رفض
  نماذج التشكيلة السابقة، وعمق التفكير يفرضه الخادم مهما أرسلت لوحة المعلمات، وإعادة خطوات التفكير مع إجابة السؤال التوضيحي. #87 (M45): الترحيب والاقتراحات والعناصر
  المخفية. #125 (M49–M56): البحث بالعربية والإنجليزية ولكل مستخدم نتائجه، وروابط المشاركة خلف الدخول، ورد نموذجين على رسالة واحدة،
  وتعطل Meilisearch، وإعادة بناء الفهرس. #129 (M57–M65): الأسئلة التوضيحية (الإجابة والتخطي ورفض الإجابة الحساسة)، ومنع البيانات
  الحساسة، وقراءة PDF وWord وExcel نصاً وحدود الرفع، وتلخيص المحادثات الطويلة. #167 (M57، M72): المواصفات بلا أي أداة وبوضع
  المخرجات `custom` بلا تعليمات LibreChat الإنجليزية. **ليس مزوّداً حياً**؛ سلوك النموذج الحي في المخرجات قيس مرة واحدة في #167.

**GitHub Actions غير مستخدم** (قرار المالك، #16 D2 المعدّل): عمود «أين» أعلاه يذكر الـ workflow المكافئ الباقي للاستخدام الاختياري فقط.

**الاستخدام الآن:** أدوات تحقق يختارها المطوّر حسب المهمة، لا بوابة لكل PR ([ADR-0011](../architecture/adr/0011-production-only-quality-gates.md))؛
الإرشاد حسب نوع التغيير ومستويات الأدلة في [DoD](definition-of-done.md#التحقق-المناسب-للمهمة-إرشاد-هندسي-ليس-بوابة)، وتشغيل فحوصات
`ci.yml`/`security.yml` بـ `run-all.sh` ([scripts/validate/README.md](../../scripts/validate/README.md)). النتائج دليل جلسة سحابة لا تحقق
مستقل؛ قبل الإنتاج تُجمع في بوابات رسمية ([DoD §2](definition-of-done.md#2-الإنتاج--بوابات-الجودة-الرسمية-planned-قبل-أي-go-live)).

## 2. مستويات مخططة

| المستوى | المحتوى | المرحلة | الموقع |
|---|---|---|---|
| Integration | محادثة بالمزوّد المعتمد (#37/#41)، رفع ملف (#40)؛ النموذج الوهمي منفّذ (§1) | M3/M4 | `tests/integration/` |
| Security | سياسة حجب لفحص الصور (عتبات واستثناءات — قرار المالك)، اختبارات الإعداد الآمن الإضافية | M6 | `tests/security/` |
| UX | لقطات RTL/LTR، فحص إمكانية الوصول؛ صفحة الدردشة: [50 حالة](chat-page-test-cases.md) بـ Playwright (#133)؛ رحلة الموظف على الكمبيوتر والجوال: [25 حالة](chat-journey-test-cases.md) (#175)؛ واجهة الفكرة 1: [131 حالة](concept1-interface-test-cases.md) (#181)؛ القائمة v5 في المستودع (§1، #221)؛ بقية السكربتات خارج المستودع (#194) | M2 | `tests/ui/` |

## 3. استراتيجية تقييم الذكاء الاصطناعي (AI Evals) — Planned

- **ما يُقيَّم:** كل مساعد/وكيل/مهارة له مجموعة تقييم (eval set) في `ai/evals/<asset>/` قبل اعتماده.
- **أنواع الحالات:** صحة المهام (golden answers)، الالتزام بالتعليمات والصيغة، جودة العربية، الإسناد للمصادر في RAG،
  حالات عدائية (prompt injection، محاولات استخراج بيانات، إساءة استخدام الأدوات)، والرفض الصحيح.
- **البيانات:** اصطناعية فقط (P0).
- **التشغيل:** يدوي موثق أولاً، ثم آلي في CI عند توفر نموذج اختبار معتمد دون أسرار مكشوفة (workflow منفصل بـ environment محمية).
- **معايير النجاح:** تُحدد لكل مساعد في الـ Issue الخاص به — **لا عتبات معتمدة حالياً**.
- **الأداة:** TBD (تقييم الخيارات في M5؛ تفضيل أدوات مفتوحة قابلة للتشغيل محلياً).

## 4. فحوصات غير مُنفّذة أو غير حاجبة ولماذا

| الفحص | السبب |
|---|---|
| markdownlint | قيمة منخفضة للمحتوى العربي مقابل ضوضاء القواعد؛ `repo_checks.py` يغطي الروابط والبنية |
| فحص الروابط الخارجية | يعتمد على الشبكة وغير حتمي؛ يمكن إضافته كفحص مجدول غير حاجب لاحقاً |
| shellcheck / PSScriptAnalyzer | غير مثبتين/معتمدين بعد في الأدوات المثبتة بالـ hash؛ السكربتات مُختبرة سلوكياً عبر smoke tests — مرشح لاحق |
| CodeQL / Dependency review | لا كود تطبيقي بعد؛ Dependency review يتطلب GitHub Advanced Security للمستودعات الخاصة |
| فحص ثغرات الصور كبوابة حاجبة | مُنفّذ report-only (M1.1)؛ لا عتبة معتمدة — لا نخترع سياسة (SC-18) |
| smoke في CI | `smoke.yml` باقٍ للاستخدام الاختياري؛ GitHub Actions غير مستخدم — الـ smoke يُشغَّل في جلسة السحابة عند تغيير البنية |
| `railway config plan` في CI | غير مستخدم: يتطلب `RAILWAY_TOKEN` وActions؛ المتغيرات تُطبّق بـ `config apply` بعد الدمج ([railway.md §4](../operations/railway.md#4-النشر--تلقائي-من-main-adr-0010)) |
