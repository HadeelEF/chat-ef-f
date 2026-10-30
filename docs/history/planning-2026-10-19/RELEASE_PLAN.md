# خطة الإصدارات (Release Plan)

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس حالة حالية ولا سياسة.** الحالة الحية: [project/CURRENT_STATE.md](../../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](../README.md).

| البيان | الحالة |
|---|---|
| اعتماد اتجاه المنتج | **Approved** — 2026-10-19 ([PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md)) |
| إصدار برمجي منشور بتسمية Git | **لا وسم جديد ضمن اعتماد هذه الخطة** |
| تاريخ الإصدارات | TBD؛ لا تواريخ مخترعة |
| الحقيقة التشغيلية | [CURRENT_STATE.md](../2026-10-20-current-state-ledger.md) |
| بوابات الجودة | **الإنتاج فقط** ([ADR-0011](../../../docs/architecture/adr/0011-production-only-quality-gates.md))؛ [DoD](../../../docs/quality/definition-of-done.md) و[Delivery Governance](delivery-governance.md) |

## 1. فرق أساسي بين ثلاثة أنواع من المعرّفات

1. **Product Increment R0.1–R1.0:** نتيجة قابلة للعرض/الاختبار؛ مرجعها
   [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md). **ليست** Git tag ولا نسخة LibreChat.
2. **Engineering Milestone M0–M8:** مسار هندسي وتاريخ توثيقي؛ مرجعه [ROADMAP.md](../../../project/ROADMAP.md).
   قد يقطع Product Release أكثر من M والعكس؛ M3 (LLM) يبدأ قبل انتهاء M2 (Branding).
3. **Software version `vMAJOR.MINOR.PATCH` (SemVer):** وسم GitHub Release مستقبلي يُصدر فقط بعد
   قرار مالك المشروع واجتياز بواباته؛ مستقل عن إصدار LibreChat upstream `v0.8.8`.

لا تعيد تسمية tags قديمة أو تنشئ tag لمجرد أن Epic مُغلق.

## 2. Product Release Register

| Release | القيمة | Epic / إثبات | قرار التقدم |
|---|---|---|---|
| R0.1 | أساس LibreChat/Railway | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15), [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) | أساس منفذ؛ اختبارات إغلاق معلقة |
| **R0.2 NEXT** | أول AI chat فعلي | [#31](https://github.com/faenazi/ef-ai-workspace/issues/31) + [#5](https://github.com/faenazi/ef-ai-workspace/issues/5) | Planned/blocked on OD-01 |
| R0.3 | هوية رسمية وRTL/UX | [#32](https://github.com/faenazi/ef-ai-workspace/issues/32) + [#7](https://github.com/faenazi/ef-ai-workspace/issues/7) | Planned |
| R0.4 | تجربة موظفين محدودة ببيانات اصطناعية | [#33](https://github.com/faenazi/ef-ai-workspace/issues/33) | Planned — security gate first |
| R0.5 | تعليمات مؤسسية، RAG وSkills | [#34](https://github.com/faenazi/ef-ai-workspace/issues/34) | Planned |
| R0.6 | RFP ثم مساعدين آخرين | [#35](https://github.com/faenazi/ef-ai-workspace/issues/35) | Planned |
| R1.0 | Enterprise Saudi production | [#36](https://github.com/faenazi/ef-ai-workspace/issues/36) | Planned — formal approvals |

## 3. Gates before any software tag or release announcement

**R0.x (تطوير/اختبار/عرض):** لا بوابة جودة رسمية ([ADR-0011](../../../docs/architecture/adr/0011-production-only-quality-gates.md))؛
قرار المالك Go/No-Go على نتيجة المنتج بأدلة تشغيل مناسبة للمهمة. **R1.0 (الإنتاج):** بوابات جودة رسمية كاملة
([DoD §2](../../../docs/quality/definition-of-done.md#2-الإنتاج--بوابات-الجودة-الرسمية-planned-قبل-أي-go-live)) ومراجعة مستقلة واعتمادات.

- Release-level ACs لها أدلة تشغيل صحيحة في البيئة المناسبة؛ نقص الاختبار = NOT RUN وليس PASS.
- **GitHub Actions ليس شرطاً** (قرار D2)؛ الفحوصات الآلية في `scripts/validate/` و`tests/` متاحة لتأهيل الإصدار.
- `CHANGELOG.md` و`CURRENT_STATE.md` وتوثيق الـ upgrade/rollback يطابقان حقيقة التشغيل.
- مالك المنتج يسجل قرار Go/No-Go مستقل لكل Product Release وGitHub Release، مع المخاطر المؤجلة.
- **Production** يحتاج بيئة سعودية معتمدة وSSO/RBAC/Audit/DR وقرار أمني مستقل واجتياز M6/M8؛ لا يسمح بالبيانات الحقيقية قبل ذلك.
- Railway `dev` autodeploy للصور فقط من watched `main` وفق
  [ADR-0010](../../../docs/architecture/adr/0010-railway-dev-autodeploy-from-main.md)، ولا يعني إطلاق نسخة منتج.

## 4. Historical planning reference (2026-10-18, superseded)

كانت مسودة الخطة القديمة تربط `v0.1.0` بـ M0، و`v0.2.0` بـ M1/M1.1،
و`v0.3.0` بـ M2، و`v0.4.0+` بـ M3–M5، و`v0.9.0` بـ M6، و`v1.0.0` بـ M8.
**هذه قيم تخطيط تاريخية ولم تُعتبر وسوماً منشورة هنا**؛ لا تستخدمها كحالة المنتج الحالية أو كأدلة CI.
سجل التنفيذ الحقيقي باقٍ في commits/PRs/CHANGELOG، وتعريف Product Releases الآن `R0.x`.
