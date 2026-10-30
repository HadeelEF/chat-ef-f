# ADR-0008 — استضافة متعددة البيئات: Railway وWindows المحلي وUbuntu في الموقع

| Field | Value |
|---|---|
| Status | **Accepted** — D1 **معتمد** من مالك المشروع في [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) (2026-10-18، سجل القرار الرسمي). اعتماد معماري فقط: **ليس** اعتماداً لـ Railway لأحمال سرية أو لإقامة البيانات، ولا تفويضاً بدمج أو نشر أو تعريض عام |
| Date | 2026-10-18 |
| Deciders | مالك المشروع (@faenazi)؛ مراجع المعمارية |
| Supersedes | [ADR-0004](0004-coolify-and-docker-compose-deployment.md) (Coolify) |
| Related | ADR-0005، ADR-0006، ADR-0007، NFR-PORT-01/02، NFR-SEC-02/03/04، NFR-PRIV-01، [#15](https://github.com/faenazi/ef-ai-workspace/issues/15)، [#17](https://github.com/faenazi/ef-ai-workspace/issues/17)، #6/#13 (مُستبدلان) |

> **تعديل 2026-10-20:** مساعد PowerShell (`scripts/windows/efaiw.ps1`) المذكور في القرار 5 واختباره أُزيلا بقرار المالك
> ([#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ مسار Windows الوحيد المدعوم هو Ubuntu WSL2 + Docker Engine (D4).
> باقي القرار دون تغيير.

## Context

M1 (PR #12، `0db80d9`) سلّم حزمة LibreChat v0.8.8 + MongoDB 8.0.34 مُختبرة على Docker Compose ومُوجّهة لـ Coolify على VPS.
لم يُنشر Coolify قط (#6 و#13 بقيا Blocked). قرر المالك استبدال Coolify بثلاث بيئات:

| البيئة | الغرض | المنصّة |
|---|---|---|
| A — Railway | تطوير/اختبار/عرض سحابي (ليست إنتاجاً) | Railway Pro، نشر من GitHub، IaC |
| B — Windows 11 | محطة المطوّر | Docker Desktop أو Docker Engine داخل WSL2، Compose v2 |
| C — Ubuntu Server LTS | استضافة داخلية مستقبلية | Docker Engine + Compose plugin، وكيل HTTPS داخلي |

حقائق Railway متحقق منها من المصدر الرسمي (مستودع `railwayapp/docs` commit `7235449` بتاريخ 2026-10-17، حزمة `railway@3.16.0`،
`railwayapp/cli` v5.70.0 — موقع docs.railway.com محجوب من بيئة السحابة فقُرئ مصدره):

| الحقيقة | الأثر |
|---|---|
| Config as Code (`railway.json`/`railway.toml`) **deprecated**؛ لا يُقرأ بعد 2026-12-01؛ البديل `.railway/railway.ts` (GA) | نستخدم IaC فقط؛ الفحص يمنع ملفات Config as Code |
| `railway config plan` يتطلب مصادقة (token)؛ لا تحقق offline في الـ CLI | التحقق الثابت عبر تقييم الملف بنفس طريقة الـ CLI بالـ SDK المثبت |
| volume **واحد** لكل خدمة؛ لا replicas مع volume؛ يُركّب مملوكاً لـ root | تصميم تخزين بمسار واحد؛ مُحوّل بدء يجهّز الـ volume ثم يُسقط الصلاحيات |
| لا bind mounts للملفات | صورتان مشتقتان صغيرتان تضمّنان `librechat.yaml` و`mongo-init/` |
| الشبكة الخاصة `<service>.railway.internal`؛ بيئات ما بعد 2025-10-16 IPv4+IPv6، الأقدم IPv6 فقط | MongoDB يستمع على `::` و`0.0.0.0` (كقالب Railway الرسمي) |
| healthcheck عند النشر فقط (افتراضي 300 ث)، لا مراقبة مستمرة | `/health` للنشر؛ المراقبة المستمرة تبقى M6 |
| نسخ volumes احتياطية يدوية/مجدولة (يومي/أسبوعي/شهري) والاستعادة كـ volume جديد | المسار الأساسي للنسخ على Railway |
| **لا منطقة في الشرق الأوسط** (us-west2، us-east4، europe-west4، asia-southeast1) | بيانات اصطناعية فقط؛ ليس مرشحاً للإنتاج (OD-05) |

## Decision

1. **منصّة واحدة قابلة للنقل:** نفس الصور الرسمية بنفس الـ digest (ADR-0007) ونفس الإعداد المشترك في البيئات الثلاث:
   - `infrastructure/common/`: `librechat.yaml`، `librechat.env` (سياسة التطبيق غير السرية: التسجيل معطّل، `SEARCH=false`…)، `mongo-init/`.
   - `infrastructure/compose/`: `compose.yaml` أساسي + `compose.local.yaml` (Windows/محلي: `127.0.0.1:3080`) + `compose.onprem.yaml`
     (Ubuntu: وكيل Caddy مثبت بالـ digest، HTTPS بشهادة CA مؤسسية أو `internal` أو ACME).
   - `infrastructure/railway/` + `.railway/railway.ts`: خدمتان تُبنيان من المستودع بـ Dockerfile مشتق `FROM` نفس الـ digest.
2. **Railway:** MongoDB خاص (لا TCP proxy ولا نطاق)، مستخدم تطبيق `readWrite`، LibreChat عبر نطاق `*.up.railway.app` المُولّد
   فقط (HTTPS من Railway)، `/health`، نسخة واحدة، حدود موارد، ~~نشر يدوي فقط~~ — **حلّ محله [ADR-0010](0010-railway-dev-autodeploy-from-main.md) (2026-10-19): نشر تلقائي من `main`**
   بـ watch paths ودون Wait for CI؛ `scripts/setup/railway-deploy.sh` (`railway up`) للطوارئ. الأسرار `preserve()` في IaC وتُضبط
   مرة واحدة بـ `scripts/setup/railway-secrets.sh` (stdin، لا تُكتب فوق قيم موجودة). **لا تطبيق تلقائي**: `plan`/`apply` بتفويض المالك.
3. **التخزين على Railway:** volume واحد لـ LibreChat على `/app/storage` مع روابط رمزية (مُنشأة وقت البناء) من `/app/uploads` و
   `/app/client/public/images` و`/app/data`؛ `/app/logs` عابر (Railway يجمع stdout). MongoDB على volume منفصل `/data/db`
   — **لا خلط** بين بيانات التطبيق وقاعدة البيانات.
4. **Coolify لم يعد هدف نشر مدعوماً.** `infrastructure/coolify/` أُزيل بنقل الملفات (التاريخ محفوظ في Git)؛ ADR-0004 → Superseded؛
   #6 و#13 أُغلقا مع الإحالة إلى #15.
5. Windows: Compose فقط (لا تثبيت MongoDB/LibreChat أصلياً)، مساعد PowerShell `scripts/windows/efaiw.ps1`. Ubuntu: لا اعتماد على
   Railway CLI أو حسابه.

## Rationale

- يحقق ADR-0005 (حاويات قابلة للنقل) دون fork: الصور المشتقة لا تغيّر كود LibreChat (ADR-0006 — المستوى 3 «build from unmodified source/image»)
  وتُفرض مساواة الـ digest آلياً.
- مسار واحد للإعداد يمنع انحراف ثلاث نسخ: `librechat.env` يُقرأ مباشرة في Compose، ويُقارن آلياً مع `railway.ts`.
- Railway Pro يوفّر بيئة عرض بلا إدارة خوادم؛ Compose يبقى المرجع المحمول لـ Windows وUbuntu وأي مزوّد مستقبلي معتمد.

## Alternatives considered

| البديل | سبب عدم الاختيار |
|---|---|
| الإبقاء على Coolify/VPS | قرار المالك؛ لم يُوفّر VPS (#6) |
| قالب MongoDB المُدار في Railway (`mongo()` في SDK) | صورة `mongo:8` غير مثبتة، بيانات root للتطبيق، متغيرات/أمر بدء غير مؤكدة عبر IaC؛ لا مستخدم أقل امتياز |
| `CONFIG_PATH` عبر URL بدل صورة مشتقة | المستودع خاص (يتطلب token في URL)؛ تبعية شبكية عند البدء |
| تشغيل LibreChat كـ root (`RAILWAY_RUN_UID=0`) | يزيد الأثر عند الاختراق؛ المحوّل يُسقط الصلاحيات إلى `node` (مُختبر R12) |
| Railway Config as Code | deprecated (قطع نهائي 2026-12-01) |
| تخزين S3/Buckets بدل volume | تغيير معماري لاستراتيجية الملفات؛ خارج النطاق |
| Kubernetes للموقع | غير مبرر الآن؛ لا ادعاء HA |

## Consequences

- صورتان مشتقتان تُبنيان على Railway؛ أي ترقية digest تُحدّث `compose.yaml` و`infrastructure/railway/*.Dockerfile` معاً (`railway_checks.py`).
- إعادة نشر خدمة ذات volume على Railway تسبب توقفاً قصيراً (موثق upstream)؛ مقبول للعرض.
- Railway خارج المملكة: **لا بيانات حقيقية مطلقاً** (NFR-PRIV-01)؛ ليس بيئة إنتاج ولا مرشحاً لـ OD-05.
- Windows (D4 معتمد): **المسار المفضّل Ubuntu WSL2 + Docker Engine/Compose**؛ Docker Desktop بديل فقط بترخيص مُتحقق منه (يتطلب اشتراكاً مدفوعاً للجهات الحكومية).
- Railway (D3 معتمد كإعداد مستهدف، غير مُطبّق): EU West، نسخة واحدة، 2 vCPU/2 GB وMongoDB 1 vCPU/1 GB، 5 GB لكل volume، حد إنفاق $30 وتنبيه $15 (يتحقق المالك من ضبطه)، نشر يدوي فقط بتفويض لـ commit مراجَع على `main` (لا اعتماد على GitHub Actions)؛ **لا نطاق عام** قبل تصفية SC-18 وتفويض #15 (D5).
- GitHub Actions غير مستخدم (D2 المعدّل في #16): لا شيء ينتظر CI؛ بوابة الجودة اليدوية في جلسة السحابة ([DoD](../../quality/definition-of-done.md)) + مراجعة مستقلة + قرار المالك.
  حالة autodeploy الحية في لوحة Railway لا يعبّر عنها IaC: يتحقق المالك من عدم ربط أي مستودع قبل أول نشر.
- سجلات LibreChat الملفية على Railway عابرة؛ التجميع المركزي M6.
- أدوات جديدة: Railway SDK/TypeScript (npm، lockfile)، Caddy (on-prem)، Trivy (فحص صور report-only).

## Verification

`Tested (cloud session)` 2026-10-18: `compose_checks.py`، `railway_checks.py` (تقييم offline + `tsc`)، `tests/smoke/compose-stack.sh local` (37)
و`onprem` (43)، `tests/smoke/railway-emulation.sh` (23 + 2 NOT RUN: IPv6)، `tests/smoke/windows-helper.sh` (10، PowerShell 7 على Linux).
النشر الفعلي على Railway، وتشغيل Windows 11 وخادم Ubuntu حقيقيين: **NOT RUN** — [#15](https://github.com/faenazi/ef-ai-workspace/issues/15)،
[#17](https://github.com/faenazi/ef-ai-workspace/issues/17). التفاصيل: [تقرير M1.1](../../history/reports/M1.1-hosting-transformation-report.md).
