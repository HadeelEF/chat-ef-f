# Baseer — Product Roadmap v1.0 | خارطة المنتج المعتمدة

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس حالة حالية ولا سياسة.** الحالة الحية: [project/CURRENT_STATE.md](../../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](../README.md).

| البيان | التفاصيل |
|---|---|
| اعتماد الاتجاه | **Approved by product owner, 2026-10-19** (نطاق المنتج وتسلسله فقط) |
| المنتج | EF AI Workspace — «بصير» اسم عمل **مؤقت** |
| الحالة الفعلية | [CURRENT_STATE.md](../2026-10-20-current-state-ledger.md) — ليس هذا الملف دليلاً على الإنجاز |
| التحويل لمهام | [DELIVERY_PLAN.md](DELIVERY_PLAN.md) · [ISSUE_MAP.md](ISSUE_MAP.md) |
| تواريخ التسليم والميزانيات | **TBD**؛ لا افتراضات أو التزامات زمنية |
| ضبط الإصدارات | [RELEASE_PLAN.md](RELEASE_PLAN.md) |

## 1. الرؤية والمبدأ

بناء **منصة ذكاء اصطناعي مؤسسية عربية أولاً وثنائية اللغة** لصندوق البيئة: محادثات متعددة النماذج، تجربة بهوية الصندوق،
معرفة وRAG، مهارات ووكلاء وMCP وArtifacts، ثم مساعدين متخصصين بدءاً بإعداد كراسات RFP وتقييم العروض والعقود والمالية.
المنتج LibreChat-first وفق [ADR-0001](../../../docs/architecture/adr/0001-librechat-as-application-foundation.md)
وتخصيص Upstream-first وفق [ADR-0006](../../../docs/architecture/adr/0006-upstream-first-customization.md)؛ لا fork دائم افتراضياً.

هذه **Product Increments** مرمزة `R0.x`، وليست Git tags `v0.x.y`، ولا تستبدل سجل مراحل الهندسة
`M0–M8` الموثق في [ROADMAP.md](../../../project/ROADMAP.md). المنتج = القيمة المقدمة؛ الهندسة = المكونات والاختبارات والبوابات.

## 2. الإصدارات والنتائج

| Release | النتيجة التي يراها المستخدم | صلتها بالمراحل الهندسية | الحالة | GitHub |
|---|---|---|---|---|
| **R0.1 — Foundation** | LibreChat + MongoDB + Railway dev + حساب مسؤول | M0/M1/M1.1 | **أساس منفذ؛ إغلاق تحقق معلّق** | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15), [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) |
| **R0.2 — AI Activation** | محادثة حقيقية عربية/إنجليزية بنموذج معتمد | M3 | **NEXT — لم تنفذ** | [Epic #31](https://github.com/faenazi/ef-ai-workspace/issues/31) |
| **R0.3 — EF Brand & UX** | واجهة تحمل الهوية المعتمدة وRTL/LTR جيدين | M2 | Planned؛ تدقيق مبكر بالتوازي | [Epic #32](https://github.com/faenazi/ef-ai-workspace/issues/32) |
| **R0.4 — Controlled Preview** | تجربة محدودة 5–10 مستخدمين ببيانات اصطناعية أو بيئة سعودية معتمدة | M8 subset + M6 controls | Planned / gated | [Epic #33](https://github.com/faenazi/ef-ai-workspace/issues/33) |
| **R0.5 — EF Intelligence** | تعليمات موثقة، RAG تجريبي، Skills/MCP/Artifacts محكومة | M4/M5 | Planned | [Epic #34](https://github.com/faenazi/ef-ai-workspace/issues/34) |
| **R0.6 — AI Assistants** | إطار موحد + مساعد RFP؛ دراسة التقييم والعقود والمالية | M7 | Planned | [Epic #35](https://github.com/faenazi/ef-ai-workspace/issues/35) |
| **R1.0 — Enterprise Production** | SSO وحوكمة واستضافة سعودية وإنتاج معتمد | M6/M8 | Planned / approval gated | [Epic #36](https://github.com/faenazi/ef-ai-workspace/issues/36) |

## 3. حدود العمل وبوابات القبول (Release Exit Gates)

### R0.1 — Foundation: Verified baseline, not full closure

**Observed in 2026-10-19:** LibreChat v0.8.8 + MongoDB 8.0.34 on Railway EU West `dev`، رابط عام،
حساب `fahad` (local ADMIN)، التسجيل مغلق، اسم «بصير» مؤقت؛ Compose للبيئات المحلية/الداخلية.
**Not yet:** LLM provider، Entra SSO، إنتاج سعودي، اختبارات فعلية على Windows/Ubuntu.
**Gate:** تصنيف أدلة RW المتبقية وbackup/limits وحماية `main` و#17
كـ verified أو مخاطر معلقة ذات مالك؛ لا إغلاق اصطناعي للمرحلة.

### R0.2 — AI Activation (أول إصدار مستخدم فعلياً)

**In:** اعتماد مزوّد نموذج واحد في [#5](https://github.com/faenazi/ef-ai-workspace/issues/5)،
تهيئة `librechat.yaml` وأسرار runtime، قائمة النماذج، المحادثة المتدفقة AR/EN، حفظ المحادثات،
أخطاء/تقييد الاستهلاك، تقييم إمكان الملفات الاصطناعية (دون افتراض RAG).
**Out:** البيانات الفعلية وSSO الحقيقي، تشغيل GPU محلي كشرط، RAG الكامل، وكلاء أو MCP غير معتمدين.
**Exit:** تسجيل دخول → نموذج مصرح → بث إجابة بالعربية/الإنجليزية → إعادة فتح المحادثة،
تجارب فشل وعزل مستخدم، وعدم تسريب الأسرار، أدلة E2E على بيئة محددة مع rollback، وقبول المالك. [#37–#41](ISSUE_MAP.md).
**اختيار المنتج لا يجيز مزوّد LLM بعينه أو إرسال بيانات الصندوق للخارج.**

### R0.3 — Official Brand & Bilingual Experience

**In:** اعتماد أصول وهوية وخطوط وحقوق استخدام من [#7](https://github.com/faenazi/ef-ai-workspace/issues/7)،
تقييم قابلية تخصيص LibreChat v0.8.8 شاشة بشاشة، login/nav/chat/settings/modal/mobile،
الترجمة وRTL/LTR والـ accessibility، وتحسينات عامة لهوية الصندوق باستخدام معلومات عامة معتمدة فقط.
**Out:** اختلاق شعار/ألوان/خطوط أو fork بلا قرار ADR.
**Exit:** مصفوفة اعتماد الهوية + لقطات AR/EN × mobile/desktop ومراجعة keyboard/contrast؛ وثائق فجوات upstream
والتراجع وإثبات قرار الاسم والهوية الرسمية. [#42–#45](ISSUE_MAP.md).

### R0.4 — Controlled Preview

**In:** تجربة مضبوطة 5–10 مستخدمين ضمن سيناريوهات اصطناعية وملاحظات غير حساسة وإصلاحات متعقبة.
**Out:** مستندات أو هويات موظفي الصندوق الحقيقية على Railway خارج المملكة، Entra Tenant، إدراجها كخدمة إنتاجية.
**Exit:** قرار eligibility/privacy وSC-18 قبل الدعوة [#46](https://github.com/faenazi/ef-ai-workspace/issues/46)،
تقرير تجربة وعيوب مع Go / Repeat / Stop [#47](https://github.com/faenazi/ef-ai-workspace/issues/47).
إن احتاجت التجربة بيانات أو هويات حقيقية **تُوقف** حتى بيئة سعودية وضوابط معتمدة.

### R0.5 — EF Intelligence, Knowledge & Skills

**In:** تعليمات من معلومات الصندوق العامة المعتمدة مع مالك ونسخة؛ RAG على بيانات اصطناعية
مع citation/ACL/ingestion؛ 2–3 مهارات مفيدة (مخاطبات/عروض/تلخيص)، تحقق MCP وArtifacts/Sandpack isolation.
**Out:** وثائق سرية على Railway، تفعيل أدوات أو مزوّدي embeddings بلا ترخيص أو قرار بيانات.
**Exit:** مجموعة AI evals قابلة للتكرار، إسناد ورفض الأسئلة غير المسندة، قيود الوصول، مصدر كل مهارة،
فحص prompt injection/egress. [#48–#50](ISSUE_MAP.md).

### R0.6 — Specialized Assistants (RFP first)

**In:** قالب مساعد (مالك أعمال، تعليمات، نموذج، معرفة، مهارات، أدوات، صلاحيات، evals)،
أول مساعد لصياغة RFP ببيانات اصطناعية؛ ثم تحليل جدوى مساعدين لتقييم العروض والعقود والمالية.
**Out:** ترسية تلقائية، موافقة تعاقدية/مالية، بيانات منافسات حقيقية قبل اعتماد الأمن.
**Exit:** نتائج تقييم أعمال لمساعد RFP مع مراجعة بشرية، وتذاكر ونطاقات قرار مستقلة للمساعدين التاليين.
[#51–#55](ISSUE_MAP.md).

### R1.0 — Enterprise Production

**In:** استضافة ومعالجة ونسخ داخل السعودية وفق الاعتماد، Entra OIDC least privilege، RBAC/ACL،
audit، retention، DR/backup، مراقبة، اختبارات أمن وأداء مستقلة، خطة رجوع.
**Out:** اعتبار نجاح Railway EU West ترخيصاً لمعالجة بيانات الصندوق أو تسجيل جميع الموظفين.
**Exit:** بوابات M6/M8 على بيئة سعودية فعلية، SLO/RTO/RPO معتمدة، مراجعة مستقلة، قرار Go-live من المالك
والأطراف المختصة. [#56–#58](ISSUE_MAP.md).

## 4. مسار المنتج ومسار الأمان بالتوازي

- **Product:** R0.1 → R0.2 → R0.3 → R0.4 → R0.5 → R0.6 → R1.0. يمكن بدء تدقيق R0.3 بالتوازي مع R0.2.
- **Enterprise readiness:** حماية `main`، فحص SC-18 المستمر (الحرجة الخمس مُعالجة/مُصنّفة على Railway `dev` منذ 2026-10-19)،
  النسخ والاستعادة، الخصوصية، صلاحيات tools، إقامات البيانات، Entra وأمان الإنتاج.
  بوابات الأمن *قبل* أي تجربة هويات/وثائق حقيقية وليست مؤجلة إلى نهاية المسار.

## 5. القياس والحوكمة

لا نسب تقديرية بلا إثبات: التحسين يُقاس بمعايير قبول **اختُبرت** وما تبقى Blocked/NOT RUN؛
غلق Issue أو وجود مستند لا يثبت قدرة النظام. GitHub Issues مصدر تقدم الأعمال،
[CURRENT_STATE](../2026-10-20-current-state-ledger.md) مصدر حالة التشغيل، و[DoD](../../../docs/quality/definition-of-done.md)
مصدر بوابات التنفيذ. تفاصيل [delivery governance](delivery-governance.md).
