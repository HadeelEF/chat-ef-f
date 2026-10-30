# Baseer Delivery Plan v1.0 — خطة تنفيذ R0.2 / R0.3

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس حالة حالية ولا سياسة.** الحالة الحية: [project/CURRENT_STATE.md](../../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](../README.md).

**State:** Approved planning sequence (2026-10-19), **not execution evidence**.
**Source of product scope:** [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md).
**Source of task status:** live GitHub Issues; runtime status: [CURRENT_STATE.md](../2026-10-20-current-state-ledger.md).
**Due dates:** TBD, no invented duration.

> آخر مراجعة لإغلاق المراحل السابقة: [Foundation Closure Audit](../reports/2026-10-19-foundation-closure-audit.md).
> **R0.1 أساس منشور وليس إغلاقاً كاملاً**: RW/Backups/Windows/Ubuntu والحماية ما زالت تتطلب أدلة؛
> لا ترفع مستوى "Verified" بسبب وجود تقرير أو دمج PR.

## 1. نقطة البداية

موجود في Railway `dev`: LibreChat v0.8.8 + MongoDB 8.0.34، مسؤول `fahad`،
التسجيل العام مغلق، النشر التلقائي لمدخلات صور Docker من `main` وفق
[ADR-0010](../../../docs/architecture/adr/0010-railway-dev-autodeploy-from-main.md).
**لا يوجد LLM provider مفعّل؛ لا محادثة ذكاء تعمل حتى R0.2**. No real EF data / tenant / approved production environment.

## 2. المسار الحرج — R0.2 AI Activation

| الترتيب | Issue | النتيجة | Ready/Blocked عند اعتماد الخطة |
|---|---|---|---|
| A | [#5 OD-01](https://github.com/faenazi/ef-ai-workspace/issues/5) | اعتماد provider/model/account/limits/نطاق البيانات | **Owner decision — OPEN** |
| B (بالتوازي) | [#38](https://github.com/faenazi/ef-ai-workspace/issues/38) | اختبارات deterministic mock للنموذج والمحادثات | **READY**، بلا API key |
| C | [#37](https://github.com/faenazi/ef-ai-workspace/issues/37) | ربط أول Provider مع أسرار Railway فقط | **BLOCKED #5** |
| D | [#39](https://github.com/faenazi/ef-ai-workspace/issues/39) | نماذج افتراضية وحدود استخدام/أخطاء | **الجزء المستقل منجز (PR #68)**؛ قيم المزوّد الحي **WAIT #5/#37** |
| E | [#40](https://github.com/faenazi/ef-ai-workspace/issues/40) | تقييم ملفات اصطناعية دون ادعاء RAG | **WAIT #37** |
| F | [#41](https://github.com/faenazi/ef-ai-workspace/issues/41) | اختبار E2E حي وقبول مالك R0.2 | **WAIT #37–#40** |

**Acceptance:** login → authorized model → streamed AR/EN answer → reopen saved chat; failures, usage limits,
no exposed secrets, user/session isolation, target evidence, rollback and explicit owner go/no-go.

## 3. R0.3 Branding — أعمال قابلة للتوازي

| Issue | العمل | القرار |
|---|---|---|
| [#7 D-04](https://github.com/faenazi/ef-ai-workspace/issues/7) | أصول وموافقات الهوية والخطوط والاسم الرسمي | **OPEN** |
| [#42](https://github.com/faenazi/ef-ai-workspace/issues/42) | تحليل حدود التخصيص وشاشات LibreChat وفق ADR-0006 | **READY** للتحليل |
| [#44](https://github.com/faenazi/ef-ai-workspace/issues/44) | تدقيق الترجمات/RTL/Accessibility | **التدقيق والمسرد منجزان (PR #70)**؛ الإصلاحات upstream تنتظر موافقة المالك |
| [#43](https://github.com/faenazi/ef-ai-workspace/issues/43) | تطبيق الهوية الرسمية | الجزء A (إخفاء L1) **منشور (PR #69)**؛ الهوية الرسمية **BLOCKED #7** |
| [#45](https://github.com/faenazi/ef-ai-workspace/issues/45) | QA واعتماد UX | **WAIT #43/#44** |

قد تبدأ تعليمات تعريف عامة **من حقائق عامة معتمدة** في R0.3،
لكن RAG المعرفة الموثقة وSkills runtime مُخططان لـ R0.5.

## 4. Closure دون تعطيل قيمة R0.2

- [#15](https://github.com/faenazi/ef-ai-workspace/issues/15): Railway RW checks، Backups، توثيق dashboard spend limits.
- [#17](https://github.com/faenazi/ef-ai-workspace/issues/17): Windows/Ubuntu في المضيف الحقيقي.
- [#3](https://github.com/faenazi/ef-ai-workspace/issues/3): قواعد حماية `main` للمطور الواحد؛ لا GitHub Actions إلزامية.
- [#16](https://github.com/faenazi/ef-ai-workspace/issues/16): SC-18؛ R-01–R-04 مُعالجة على Railway `dev` (ADR-0012، 2026-10-19)، R-05 غير متأثرة؛ فحص أسبوعي.
- [PR #19](https://github.com/faenazi/ef-ai-workspace/pull/19) **أُغلق دون دمج**؛ الترقية المنضبطة للصور الثلاثية/الاستعادة والأمن في [#62](https://github.com/faenazi/ef-ai-workspace/issues/62).
- [#59](https://github.com/faenazi/ef-ai-workspace/issues/59): Native GitHub Project / Milestones pending tool support.

## 5. ما بعد R0.3

- **R0.4** [#33](https://github.com/faenazi/ef-ai-workspace/issues/33): لا تجربة قبل مرور بيانات/أمن/دعوات [#46](https://github.com/faenazi/ef-ai-workspace/issues/46).
- **R0.5** [#34](https://github.com/faenazi/ef-ai-workspace/issues/34): public institutional instructions → synthetic RAG → Skills/MCP/Artifacts.
- **R0.6** [#35](https://github.com/faenazi/ef-ai-workspace/issues/35): Assistant framework → RFP → technical evaluation/contracts/finance discovery.
- **R1.0** [#36](https://github.com/faenazi/ef-ai-workspace/issues/36): production Saudi residency, Entra, RBAC, audit, DR + independent approval.

## 6. كيفية التنفيذ في جلسة جديدة

1. ابدأ من [START_HERE.md](../../../project/START_HERE.md) و[AGENTS.md](../../../AGENTS.md)، ثم اقرأ CURRENT_STATE والأعمال المفتوحة مباشرة.
2. اختر Issue واحدة **Ready**؛ لا تنفذ Provider قبل #5 ولا Brand رسمي قبل #7.
3. نفّذ على فرع خاص مع FR/NFR وACs، وتحقق بما تحتاجه المهمة واذكر ما شُغّل فعلاً.
4. افتح PR واضحاً صغيراً مع rollback؛ **لا بوابة جودة رسمية ولا GitHub Actions في التطوير** ([ADR-0011](../../../docs/architecture/adr/0011-production-only-quality-gates.md))، و[DoD](../../../docs/quality/definition-of-done.md) يحدد الإنجاز.
5. دمج `main` قد ينشر مباشرة صورة Railway (ADR-0010) إذا تغيرت watched paths؛ اختبر قبل الدمج.
6. لا تُحدّث CURRENT_STATE بحالة `Verified (target environment)` إلا بعد اختبار فعلي، ولا تُغلق بوابة الإصدار اعتماداً على التوثيق.

## 7. Evidence matrix

| مجال | المطلوب لإثباته | إن تعذّر |
|---|---|---|
| Model/chat | redacted config + live AR/EN test, stable chat history, failures | NOT RUN؛ لا تدّع محادثة حية |
| Brand/RTL | approved provenance, desktop/mobile screenshots, accessibility | يبقى Planned/Blocked |
| Pilot | approved synthetic scripts/accounts, permission review, feedback | لا دعوات |
| RAG/tools | synthetic corpus, citations, ACL/egress and injection evals | Blocked |
| Production | Saudi target, SSO, independent security/DR signoff | لا بيانات حقيقية |
