# أصول الذكاء الاصطناعي وقت التشغيل (Runtime AI Assets)

| الحقل | القيمة |
|---|---|
| الحالة | مهارة المنصة `ef-brand-guidelines` (#146، [ADR-0017](../docs/architecture/adr/0017-platform-skills-from-repository.md))؛ الأوامر الجاهزة الرسمية (#189، [ADR-0018](../docs/architecture/adr/0018-ef-ready-commands-from-repository.md)) |
| آخر تحقق من آليات LibreChat | 2026-10-24، مصدر v0.8.8 |

## 1. الفصل الصارم بين نوعي المهارات

| | مهارات التطوير (Development Skills) | مهارات المنصّة (Runtime AI Skills) |
|---|---|---|
| الموقع | `.claude/skills/` (+ `.agents/skills` رابط رمزي لـ Codex) | `ai/skills/` |
| المستخدم | وكلاء البرمجة (Claude Code / Codex) لبناء المستودع | المساعدون داخل EF AI Workspace لخدمة الموظفين |
| النشر | تُقرأ من المستودع مباشرة | تُنشر إلى LibreChat عبر آلية مدعومة (أدناه) |

**لا تُخلط مسؤولياتهما.** مهارة تطوير لا تُرفع إلى LibreChat، ومهارة منصّة لا تُستخدم لتوجيه وكيل البرمجة.

## 2. الهيكل المخطط (يُنشأ عند أول أصل فعلي — لا مجلدات فارغة)

```text
ai/
├── agents/<agent-id>/       تعريف الوكيل المعتمد (تعليمات، نموذج، أدوات، مهارات، مالك، نسخة)
├── skills/<skill-name>/     SKILL.md (+ ملفات داعمة) بصيغة LibreChat Skills
├── prompts/                 الأوامر الجاهزة الرسمية (ef-templates.json)
├── knowledge/synthetic/     بيانات معرفة اصطناعية فقط (P0)
└── evals/<asset>/           مجموعات تقييم لكل أصل
```

## 3. آليات LibreChat المدعومة (متحقق منها في v0.8.8)

| الأصل | آليات مدعومة | ما **لا** يعمل |
|---|---|---|
| Skills | (أ) رفع عبر الواجهة (`.md`/`.zip`/`.skill`)؛ (ب) `POST /api/skills/import`؛ (ج) مجلد مُركّب `DEPLOYMENT_SKILLS_DIR` (افتراضي `./skill`) — للقراءة فقط ويتطلب إعادة تشغيل، وملف غير صالح يوقف الإقلاع؛ (د) مزامنة GitHub عبر `skillSync.github` في `librechat.yaml` | مهارة من مجلد النشر لا تُعدّل ولا تُحذف من الواجهة |
| Agents | Agent Builder في الواجهة؛ Agent Management API (`/api/agents/v1/agents`، **beta**، OIDC machine tokens) | **لا استيراد/seed من ملفات** — وضع ملف في المستودع لا ينشئ وكيلاً |
| MCP servers | `mcpServers` في `librechat.yaml` (إعداد دائم من المستودع) | — |
| Prompts (أوامر جاهزة) | الواجهة؛ `POST /api/prompts` ثم المشاركة؛ دوال LibreChat من سكربت داخل الحاوية (`createPromptGroup` و`grantPermission`) | لا مجلد نشر ولا seed في upstream؛ قوائم v0.8.8 لا تعيد `command` (أُصلح بعد v0.8.8) |

**تنبيه:** وجود ملف في GitHub **لا يعني** نشره في LibreChat. حالة النشر تُسجّل لكل أصل.

## 4. نهج المزامنة وكشف الانحراف (Planned — M5)

1. **المصدر المعتمد:** التعريف في `ai/` بعد دمج PR معتمد.
2. **النشر:**
   - Skills: `ai/skills/` هو مجلد النشر (`/app/skill`): يُنسخ في صورة Railway ويُربط للقراءة فقط في Compose
     ([ADR-0017](../docs/architecture/adr/0017-platform-skills-from-repository.md)). يُفحص قبل الدمج بـ `repo_checks.py platform-skills`.
   - Prompts: `ai/prompts/ef-templates.json` يُنشأ مرة واحدة لكل الموظفين عند الإقلاع، ثم يملكه المسؤول في الواجهة
     ([ADR-0018](../docs/architecture/adr/0018-ef-ready-commands-from-repository.md)).
   - Agents: سكربت يستخدم Agent Management API إذا ثبت استقراره، وإلا إجراء يدوي موثق بقائمة تحقق.
3. **كشف الانحراف:** سكربت مجدول يقرأ الحالة من LibreChat (API) ويقارنها بالمستودع (hash للتعليمات والإعداد)، ويفتح Issue عند الاختلاف.
4. **التغييرات من الواجهة:** أي تعديل يتم مباشرة في LibreChat يُعتبر انحرافاً يجب إرجاعه إلى المستودع عبر PR أو التراجع عنه.

## 5. الحوكمة

كل أصل يحتاج: مالك أعمال، تصنيف البيانات التي يصل إليها، الأدوات المسموحة، مجموعة تقييم، ونسخة. انظر
[security-baseline.md](../docs/security/security-baseline.md#3-ضوابط-خاصة-بالذكاء-الاصطناعي) و
[testing-strategy.md](../docs/quality/testing-strategy.md#3-استراتيجية-تقييم-الذكاء-الاصطناعي-ai-evals--planned).

## 6. الأصول المنشورة

| الأصل | النوع | المالك | البيانات | الأدوات | التقييم | النسخة |
|---|---|---|---|---|---|---|
| [`ef-brand-guidelines`](skills/ef-brand-guidelines/SKILL.md) | مهارة منصة، `always-apply` | الاتصال المؤسسي (TBD)؛ المستودع @faenazi | لا بيانات: قواعد عامة من دليل الهوية الإصدار 01 | لا أدوات | `mock_chat.py` M83–M85؛ فحص الواجهة في #146 | Git (#146) |
| [`ef-templates.json`](prompts/ef-templates.json) | 8 أوامر جاهزة رسمية للجميع | TBD؛ المستودع @faenazi | لا بيانات: قوالب كتابة عامة | لا أدوات | `mock_chat.py` M87–M90؛ فحص الواجهة في #189 | Git (#189) |
