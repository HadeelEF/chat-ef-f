# Architecture Decision Records (ADR)

سجل القرارات المعمارية هو **المرجع الوحيد** للقرارات المعتمدة — لا يوجد سجل قرارات منافس في أي مكان آخر.

## الفهرس

| ADR | القرار | الحالة | التاريخ |
|---|---|---|---|
| [0001](0001-librechat-as-application-foundation.md) | LibreChat أساساً للتطبيق | Accepted | 2026-10-17 |
| [0002](0002-github-repository-as-source-of-truth.md) | مستودع GitHub مصدراً وحيداً للحقيقة | Accepted | 2026-10-17 |
| [0003](0003-ai-assisted-engineering-with-shared-agents-md.md) | هندسة بمساعدة Claude Code Cloud مع سياسة AGENTS.md مشتركة | Accepted | 2026-10-17 |
| [0004](0004-coolify-and-docker-compose-deployment.md) | النشر عبر Coolify و Docker Compose | **Superseded by ADR-0008** | 2026-10-17 |
| [0005](0005-portable-container-architecture.md) | بنية حاويات قابلة للنقل | Accepted | 2026-10-17 |
| [0006](0006-upstream-first-customization.md) | التخصيص Upstream-first دون fork دائم | Accepted | 2026-10-17 |
| [0007](0007-pin-librechat-v0.8.8-and-mongodb-8.0.md) | تثبيت LibreChat v0.8.8 و MongoDB 8.0.34 (M1) | **Accepted** — نطاق محدود: بيانات اصطناعية/عرض فقط، ليس للإنتاج (#11)؛ «لا Meilisearch» **معدَّل بـ ADR-0014** | 2026-10-18 |
| [0008](0008-multi-environment-hosting-railway-windows-ubuntu.md) | استضافة متعددة البيئات: Railway (عرض) وWindows المحلي وUbuntu في الموقع؛ يحل محل ADR-0004 | **Accepted** — D1 معتمد في #16 (2026-10-18)؛ اعتماد معماري فقط؛ الخدمات على Railway **معدَّلة بـ ADR-0014** | 2026-10-18 |
| [0009](0009-development-phase-agent-delegation.md) | تفويض الوكيل في مرحلة التطوير: الدمج والنشر على Railway `dev` | **Accepted** — تعليمات المالك الصريحة (2026-10-19)؛ شرط الدمج **معدَّل بـ ADR-0011**، والبند 3 (التسجيل) **معدَّل بـ ADR-0023** | 2026-10-19 |
| [0010](0010-railway-dev-autodeploy-from-main.md) | النشر التلقائي على Railway `dev` من `main` (watch paths، دون Wait for CI)؛ يحل محل «النشر اليدوي فقط» في D2 | **Accepted** — تعليمات المالك الصريحة (2026-10-19)؛ نتيجة «بوابة الجودة قبل النشر» **معدَّلة بـ ADR-0011** | 2026-10-19 |
| [0011](0011-production-only-quality-gates.md) | بوابات الجودة الرسمية للإنتاج فقط؛ تحقق تطويري حسب المهمة؛ يحل محل بوابة الجودة اليدوية لكل PR (D2 المعدّل) | **Accepted** — تعليمات المالك الصريحة (2026-10-19) | 2026-10-19 |
| [0012](0012-temporary-security-patch-layer.md) | طبقة ترقيع أمني مؤقتة لصورة LibreChat على Railway حتى إصدار upstream (R-01–R-04) | **Accepted** — قرار المالك (2026-10-19، #16) | 2026-10-19 |
| [0013](0013-arabic-web-client-build.md) | بناء واجهة الويب العربية لصورة Railway من مصدر LibreChat المثبّت (ترجمة كاملة وتعديلات RTL) | **Accepted** — تعليمات المالك (2026-10-20، #89) | 2026-10-20 |
| [0014](0014-conversation-search-meilisearch.md) | البحث في المحادثات: خدمة Meilisearch خاصة في كل بيئة (ثلاث خدمات على Railway) | **Accepted** — تعليمات المالك (2026-10-21، #125) | 2026-10-21 |
| [0015](0015-web-search-through-provider-built-in-search.md) | الاتصال بالإنترنت: البحث المدمج في مزوّد النموذج المعتمد (Qwen Cloud) | **Accepted** — قرار المالك (2026-10-22، #135)؛ البند 5 (مفتاح الإنترنت) **معدَّل بـ ADR-0022** | 2026-10-22 |
| [0016](0016-librechat-admin-panel.md) | لوحة الإدارة: LibreChat Admin Panel الرسمية خدمةً رابعة، وبناء أمني مؤقت لصورة Railway (CVE-2026-102989) | **Accepted** — قرارات المالك (2026-10-23، #141) | 2026-10-23 |
| [0017](0017-platform-skills-from-repository.md) | مهارات المنصّة من المستودع: `ai/skills/` يُثبَّت لكل الموظفين للقراءة فقط (مجلد النشر في LibreChat)؛ أولها هوية الصندوق | **Accepted** — طلب المالك (2026-10-23، #146) | 2026-10-23 |
| [0018](0018-ef-ready-commands-from-repository.md) | الأوامر الجاهزة الرسمية من المستودع: `ai/prompts/` تُنشأ مرة واحدة لكل الموظفين؛ النشر للجميع للمسؤول فقط | **Accepted** — طلب المالك (2026-10-24، #189) | 2026-10-24 |
| [0019](0019-google-sign-in-for-dev-testers.md) | الدخول والتسجيل الذاتي عبر Google لقائمة مختبرين في Railway `dev` | **Deprecated** — ألغاه المالك قبل التفعيل (2026-10-25، #201)؛ الدخول والتسجيل بالوضع الافتراضي (SC-10) | 2026-10-25 |
| [0020](0020-open-self-registration.md) | تفعيل التسجيل الذاتي الافتراضي في LibreChat (مفتوح، بلا حدود استهلاك)؛ يعدّل SC-10 | **Superseded** بـ ADR-0024 (2026-10-27) | 2026-10-25 |
| [0021](0021-mcp-servers-for-admins-only.md) | خوادم MCP للمسؤول فقط: سياسة أدوار تُطبَّق قبل كل إقلاع (`roles-policy.js`)؛ يعدّل SC-21 | **Accepted** — قرار المالك (2026-10-25، #218) | 2026-10-25 |
| [0022](0022-search-always-on-and-skills-as-message-text.md) | البحث في الإنترنت دائماً بلا مفتاح، والمهارة المختارة نصاً مرفقاً بالرسالة لا أدوات؛ يعدّل ADR-0015 البند 5 وADR-0017 | **Accepted** — قرار المالك (2026-10-25، #224) | 2026-10-25 |
| [0023](0023-deploy-log-on-issue-15.md) | سجل نشر `dev` على #15، و`CURRENT_STATE.md` عند تغيّر الحالة المتحققة فقط؛ يعدّل ADR-0009 البند 3 | **Accepted** — قرار المالك (2026-10-26، #235) | 2026-10-26 |
| [0024](0024-close-self-registration.md) | إغلاق التسجيل الذاتي في LibreChat؛ الحسابات ينشئها المسؤول؛ يحل محل ADR-0020 ويعدّل SC-10 | **Accepted** — قرار المالك (2026-10-27، #245) | 2026-10-27 |

## الحالات

`Proposed` (مقترح بانتظار اعتماد مالك المشروع) · `Accepted` · `Superseded by ADR-NNNN` · `Deprecated`.

قاعدة: لا يُوسم ADR بـ `Accepted` إلا إذا كان مدعوماً بقرار معتمد موثق (ميثاق المشروع أو موافقة صريحة لمالك المشروع في PR/Issue).

## إضافة ADR جديد

1. انسخ القالب أدناه إلى `NNNN-short-title.md` بالرقم التالي.
2. أضفه إلى الفهرس أعلاه في نفس الـ PR.
3. القرار الذي يستبدل قراراً سابقاً: حدّث حالة القديم إلى `Superseded by ADR-NNNN` ولا تحذفه.
4. يتحقق `scripts/validate/repo_checks.py` من الأقسام الإلزامية والفهرسة.

```markdown
# ADR-NNNN — العنوان

| Field | Value |
|---|---|
| Status | Proposed |
| Date | YYYY-MM-DD |
| Deciders | ... |
| Related | FR-/NFR-/Issue # |

## Context
## Decision
## Rationale
## Alternatives considered
## Consequences
## Verification
```
