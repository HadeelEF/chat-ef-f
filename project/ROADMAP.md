# خارطة الطريق (Roadmap)

| الحقل | القيمة |
|---|---|
| الاعتماد | نتائج المنتج R0.1–R1.0 وتسلسلها اعتمدها المالك في 2026-10-19 (النطاق والتسلسل فقط؛ التواريخ والميزانيات **TBD**) |
| الحالة الفعلية | [CURRENT_STATE.md](CURRENT_STATE.md) — هذه الوثيقة تصف **الخطة** لا الإنجاز |
| التاريخ | قوائم قبول M0/M1/M1.1 كما أُغلقت ووثائق التخطيط الأصلية (PR #61) في [docs/history/](../docs/history/README.md) |

## 1. ثلاثة أنواع من المعرّفات

1. **Product Increment `R0.1`–`R1.0`:** نتيجة يراها المستخدم ويختبرها (§2)؛ **ليست** Git tag ولا إصدار LibreChat.
2. **Engineering Milestone `M0`–`M8`:** مسار هندسي (§4)؛ قد يقطع الإصدار الواحد أكثر من مرحلة والعكس (M3 يبدأ قبل اكتمال M2).
3. **Software version `vMAJOR.MINOR.PATCH`:** وسم GitHub Release مستقبلي لا يُصدر إلا بقرار المالك (§5)؛ مستقل عن upstream `v0.8.8`.

## 2. خارطة المنتج المعتمدة

| Release | النتيجة التي يراها المستخدم | المراحل | Epic / القرار | Issues التنفيذ |
|---|---|---|---|---|
| **R0.1 Foundation** | LibreChat + MongoDB على Railway `dev` + حساب مسؤول | M0/M1/M1.1 | [#15] | [#17]، [#3]، [#16]، [#62] |
| **R0.2 AI Activation** | محادثة حقيقية AR/EN بنموذج معتمد | M3 | Epic [#31]، قرار [#5] | [#37]، [#38]، [#39]، [#40]، [#41] |
| **R0.3 Brand & UX** | واجهة بالهوية المعتمدة وRTL/LTR سليمان | M2 | Epic [#32]، قرار [#7] | [#42]، [#43]، [#44]، [#45] |
| **R0.4 Controlled Preview** | تجربة 5–10 مستخدمين ببيانات اصطناعية | M8 جزئياً + ضوابط M6 | Epic [#33] | [#46]، [#47] |
| **R0.5 EF Intelligence** | تعليمات موثقة، RAG تجريبي، Skills/MCP/Artifacts محكومة | M4/M5 | Epic [#34] | [#48]، [#49]، [#50] |
| **R0.6 AI Assistants** | إطار موحد + مساعد RFP؛ دراسة التقييم والعقود والمالية | M7 | Epic [#35] | [#51]، [#52]، [#53]، [#54]، [#55] |
| **R1.0 Enterprise Production** | SSO وحوكمة واستضافة سعودية وإنتاج معتمد | M6/M8 | Epic [#36] | [#56]، [#57]، [#58] |

المسار: R0.1 → R0.2 → R0.3 → R0.4 → R0.5 → R0.6 → R1.0؛ تدقيق R0.3 يجوز بالتوازي مع R0.2. بوابات الأمن (حماية `main`،
SC-18، النسخ، الخصوصية، صلاحيات الأدوات، إقامة البيانات، Entra) تسبق أي تجربة بهويات أو وثائق حقيقية ولا تُؤجل إلى النهاية.
اعتماد الخارطة ≠ اعتماد مزوّد أو بيانات حقيقية أو هوية أو إنفاق أو إنتاج. حوكمة عابرة:
[#59] (GitHub Project/Milestones)، [#8] (Codex).

## 3. بوابات الخروج (Exit Gates)

### R0.1 — Foundation

- **In:** LibreChat v0.8.8 + MongoDB 8.0.34 على Railway EU West `dev` ببيانات اصطناعية، رابط عام، مسؤول محلي؛ Compose للبيئتين المحليتين.
- **Out:** مزوّد LLM، Entra SSO، إنتاج سعودي.
- **Exit:** تصنيف RW المتبقية والنسخ وحد الإنفاق وحماية `main` و#17 كـ verified أو مخاطر معلقة ذات مالك؛ لا إغلاق اصطناعي.

### R0.2 — AI Activation (أول إصدار يستخدمه الناس)

- **In:** مزوّد واحد معتمد في #5، `librechat.yaml` وأسرار runtime، قائمة النماذج، بث AR/EN، حفظ المحادثات، أخطاء وتقييد
  الاستهلاك، تقييم الملفات الاصطناعية دون افتراض RAG.
- **Out:** بيانات فعلية وSSO حقيقي، GPU محلي كشرط، RAG كامل، وكلاء أو MCP غير معتمدين.
- **Exit:** دخول → نموذج مصرح → بث إجابة AR/EN → إعادة فتح المحادثة؛ تجارب فشل وعزل مستخدم؛ لا تسريب أسرار؛ أدلة E2E على بيئة
  محددة مع rollback؛ قبول المالك. اختيار المنتج لا يجيز مزوّداً بعينه ولا إرسال بيانات الصندوق للخارج.

### R0.3 — Official Brand & Bilingual Experience

- **In:** أصول وهوية وخطوط وحقوق استخدام من #7؛ تقييم تخصيص LibreChat شاشة بشاشة؛ الترجمة وRTL/LTR والوصول؛ معلومات عامة معتمدة فقط.
- **Out:** اختلاق شعار أو ألوان أو خطوط، أو fork بلا قرار ADR.
- **Exit:** مصفوفة اعتماد الهوية + لقطات AR/EN × جوال/سطح مكتب ومراجعة لوحة المفاتيح والتباين؛ فجوات upstream والتراجع؛ قرار
  الاسم والهوية الرسمية موثق.

### R0.4 — Controlled Preview

- **In:** تجربة مضبوطة 5–10 مستخدمين بسيناريوهات اصطناعية وملاحظات غير حساسة وإصلاحات متعقبة.
- **Out:** وثائق أو هويات موظفين حقيقية على Railway، Entra tenant، اعتبارها خدمة إنتاجية.
- **Exit:** قرار الأهلية والخصوصية وSC-18 قبل الدعوة (#46)؛ تقرير تجربة وعيوب مع Go / Repeat / Stop (#47). أي حاجة لبيانات
  حقيقية = توقف حتى بيئة سعودية وضوابط معتمدة.

### R0.5 — EF Intelligence, Knowledge & Skills

- **In:** تعليمات من معلومات الصندوق العامة المعتمدة بمالك ونسخة؛ RAG على بيانات اصطناعية مع citation/ACL/ingestion؛ 2–3 مهارات
  مفيدة؛ تحقق MCP وعزل Artifacts/Sandpack.
- **Out:** وثائق سرية على Railway؛ أدوات أو مزوّدو embeddings بلا ترخيص أو قرار بيانات.
- **Exit:** AI evals قابلة للتكرار، إسناد ورفض الأسئلة غير المسندة، قيود الوصول، مصدر كل مهارة، فحص prompt injection والخروج الشبكي.

### R0.6 — Specialized Assistants (RFP أولاً)

- **In:** قالب مساعد (مالك أعمال، تعليمات، نموذج، معرفة، مهارات، أدوات، صلاحيات، evals)؛ مساعد RFP ببيانات اصطناعية؛ ثم جدوى
  مساعدي تقييم العروض والعقود والمالية.
- **Out:** ترسية تلقائية، موافقة تعاقدية أو مالية، بيانات منافسات حقيقية قبل اعتماد الأمن.
- **Exit:** تقييم أعمال لمساعد RFP بمراجعة بشرية؛ تذاكر ونطاقات قرار مستقلة للمساعدين التاليين.

### R1.0 — Enterprise Production

- **In:** استضافة ومعالجة ونسخ داخل السعودية، Entra OIDC بأقل امتياز، RBAC/ACL، audit، retention، DR، مراقبة، اختبارات أمن
  وأداء مستقلة، خطة رجوع.
- **Out:** اعتبار نجاح Railway EU West ترخيصاً لمعالجة بيانات الصندوق أو تسجيل جميع الموظفين.
- **Exit:** بوابات M6/M8 على بيئة سعودية فعلية؛ SLO/RTO/RPO معتمدة؛ مراجعة مستقلة؛ قرار Go-live من المالك والأطراف المختصة
  ([DoD §2](../docs/quality/definition-of-done.md#2-الإنتاج--بوابات-الجودة-الرسمية-planned-قبل-أي-go-live)).

## 4. المراحل الهندسية M0–M8

| المرحلة | العنوان | الهدف | يعتمد على | الحالة / الإصدار |
|---|---|---|---|---|
| **M0** | Repository Foundation & Governance | مستودع مؤسسي هو المصدر الوحيد للحقيقة، صديق للوكلاء، بفحوصات آلية | — | مكتملة — PR #9 (`0eab526`) |
| **M1** | LibreChat Platform Foundation | LibreChat مثبت الإصدار، آمن افتراضياً، مُتحقق منه في السحابة | M0 | مكتملة — PR #12 (`0db80d9`) |
| **M1.1** | Multi-Environment Hosting & First Controlled Railway Deployment | إعداد مشترك لثلاث بيئات (ADR-0008) وأول نشر مُتحكَّم به على Railway | M1 | أ مكتملة — PR #18 (`bccd408`)؛ ب مفتوحة (#15، #17) |
| **M2** | Branding & Bilingual UX | تجربة عربية أولاً + هوية (مؤقتة ثم رسمية) عبر آليات مدعومة | M1، D-04 | R0.3 |
| **M3** | Models, Chat & AI Capabilities | ربط مزوّدين معتمدين ونماذج محلية، إدارة المحادثات | M1، OD-01 | R0.2 |
| **M4** | Knowledge, RAG & Artifacts | رفع الملفات، RAG، Artifacts بإقامة بيانات مقيّمة | M3 | R0.5 |
| **M5** | Agents, Skills & MCP | وكلاء ومهارات وأدوات محكومة من المستودع مع كشف الانحراف | M3 | R0.5 |
| **M6** | Security, Governance & Operations | Entra ID SSO، RBAC، تدقيق، نسخ واستعادة مجرّبة، مراقبة | M1، D-05 | ضوابط R0.4؛ R1.0 |
| **M7** | Specialized Assistants | أول مساعد متخصص (RFP) بتقييمات | M5، OD-06 | R0.6 |
| **M8** | Pilot & Production Readiness | تجربة محدودة، أهداف NFR معتمدة، نقل لبنية سعودية معتمدة | M6، OD-04، OD-05 | R0.4 جزئياً؛ R1.0 |

معايير القبول التفصيلية لكل مرحلة تُكتب في Issue المرحلة عند بدئها استناداً إلى [FR](../docs/product/functional-requirements.md)
و[NFR](../docs/product/non-functional-requirements.md). قوائم M0/M1/M1.1 كما أُغلقت ومواءمة الميثاق الأصلي:
[السجل التاريخي](../docs/history/engineering-roadmap-m0-m1-closure.md).

## 5. سياسة الوسوم والإصدار

- لا وسم Git ولا إعلان إصدار إلا بقرار المالك؛ إغلاق Epic أو وجود وثيقة لا يُنشئ وسماً، ولا تُعاد تسمية وسوم قديمة.
- `R0.x`: قرار Go/No-Go للمالك على نتيجة المنتج بأدلة تشغيل مناسبة للمهمة
  ([ADR-0011](../docs/architecture/adr/0011-production-only-quality-gates.md))؛ `R1.0`: بوابات رسمية كاملة ومراجعة مستقلة واعتمادات.
- معايير القبول على مستوى الإصدار لها أدلة في البيئة المناسبة؛ ما لم يُختبر = NOT RUN لا PASS. GitHub Actions ليس شرطاً (D2)؛
  الفحوصات في `scripts/validate/` و`tests/` متاحة لتأهيل الإصدار.
- `CHANGELOG.md` و`CURRENT_STATE.md` وتوثيق الترقية والتراجع تطابق حقيقة التشغيل عند أي إصدار.
- نشر Railway `dev` التلقائي ([ADR-0010](../docs/architecture/adr/0010-railway-dev-autodeploy-from-main.md)) ليس إطلاق إصدار.
  مرجع التخطيط القديم (`v0.1.0`↔M0 …، مُلغى) في [RELEASE_PLAN §4](../docs/history/planning-2026-10-19/RELEASE_PLAN.md).

## 6. ترتيب التنفيذ الحالي

| الترتيب | Issue | النتيجة | الاعتمادية / المانع |
|---|---|---|---|
| A | [#5] OD-01 | اعتماد المزوّد والنموذج والحساب والحدود ونطاق البيانات | محسوم 2026-10-20، عُدّلت التشكيلة في #131: Qwen Cloud، `qwen3.8-flash` (افتراضي، وبتفكير) و`deepseek-v4.1-flash-1017`، بيانات اصطناعية |
| B | [#37] | ربط أول مزوّد بأسرار Railway فقط | مفتاح المزوّد في Railway `dev` (إجراء مالك) |
| C | [#39] | قيم المزوّد الحي (الجزء المستقل عن المزوّد منجز) | #37 |
| D | [#40] | تقييم ملفات اصطناعية دون ادعاء RAG | #37 |
| E | [#41] | E2E حي وقبول المالك لـ R0.2 | #37–#40 |
| يُعاد | [#38] | انحدار المحادثة بنموذج وهمي (`tests/integration/mock_chat.py`) | بعد #37 وبعد أي ترقية LibreChat |
| بالتوازي | [#43] الجزء B، [#45] | الهوية الرسمية ثم QA واعتماد UX | #7؛ ثم #43/#44 |
| بالتوازي | [#44] | تقديم إصلاحات RTL إلى upstream ومراجعة المسرد لغوياً | موافقة المالك |
| إغلاق R0.1 | [#15]، [#17]، [#3]، [#16]، [#62]، [#59] | RW المتبقية والنسخ وحد الإنفاق؛ Windows/Ubuntu الحقيقي؛ حماية `main`؛ SC-18 الأسبوعي؛ الترقية المنضبطة؛ Project/Milestones | إجراءات مالك أو بيئة مستهدفة |

الحالة الفعلية لكل بند في [CURRENT_STATE §1–§3](CURRENT_STATE.md). ما لا يُثبت في بيئته (محادثة حية، هوية معتمدة، تجربة،
RAG وأدوات، إنتاج) يبقى NOT RUN أو Blocked ولا يُدّعى.

<!-- روابط الـ Issues (reference-style لإبقاء الصفوف قصيرة) -->
[#3]: https://github.com/faenazi/ef-ai-workspace/issues/3
[#5]: https://github.com/faenazi/ef-ai-workspace/issues/5
[#7]: https://github.com/faenazi/ef-ai-workspace/issues/7
[#8]: https://github.com/faenazi/ef-ai-workspace/issues/8
[#15]: https://github.com/faenazi/ef-ai-workspace/issues/15
[#16]: https://github.com/faenazi/ef-ai-workspace/issues/16
[#17]: https://github.com/faenazi/ef-ai-workspace/issues/17
[#31]: https://github.com/faenazi/ef-ai-workspace/issues/31
[#32]: https://github.com/faenazi/ef-ai-workspace/issues/32
[#33]: https://github.com/faenazi/ef-ai-workspace/issues/33
[#34]: https://github.com/faenazi/ef-ai-workspace/issues/34
[#35]: https://github.com/faenazi/ef-ai-workspace/issues/35
[#36]: https://github.com/faenazi/ef-ai-workspace/issues/36
[#37]: https://github.com/faenazi/ef-ai-workspace/issues/37
[#38]: https://github.com/faenazi/ef-ai-workspace/issues/38
[#39]: https://github.com/faenazi/ef-ai-workspace/issues/39
[#40]: https://github.com/faenazi/ef-ai-workspace/issues/40
[#41]: https://github.com/faenazi/ef-ai-workspace/issues/41
[#42]: https://github.com/faenazi/ef-ai-workspace/issues/42
[#43]: https://github.com/faenazi/ef-ai-workspace/issues/43
[#44]: https://github.com/faenazi/ef-ai-workspace/issues/44
[#45]: https://github.com/faenazi/ef-ai-workspace/issues/45
[#46]: https://github.com/faenazi/ef-ai-workspace/issues/46
[#47]: https://github.com/faenazi/ef-ai-workspace/issues/47
[#48]: https://github.com/faenazi/ef-ai-workspace/issues/48
[#49]: https://github.com/faenazi/ef-ai-workspace/issues/49
[#50]: https://github.com/faenazi/ef-ai-workspace/issues/50
[#51]: https://github.com/faenazi/ef-ai-workspace/issues/51
[#52]: https://github.com/faenazi/ef-ai-workspace/issues/52
[#53]: https://github.com/faenazi/ef-ai-workspace/issues/53
[#54]: https://github.com/faenazi/ef-ai-workspace/issues/54
[#55]: https://github.com/faenazi/ef-ai-workspace/issues/55
[#56]: https://github.com/faenazi/ef-ai-workspace/issues/56
[#57]: https://github.com/faenazi/ef-ai-workspace/issues/57
[#58]: https://github.com/faenazi/ef-ai-workspace/issues/58
[#59]: https://github.com/faenazi/ef-ai-workspace/issues/59
[#62]: https://github.com/faenazi/ef-ai-workspace/issues/62
