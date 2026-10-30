# الحالة المتحققة الآن (Current Verified State)

| الحقل | القيمة |
|---|---|
| آخر تحديث | 2026-10-26 — آخر نشر: [سجل النشر في #15](https://github.com/faenazi/ef-ai-workspace/issues/15) ([ADR-0023](../docs/architecture/adr/0023-deploy-log-on-issue-15.md)) |
| التشغيل | LibreChat v0.8.8 + MongoDB 8.0.34 على Railway `dev` (EU West) **ببيانات اصطناعية فقط**؛ رابطان عامان (المنصة ولوحة الإدارة)؛ مسؤول محلي واحد؛ التسجيل مغلق منذ 2026-10-27 (ADR-0024، #245)؛ Qwen Cloud بثلاثة نماذج (#37، #39) |
| المرحلة | **R0.2 AI Activation جارية** (#5 محسوم: Qwen Cloud)؛ من R0.3 أُنجزت التدقيقات والواجهة العربية، والهوية مطبّقة بقرار المالك (#92) ([ROADMAP §6](ROADMAP.md#6-ترتيب-التنفيذ-الحالي)) |

> لقطة فقط: كل سطر هنا له دليل مرتبط، والوثائق الموجودة ≠ وظائف تعمل. التسلسل الزمني في الـ Issues و`CHANGELOG.md`
> و[docs/history/](../docs/history/README.md). المستويات: `Tested (cloud session)` = نفّذه الوكيل في السحابة (غير مستقل)؛
> `Verified (target environment)` = في Railway/Windows/Ubuntu الحقيقي؛ `Verified (GitHub CI)` غير مستخدم (D2).

## 1. متحقق الآن

| البند | المستوى | الدليل |
|---|---|---|
| Railway `dev`: أربع خدمات من `railway.ts`، MongoDB خاص، نشر تلقائي (ADR-0010)، المتغيرات بـ `config apply` | Verified (target environment) | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| طبقة الترقيع المؤقتة (ADR-0012): R-01–R-04 معالجة، R-05 غير متأثرة؛ **R-09** بانتظار المالك (§3) | Verified (target environment) 2026-10-19 | PR #73، [السجل](../docs/security/vulnerability-register.md) |
| صلاحيات AI: الوكلاء وSkills والذاكرة والأوامر الجاهزة؛ MCP للمسؤول؛ تشغيل الكود والأفعال مغلقة | Verified (target environment)؛ السلوك Tested (cloud session) | [التفاصيل](../docs/architecture/ai-safe-defaults.md)، [سجل البدء](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6399760645) |
| إخفاء علامة upstream (#43 الجزء A) | Verified (target environment) | PR #69، [#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6277008799) |
| اسم العمل «بصير» (`APP_TITLE`، مؤقت) | Verified (target environment)؛ عنوان التبويب في #234 | PR #27، [#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6264988990) |
| أسرار Railway فقط؛ لا أسرار في Git | Verified (target environment) | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| انحدار المحادثة بنموذج وهمي (`mock_chat.py`) | Tested (cloud session) 93/93، 2026-10-26 | [#38](https://github.com/faenazi/ef-ai-workspace/issues/38) |
| Qwen Cloud: سريع (`qwen3.8-flash`، افتراضي) ومتأنٍّ وعميق؛ عناوين بلغة المحادثة | Verified (target environment)؛ المعيار Tested (cloud session) | [#37](https://github.com/faenazi/ef-ai-workspace/issues/37)، [المعيار](../docs/quality/model-benchmark.md) |
| الواجهة العربية (ADR-0013): القائمة الجانبية، صفحة المحادثة وإصلاحات اختبارها الحي (#41)، تثبيت PWA وإحساس تطبيق الجوال (#238) | Tested (cloud session)؛ منشورة؛ الفحص البصري في #234 | [الرحلة](../docs/quality/chat-journey-test-cases.md)، [الفكرة 1](../docs/quality/concept1-interface-test-cases.md) |
| هوية الصندوق (D-04): الألوان والخط والشعارات ولوحة الدخول | Verified (target environment) | [#92](https://github.com/faenazi/ef-ai-workspace/issues/92)، [#94](https://github.com/faenazi/ef-ai-workspace/issues/94) |
| Compose: local 49/49، onprem 56/56، سلبية 33/33؛ محاكاة Railway 42/43 (R33 قديم) | Tested (cloud session) 10-23/10-25 | #141 |
| مزايا LibreChat: البحث، المشاركة، المقارنة، الملفات، SC-22، بحث Qwen | Tested (cloud session)؛ منشورة؛ البحث الحي في #234 | [#125](https://github.com/faenazi/ef-ai-workspace/issues/125)، [#135](https://github.com/faenazi/ef-ai-workspace/issues/135) |
| تدقيقات الهوية (#42) وRTL والوصول (#44) والعربية (#127) والدردشة (#133) | Tested (cloud session)؛ منشورة | [المصفوفة](../docs/design/audits/brand-implementation-matrix.md)، [التدقيق](../docs/design/audits/arabic-rtl-audit.md)، [RTL](../docs/design/audits/arabic-rtl-full-test.md)، [الدردشة](../docs/quality/chat-page-test-cases.md) |
| المخرجات (#149–#167): الهوية، Word/PowerPoint، تعليمات عربية، معاينة محلية | Verified (target environment)؛ Qwen حي 16/17 Tested (cloud session) | [#167](https://github.com/faenazi/ef-ai-workspace/issues/167) |
| لوحة الإدارة (ADR-0016) بهوية الصندوق، بناء أمني مؤقت (#165) | Verified (target environment)، ومنه رفض الاستيراد المجهول؛ دخول المالك في #234 | [#141](https://github.com/faenazi/ef-ai-workspace/issues/141) |

## 2. غير متحقق / NOT RUN

- حماية فرع `main`: rulesets `[]` (2026-10-25)؛ مستودع خاص: يلزم GitHub Pro → **إجراء مالك** ([#3](https://github.com/faenazi/ef-ai-workspace/issues/3)).
- S1 (#196): 14 مجموعة Jest تفشل بتعديلاتنا وسكربتات Playwright خارج المستودع (#194)؛ 31/33 تعديلاً تتعارض مع upstream `main` (#193)؛ صور Compose ≠ Railway (#195).
- Windows 11 حقيقي وخادم Ubuntu حقيقي ([#17](https://github.com/faenazi/ef-ai-workspace/issues/17)).
- Railway: نسخ الـ volumes، حد الإنفاق، RW2/RW5–RW9/RW12 ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15)).
- فحوص المالك من الجوال ([#234](https://github.com/faenazi/ef-ai-workspace/issues/234))؛ قارئ الشاشة؛ الشبكة الخاصة IPv6-only؛ `admin-config-drift.sh --railway` (مفتاح SSH للمالك، #141).

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

1. **المالك:** P0 في #196 (#3، R-09 في #16، نسخ #15)؛ E2E (#41)؛ فحوص الجوال ([#234](https://github.com/faenazi/ef-ai-workspace/issues/234))؛ قرارات #213 و#122 و#39 وتنبيه إنفاق Qwen.
2. **الوكيل:** خطة S1 ([#196](https://github.com/faenazi/ef-ai-workspace/issues/196)): #194 → #40 → سجل E2E في #41.
3. **بالتوازي:** فحص SC-18 أسبوعياً من جلسة الوكيل (`image-scan.yml` لا يعمل، D2)؛ آخره 2026-10-25؛ ومتابعة إصدار LibreChat (#16، #193).

## 5. تنبيهات تشغيلية

- Watch paths (ADR-0010): `infrastructure/railway/*`، و`common/` (`librechat.yaml` و`client/**` و`mongo-init/**` و`prompts-seed.js` و`roles-policy.js`)، و`ai/skills/**` و`ai/prompts/**`؛ دمجها في `main` ينشر `dev` فوراً.
- شبكة الجلسة تعترض TLS داخل `docker build`: الصور تُختبر بنسخة فيها شهادة الوكيل فقط.
- استعادة النسخ تتطلب نفس `CREDS_KEY`/`CREDS_IV`؛ تدويرهما يُتلف بيانات الاعتماد المخزنة.
- Railway خارج المملكة: بيانات اصطناعية فقط وليس مرشحاً للإنتاج (OD-05)؛ لا ربط tenant Entra الحقيقي ولا حسابات موظفين حقيقية.
