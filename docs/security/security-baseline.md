# خط الأساس الأمني (Security Baseline)

| الحقل | القيمة |
|---|---|
| الحالة | Draft — متطلبات وضوابط مخططة؛ لا شيء معتمد من جهة أمنية بعد (SC-18 Approved بقرار المالك D5 في #16) |

> **لا ادعاء امتثال.** لا تدّعي هذه الوثيقة الامتثال لأي إطار تنظيمي أو أمني سعودي (مثل ضوابط NCA أو نظام PDPL).
> تحديد الإطار المطبّق ونطاقه يتطلب اعتماد فريق الأمن/الالتزام (UR-06).

## 1. مقياس حالة الضوابط

| الحالة | المعنى | الدليل المطلوب |
|---|---|---|
| `Requirement` | متطلب موثق دون تصميم ضابط | مرجع FR/NFR |
| `Planned` | ضابط مصمم ومُسند لمرحلة | Issue/ADR |
| `Implemented` | موجود في الكود/الإعداد | commit/PR |
| `Tested` | اختُبر آلياً أو يدوياً | سجل اختبار/CI run |
| `Approved` | اعتمدته جهة مختصة | مرجع الاعتماد |

## 2. سجل الضوابط

| ID | المجال | الضابط | الحالة | الدليل / المرحلة |
|---|---|---|---|---|
| SC-01 | الأسرار | لا أسرار في Git؛ `.gitignore` يمنع `.env` والمفاتيح؛ وكلاء Claude Code ممنوعون من قراءة ملفات الأسرار مع إتاحة `.env.example` | Implemented + Tested (cloud session) | `.gitignore`، `.claude/settings.json`، `repo_checks.py forbidden settings`، gitleaks |
| SC-02 | الأسرار | فحص أسرار لتاريخ Git كاملاً (`gitleaks`) | Implemented + Tested (cloud session)؛ يُشغَّل في التطوير عند التغييرات التي قد تمس الأسرار، وإلزامي في بوابات الإنتاج (ADR-0011) | `.github/workflows/security.yml`؛ `scripts/validate/run-all.sh` |
| SC-03 | التوصيل الآمن | Actions مثبتة بـ SHA، صلاحيات `{}` افتراضياً، `persist-credentials: false`، أدوات بـ checksum/hash | Implemented + Tested (cloud session)؛ الـ workflows باقية للاستخدام الاختياري ومُدقّقة (zizmor/actionlint) دون تشغيل على GitHub | `ci.yml`, `security.yml`, zizmor, actionlint |
| SC-04 | التوصيل الآمن | قاعدة GitHub تمنع direct push/force-push وحذف `main`، وتشترط PR وحل المحادثات، دون GitHub Actions أو موافقة يتعذر تحقيقها لمطور منفرد | **NOT VERIFIED** — إجراء مالك P0؛ rulesets `[]` (2026-10-19) | [#3](https://github.com/faenazi/ef-ai-workspace/issues/3)؛ حرج لأن `main` ينشر Railway تلقائياً (ADR-0010) |
| SC-05 | الأسرار | الأسرار وقت التشغيل خارج Git بقيم فريدة لكل بيئة: `.env` محلي (`new-env.sh`)؛ Railway `preserve()` عبر `railway-secrets.sh` | Implemented + Tested (cloud session)؛ Railway Verified (target environment) | `${VAR:?}`؛ T02؛ `railway_checks.py` يرفض سراً حرفياً؛ T34/R25 لا أسرار في السجلات؛ [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| SC-06 | الشبكة | لا منافذ منشورة لـ MongoDB/Meilisearch/RAG/pgvector ولا لأدوات إدارة قواعد البيانات؛ نقطة دخول واحدة لكل بيئة، ولوحة الإدارة ([ADR-0016](../architecture/adr/0016-librechat-admin-panel.md)) خلفها وعلى frontend فقط | Implemented + Tested (cloud session) | `compose_checks.py`؛ T20–T24، T44، O01–O02؛ N31، N33؛ Railway: `railway_checks.py`، R09 |
| SC-07 | الشبكة | HTTPS لكل وصول غير محلي: Railway edge (`*.up.railway.app`)؛ Caddy في الموقع مع HSTS وتحويل HTTP→HTTPS؛ محلياً loopback فقط | On-prem: Implemented + Tested (cloud session, CA داخلية — O03–O06)؛ Railway: Configured، **NOT RUN** (#15)؛ CA مؤسسية على خادم حقيقي NOT RUN (#17) | [deployment.md](../operations/deployment.md) |
| SC-08 | البيانات | MongoDB بمصادقة + مستخدم تطبيق `readWrite` على قاعدته فقط | Implemented + Tested (cloud session) | T06–T09 |
| SC-09 | الحاويات | صور رسمية مثبتة بـ tag + digest؛ صور Railway المشتقة `FROM` نفس الـ digest؛ تحديثات عبر Dependabot (major لـ MongoDB مستبعد) | Implemented + Tested (cloud session) | `compose_checks.py`؛ `railway_checks.py`؛ T04، R02 |
| SC-10 | الهوية | التسجيل الذاتي مغلق بقرار المالك ([ADR-0024](../architecture/adr/0024-close-self-registration.md))، الحسابات ينشئها المسؤول؛ Entra ID OIDC للإنتاج | Implemented + Tested (cloud session) (T13–T15، R16–R17، M06)؛ M6: Planned | `ALLOW_REGISTRATION=false`، لا دخول اجتماعي؛ `OPENID_*` لاحقاً |
| SC-11 | الصلاحيات | RBAC مبني على مجموعات Entra؛ فصل المسؤول | Requirement | OD-03 |
| SC-12 | التدقيق | سجل تدقيق للدخول والإدارة والوصول | Requirement — **فجوة upstream** | `AuditLog` في v0.8.8 يسجل 4 إجراءات إدارية فقط |
| SC-13 | الاحتفاظ | سياسة احتفاظ للمحادثات والملفات | Requirement | `interface.generalChatRetention` متاح؛ السياسة OD-07 |
| SC-14 | النسخ والاستعادة | نسخ احتياطي مشفّر واستعادة مجرّبة | Compose: Tested (cloud session) — local + on-prem (T28–T33)؛ Railway volume backups: Configured في الإجراء، NOT RUN (#15)؛ التشفير والجدولة والوجهة: Planned M6 | [operations/runbook.md](../operations/runbook.md) |
| SC-15 | إقامة البيانات | بيانات الإنتاج داخل المملكة؛ كل وجهة Z4 مقيّمة | Requirement | [data-flow.md](../architecture/data-flow.md#3-ملخص-بيانات-تغادر-البنية) |
| SC-16 | المراقبة | سجلات مركزية وتنبيهات | Requirement | M6 |
| SC-17 | حدود الاستخدام | حدود معدل ورصيد لكل مستخدم | Planned M6؛ حدود upstream الافتراضية للرسائل والتزامن **غير مفعّلة**، الدخول 7/5 دقائق فعّال — القيم قرار المالك مع #5 ([ai-safe-defaults §7](../architecture/ai-safe-defaults.md#7-قرارات-مفتوحة-لا-قيم-مخترعة)) | `rateLimits`, `balance.*`, `LIMIT_*` |
| SC-18 | الحاويات | فحص ثغرات الصور (أسبوعياً، عند تغيير digest، قبل أي تعريض عام) مع تقييم وصول لكل CVE؛ لا تعريض عام مع CRITICAL قابلة للوصول دون قبول منفصل | **Approved** (D5، #16)؛ Implemented (report-only) + Tested (cloud session) | [السجل](vulnerability-register.md)، [خطة المعالجة](cve-remediation-plan.md)، `image-scan.sh` |
| SC-19 | إقامة البيانات | Railway بيئة عرض فقط خارج المملكة: بيانات اصطناعية فقط، لا مفاتيح نماذج حقيقية ببيانات مصنفة | Requirement + Planned (#15) — يُفرض إجرائياً، لا تقنياً | ADR-0008، NFR-PRIV-01 |
| SC-20 | الحاويات | حراس بدء ترفض التشغيل دون الأسرار (لا تهيئة MongoDB بلا مصادقة)؛ LibreChat على Railway يعمل كمستخدم غير root | Implemented + Tested (cloud session) | `infrastructure/railway/*-start.sh`؛ R04–R05، R12 |
| SC-21 | الصلاحيات | أقل امتياز لأدوات AI: الوكلاء وSkills والذاكرة بمشاركة داخلية (#108)؛ MCP للمسؤول فقط بلا مشاركة (ADR-0021)؛ الأفعال وMCP للموظف والبحث وتشغيل الكود والبحث في الملفات مغلقة (403)؛ لا نص لخطأ المزوّد | Implemented + Tested (cloud session) (#39، #108، #218) | `librechat.yaml`، `roles-policy.js`؛ M22–M36، M92–M93؛ [ai-safe-defaults](../architecture/ai-safe-defaults.md) |
| SC-22 | حماية البيانات | الرسالة وإجابة السؤال التوضيحي ونص الملف تُرفض قبل النموذج والتخزين إن طابقت رقم هوية أو إقامة، أو آيبان سعودياً، أو مفتاح API، أو رمز Bearer. شبكة أمان لا تغني عن البيانات الاصطناعية (NFR-PRIV-01) | Implemented + Tested (cloud session) (#129) | `librechat.yaml` (`filters`)؛ M60، M61، M63؛ [ai-safe-defaults](../architecture/ai-safe-defaults.md) |
| SC-23 | الصلاحيات | إعدادات المنصة في Git فقط: لا تجاوزات إعدادات في MongoDB (`configs`) ولا دور مخصص يسمح بأكثر من دور USER المأخوذ من `librechat.yaml` (قرار المالك، #141) | Implemented + Tested (cloud session) | `scripts/operations/admin-config-drift.sh`؛ M81، T49 |

## 3. ضوابط خاصة بالذكاء الاصطناعي

| ID | الخطر | الضابط المخطط | المرحلة |
|---|---|---|---|
| AI-01 | إرسال بيانات مصنفة لمزوّد غير معتمد | قائمة مزوّدين معتمدة لكل تصنيف؛ بيانات اصطناعية في العرض | M3 |
| AI-02 | Prompt injection (مباشر وغير مباشر عبر الملفات/الأدوات) | تعليمات نظام محصّنة، عزل محتوى الأدوات، تأكيد بشري للإجراءات ذات الأثر، اختبارات evals عدائية | M5 |
| AI-03 | صلاحيات أدوات/MCP زائدة | أقل امتياز (MCP للمسؤول فقط بلا مشاركة، `roles-policy.js`، ADR-0021)، قائمة خوادم معتمدة، `mcpSettings.allowedDomains` | M5 |
| AI-04 | تسريب معلومات حساسة في الإجابات أو السجلات | تصنيف البيانات، عدم تسجيل المحتوى الحساس في السجلات التشغيلية | M6 |
| AI-05 | Artifacts تنفّذ كوداً وتحمّل من CDN عام | استضافة Sandpack ذاتياً أو تعطيل | M4 |
| AI-06 | مهارات/وكلاء غير معتمدين | التعريفات المعتمدة في المستودع + مراجعة PR + كشف الانحراف | M5 |
| AI-07 | SSRF عبر نقاط النهاية المخصصة | `endpoints.allowedAddresses` و`mcpSettings.allowedAddresses` بالحد الأدنى | M3 |

## 4. وثائق مرتبطة

[SECURITY.md](../../SECURITY.md) (الإبلاغ والقواعد) · [data-handling.md](data-handling.md) (التصنيف والتعامل) ·
[NFRs](../product/non-functional-requirements.md).
