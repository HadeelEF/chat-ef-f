# الحالة المتحققة الآن (Current Verified State)

> **سجل تاريخي (أُرشف 2026-10-26، [#235](https://github.com/faenazi/ef-ai-workspace/issues/235))؛ ليس حالة حالية ولا سياسة.** نص `project/CURRENT_STATE.md` كما هو في `main@b1cea96` قبل إعادة ترتيبه؛ الحالة الحية: [project/CURRENT_STATE.md](../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](README.md).

| الحقل | القيمة |
|---|---|
| آخر تحديث | 2026-10-26 — آخر نشر متحقق: librechat `b6561809` (#230) وadmin-panel `9e70ca20` |
| التشغيل | LibreChat v0.8.8 + MongoDB 8.0.34 على Railway `dev` (EU West) **ببيانات اصطناعية فقط**؛ رابطان عامان (المنصة ولوحة الإدارة)؛ مسؤول محلي واحد؛ التسجيل مفتوح (ADR-0020)؛ Qwen Cloud بثلاثة نماذج (#37، #39) |
| المرحلة | **R0.2 AI Activation جارية** (#5 محسوم: Qwen Cloud)؛ من R0.3 أُنجزت التدقيقات والواجهة العربية، والهوية مطبّقة بقرار المالك (#92) ([ROADMAP §6](../../project/ROADMAP.md#6-ترتيب-التنفيذ-الحالي)) |

> لقطة فقط: كل سطر هنا له دليل مرتبط، والوثائق الموجودة ≠ وظائف تعمل. التسلسل الزمني في الـ Issues و`CHANGELOG.md`
> و[docs/history/](../history/README.md). المستويات: `Tested (cloud session)` = نفّذه الوكيل في السحابة (غير مستقل)؛
> `Verified (target environment)` = في Railway/Windows/Ubuntu الحقيقي؛ `Verified (GitHub CI)` غير مستخدم (D2).

## 1. متحقق الآن

| البند | المستوى | الدليل |
|---|---|---|
| Railway `dev`: الخدمات الأربع منشورة من `railway.ts`، MongoDB خاص، نشر تلقائي من `main` لمدخلات الصور ([ADR-0010](../architecture/adr/0010-railway-dev-autodeploy-from-main.md))، المتغيرات بـ `config apply` | Verified (target environment) | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| طبقة الترقيع المؤقتة ([ADR-0012](../architecture/adr/0012-temporary-security-patch-layer.md)): R-01–R-04 معالجة في صورة Railway، R-05 غير متأثرة؛ Compose بلا الطبقة؛ **R-09** بانتظار المالك (§3) | Verified (target environment) 2026-10-19 | PR #73، [السجل](../security/vulnerability-register.md) |
| صلاحيات AI (#39، #108، #189): الوكلاء وSkills والذاكرة داخلياً، والنشر للجميع للمسؤول فقط، و8 أوامر جاهزة (ADR-0018)؛ MCP للمسؤول (ADR-0021)؛ تشغيل الكود والأفعال مغلقة ([التفاصيل](../architecture/ai-safe-defaults.md)) | Verified (target environment): `008f712a` سجل البدء؛ السلوك Tested (cloud session) | #219، [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| إخفاء علامة upstream (#43 الجزء A): لا تذييل ولا رابط upstream، لا `buildInfo` ([المصفوفة §11](../design/audits/brand-implementation-matrix.md)) | Verified (target environment) | PR #69، [#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6277008799) |
| اسم العمل «بصير» (`APP_TITLE`، مؤقت `PROVISIONAL`) مطبّق في `dev` | Verified (target environment)؛ عنوان التبويب owner-check | PR #27، [#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6264988990) |
| أسرار Railway فقط (أسماء فقط في السجلات، ومنها `SESSION_SECRET` #141)؛ لا أسرار في Git | Verified (target environment) | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| انحدار المحادثة بنموذج وهمي `mock_chat.py` (M01–M93) | Tested (cloud session) **93/93** 2026-10-25 | [#38](https://github.com/faenazi/ef-ai-workspace/issues/38)، #218 |
| Qwen Cloud: سريع `qwen3.8-flash` (افتراضي)، متأنٍّ بتفكير، عميق `deepseek-v4.1-flash-1017`؛ عناوين بلغة المحادثة؛ مهلة 60 ث؛ [المعيار](../quality/model-benchmark.md) (#211) | Verified (target environment): `fad1102c`، `542321ae`؛ Tested (cloud session) 10-25 | [#37](https://github.com/faenazi/ef-ai-workspace/issues/37) |
| الواجهة العربية (ADR-0013) | منشورة حتى #230 (`b6561809`)؛ المحادثة 25/25، «التخصيص» 135/135، PWA 9/9 Tested (cloud session)؛ الفحص البصري عند المالك | #232، #224، #221، [#115](https://github.com/faenazi/ef-ai-workspace/issues/115)، [الرحلة](../quality/chat-journey-test-cases.md)، [الفكرة 1](../quality/concept1-interface-test-cases.md) |
| هوية الصندوق (D-04): الألوان والخط والشعارات (#92)، لوحة الدخول والإجراء الرئيسي (#94) | Verified (target environment): `325d0fd1`، `ae6b9b1e` | [#92](https://github.com/faenazi/ef-ai-workspace/issues/92)، [#94](https://github.com/faenazi/ef-ai-workspace/issues/94) |
| Compose: local 49/49 ومحادثة 93/93 وسلبية 33/33 (10-25)، onprem 56/56 (10-23)؛ محاكاة Railway 42/43 (R33 قديم) | Tested (cloud session) | #141 |
| مزايا LibreChat: البحث، المشاركة، المقارنة، الملفات، SC-22، بحث Qwen دائماً؛ لا بطاقات أسئلة (#167) | Tested (cloud session)؛ منشورة؛ البحث الحي عند المالك | [#125](https://github.com/faenazi/ef-ai-workspace/issues/125)، [#135](https://github.com/faenazi/ef-ai-workspace/issues/135)، [#138](https://github.com/faenazi/ef-ai-workspace/issues/138) |
| تدقيق الهوية (#42) وRTL والوصول (#44)؛ اختبار العربية (#127) 21/21؛ الدردشة (#133) 105/105 | Tested (cloud session)؛ منشورة | [المصفوفة](../design/audits/brand-implementation-matrix.md)، [التدقيق](../design/audits/arabic-rtl-audit.md)، [RTL](../design/audits/arabic-rtl-full-test.md)، [الدردشة](../quality/chat-page-test-cases.md) |
| المخرجات (#149–#167): الهوية، Word/PowerPoint، تعليمات عربية، معاينة محلية | Verified (target environment): `b6561809`؛ Tested (cloud session): Qwen حي 16/17، Playwright | [#167](https://github.com/faenazi/ef-ai-workspace/issues/167)، #230 |
| لوحة الإدارة ([ADR-0016](../architecture/adr/0016-librechat-admin-panel.md)): بناء أمني مؤقت (0 CRITICAL؛ #165)، بهوية الصندوق (#160) | Verified (target environment): `227d2426`، رفض الاستيراد المجهول؛ دخول المالك owner-check | [#141](https://github.com/faenazi/ef-ai-workspace/issues/141)، [#165](https://github.com/faenazi/ef-ai-workspace/issues/165) |

## 2. غير متحقق / NOT RUN

- حماية فرع `main`: rulesets `[]` (2026-10-25)؛ مستودع خاص: يلزم GitHub Pro → **إجراء مالك** ([#3](https://github.com/faenazi/ef-ai-workspace/issues/3)).
- S1 (#196): 14 مجموعة Jest تفشل بتعديلاتنا وسكربتات Playwright خارج المستودع (#194)؛ 31/33 تعديلاً تتعارض مع upstream `main` (#193)؛ صور Compose ≠ Railway (#195).
- Windows 11 حقيقي وخادم Ubuntu حقيقي ([#17](https://github.com/faenazi/ef-ai-workspace/issues/17)).
- Railway: نسخ الـ volumes، حد الإنفاق، RW2/RW5–RW9/RW12 ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15)).
- الفحص البصري للرابط العام؛ قارئ الشاشة؛ الشبكة الخاصة IPv6-only؛ `admin-config-drift.sh --railway` (مفتاح SSH للمالك، #141).
- مخرجات #167 وبحث الإنترنت (#135) من جوال المالك (Safari).

## 3. العوائق

| القرار / العائق | يعيق | Issue |
|---|---|---|
| E2E مسجّل على Railway (المالك أو حساب `qa-` بتفويضه)، وحدود #39، و#40 | إغلاق R0.2 | [#41](https://github.com/faenazi/ef-ai-workspace/issues/41) |
| قرار R-09 (SC-18) | الرابط العام لـ `dev` | [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) |
| «بصير برو» بلا بحث | الإنترنت في كل وضع | #213 |
| تأكيد ترخيص استضافة خط Aktiv Grotesk (استثناء المالك) | التعريض الأوسع R0.4 | [#7](https://github.com/faenazi/ef-ai-workspace/issues/7) |
| حماية `main` | SC-04 | [#3](https://github.com/faenazi/ef-ai-workspace/issues/3) |
| بيئة داخل المملكة + جهاز Windows وخادم Ubuntu | التحقق المستهدف، Entra الحقيقي، أي بيانات حقيقية | [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) |
| ترقية الصور المنضبطة (وإزالة طبقة ADR-0012 عند أول ترقية LibreChat) | #16، #62 | [#62](https://github.com/faenazi/ef-ai-workspace/issues/62) |
| GitHub Projects/Milestones غير منشأة | تتبّع R0.x الأصلي | [#59](https://github.com/faenazi/ef-ai-workspace/issues/59) |

## 4. المهمة التالية

1. **المالك:** P0 في #196 (#3، R-09 في #16، نسخ #15)؛ E2E (#41)؛ فحوص الجوال (#232، #224، #221، #141، #135، #138، #167، #157، #169)؛ قرارات #213 و#122 و#39 وتنبيه إنفاق Qwen.
2. **الوكيل:** خطة S1 ([#196](https://github.com/faenazi/ef-ai-workspace/issues/196)): #194 → #40 → سجل E2E في #41.
3. **بالتوازي:** فحص SC-18 أسبوعياً من جلسة الوكيل (`image-scan.yml` لا يعمل، D2)؛ آخره 2026-10-25؛ ومتابعة إصدار LibreChat (#16، #193).

## 5. تنبيهات تشغيلية

- Watch paths (ADR-0010): `infrastructure/railway/*`، و`common/` (`librechat.yaml` و`client/**` و`mongo-init/**` و`prompts-seed.js` و`roles-policy.js`)، و`ai/skills/**` و`ai/prompts/**`؛ دمجها في `main` ينشر `dev` فوراً.
- شبكة الجلسة تعترض TLS داخل `docker build`: الصور تُختبر بنسخة فيها شهادة الوكيل فقط.
- استعادة النسخ تتطلب نفس `CREDS_KEY`/`CREDS_IV`؛ تدويرهما يُتلف بيانات الاعتماد المخزنة.
- Railway خارج المملكة: بيانات اصطناعية فقط وليس مرشحاً للإنتاج (OD-05)؛ لا ربط tenant Entra الحقيقي ولا حسابات موظفين حقيقية.
