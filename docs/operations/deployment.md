# البيئات والنشر (Environments & Deployment)

| الحقل | القيمة |
|---|---|
| الحالة | ثلاث بيئات وفق [ADR-0008](../architecture/adr/0008-multi-environment-hosting-railway-windows-ubuntu.md)؛ Railway `dev` **منشور برابط عام** ببيانات اصطناعية ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15))؛ Windows وUbuntu الحقيقيان **NOT RUN** ([#17](https://github.com/faenazi/ef-ai-workspace/issues/17)) |
| الإعداد المرجعي | [`infrastructure/`](../../infrastructure/README.md) + [`.railway/railway.ts`](../../.railway/railway.ts) — المصدر الوحيد للإعداد |

## 1. البيئات

| البيئة | الغرض | الاستضافة | البيانات | الدليل | الحالة |
|---|---|---|---|---|---|
| **A — Railway** | تطوير/اختبار/عرض سحابي (**ليست إنتاجاً**) | Railway Pro، منطقة EU West (لا منطقة سعودية) | **اصطناعية فقط** | [railway.md](railway.md) | IaC + نشر تلقائي من `main` لمدخلات الصور (ADR-0010)؛ الحالة المتحققة في [CURRENT_STATE](../../project/CURRENT_STATE.md) و[#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| **B — Windows 11 محلي** | محطة المطوّر | **Ubuntu WSL2 + Docker Engine/Compose** (D4 معتمد؛ Docker Desktop غير مدعوم) | اصطناعية | [windows-local.md](windows-local.md) | Compose مُختبر في جلسة السحابة؛ Windows حقيقي في [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) |
| **C — Ubuntu في الموقع** | استضافة داخلية مستقبلية | Ubuntu Server LTS + Docker Engine + Caddy HTTPS | اصطناعية حتى بوابات M6/M8 | [ubuntu-onprem.md](ubuntu-onprem.md) | Compose مُختبر في جلسة السحابة؛ خادم حقيقي في #17 |
| Cloud dev (Claude Code) | بناء واختبار آلي | حاوية سحابية مؤقتة | اصطناعية | — | تُشغَّل فيها كل الاختبارات أعلاه |
| CI (GitHub Actions) | — | — | — | [definition-of-done.md](../quality/definition-of-done.md#التحقق-المناسب-للمهمة-إرشاد-هندسي-ليس-بوابة) | **غير مستخدم** (قرار المالك، #16 D2 المعدّل)؛ في التطوير تحقق مناسب للمهمة في جلسة السحابة ([ADR-0011](../architecture/adr/0011-production-only-quality-gates.md))؛ الـ workflows باقية |
| Production | استخدام فعلي | بنية سعودية معتمدة (OD-05) | حقيقية | — | Future (M8). **لا ادعاء جاهزية إنتاجية** |

Coolify **لم يعد هدف نشر** (ADR-0004 → Superseded). سجله التاريخي في Git وفي [تقرير M1](../history/reports/M1-delivery-report.md).

## 2. منصّة واحدة، ثلاث استضافات

| الطبقة | المسار | يستخدمه |
|---|---|---|
| إعداد التطبيق المشترك | `infrastructure/common/librechat.yaml`، `librechat.env` (سياسة غير سرية)، `mongo-init/` | الكل |
| Docker Compose | `infrastructure/compose/compose.yaml` + `compose.local.yaml` / `compose.onprem.yaml` + `Caddyfile` | Windows، Ubuntu |
| Railway | `.railway/railway.ts` + `infrastructure/railway/*.Dockerfile` و`*-start.sh` | Railway |
| الأسرار | `.env` محلي (git-ignored) بـ `new-env.sh`؛ متغيرات Railway بـ `railway-secrets.sh` | لكل بيئة قيمها |

**الصور (ADR-0007، ADR-0014):** `ghcr.io/librechat-ai/librechat:v0.8.8@sha256:5b706bce…` و`mongo:8.0.34@sha256:4a4ab5d4…`
و`getmeili/meilisearch:v1.54.3@sha256:e68913ab…` و`ghcr.io/librechat-ai/librechat-admin-panel:82fb4b6…@sha256:75b30880…` (لوحة الإدارة، [ADR-0016](../architecture/adr/0016-librechat-admin-panel.md)) — Railway يبني `FROM` نفس الـ digest بالضبط (يُفرض بـ `railway_checks.py`)؛ صورة اللوحة على Railway بناء أمني مؤقت. Caddy (on-prem فقط): `caddy:2.11.7-alpine@sha256:d8542f48…`.

**ضوابط مشتركة مُطبّقة ومُختبرة:** MongoDB بـ `--auth` ومستخدم تطبيق `readWrite` على قاعدته فقط وبلا وصول عام؛ Meilisearch خاصة
بمفتاح رئيسي (البحث في المحادثات)؛ أسرار إلزامية بلا قيم افتراضية؛ الدخول الاجتماعي معطّل (التسجيل الذاتي مغلق، ADR-0024)، وروابط المشاركة خلف
الدخول فقط؛ healthchecks؛ نسخة واحدة؛
صور مثبتة بالـ digest. التفاصيل والأدلة: [security-baseline.md](../security/security-baseline.md).

## 3. إنشاء أول مسؤول (كل البيئات)

التسجيل الذاتي مغلق ([ADR-0024](../architecture/adr/0024-close-self-registration.md))، فكل حساب ينشئه المسؤول بهذا الأمر. في LibreChat v0.8.8
**أول مستخدم في قاعدة فارغة يحصل على ADMIN**، واللاحقون USER. **أنشئ المسؤول بالأمر أدناه قبل أن تصبح البيئة قابلة للوصول.** الأمر واحد، يتغير مكان تشغيله:

| البيئة | أين |
|---|---|
| Windows (WSL2) | داخل WSL: `docker compose -f compose.yaml -f compose.local.yaml exec librechat npm run create-user -- …` |
| Ubuntu / WSL | `docker compose -f compose.yaml -f compose.onprem.yaml exec librechat npm run create-user -- <email> "<name>" <username> --email-verified=true` |
| Railway | `railway ssh --service librechat` ثم `npm run create-user -- …` |

يطلب كلمة المرور تفاعلياً (لا تمررها في سطر الأوامر). هويات اصطناعية فقط (`@example.invalid`) في بيئات غير معتمدة.
مُختبر: T16–T19 (Compose)، R18–R19 (محاكاة Railway). بعدها ينشئ أي مستخدم حسابه من رابط التسجيل في صفحة الدخول بدور USER (T14، R17).

**لوحة الإدارة** (مجموعات وأدوار مخصصة ومنح): العناوين وما يُسمح به وفحص الانحراف في [runbook.md §6](runbook.md#6-لوحة-الإدارة-admin-panel--adr-0016). اللوحة لا تنشئ الحسابات على v0.8.8، فيبقى `create-user` أعلاه هو الطريق.

## 4. ربط نموذج دون كشف بيانات الاعتماد (M3)

1. اعتماد المزوّد في OD-01 ([scope.md](../product/scope.md)): المعتمد للعرض Qwen Cloud بثلاثة نماذج للموظفين (#37).
2. endpoint في `infrastructure/common/librechat.yaml` يشير إلى `apiKey: '${QWEN_API_KEY}'` (مسار مراقَب: الدمج ينشر `dev`).
3. المفتاح سرّ في كل بيئة فقط: `.env` (Compose: `QWEN_API_KEY`، اختياري محلياً)، ومتغير `preserve()` في `railway.ts` يضيفه المالك من
   لوحة Railway ثم `railway config plan/apply`. **ممنوع إرسال أي بيانات حقيقية عبر Railway.**
4. gitleaks يمنع دمج أي مفتاح بالخطأ، و`railway_checks.py` يرفض المفتاح كقيمة حرفية في IaC (اختبار N19).

## 5. التشغيل والترقية والتراجع

[runbook.md](runbook.md): النسخ والاستعادة لكل بيئة، الترقية، التراجع، السجلات، الحوادث.
