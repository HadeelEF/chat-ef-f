# ADR-0016 — لوحة الإدارة: خدمة LibreChat Admin Panel الرسمية، وبناء أمني مؤقت لصورة Railway

| Field | Value |
|---|---|
| Status | **Accepted** — قرارات المالك 2026-10-23 في جلسة Claude Code Cloud ([#141](https://github.com/faenazi/ef-ai-workspace/issues/141)، القرارات 1–4)؛ **القرار 5 (الهوية) مُضاف 2026-10-24** بقرار المالك 2026-10-23 ([#160](https://github.com/faenazi/ef-ai-workspace/issues/160)) |
| Date | 2026-10-23 |
| Deciders | مالك المشروع (@faenazi)؛ اختيار الـ commit والحزم هندسي (الوكيل) |
| Related | FR-014، FR-001 AC-2؛ NFR-SEC-02؛ SC-06، SC-12، SC-18؛ ADR-0006، ADR-0008، ADR-0009، ADR-0010، ADR-0012 |

## Context

- المالك يريد موقع إدارة يفتحه من الجوال. LibreChat v0.8.8 لا يحمل واجهة إدارة داخلية. upstream يقدّم
  [LibreChat Admin Panel](https://www.librechat.ai/docs/features/admin_panel) بحالة **Preview**: حاوية منفصلة (Bun + Vite، منفذ 3000) تستدعي
  `/api/admin/*` في LibreChat ≥ v0.8.5، وLibreChat يتحقق في كل طلب من `role: ADMIN` أو منحة `access:admin`.
- ما تفعله اللوحة على v0.8.8 (من المصدر، 2026-10-23):
  - مجموعات وأدوار مخصصة وأعضاؤها، ومنح إدارية، وسجل تدقيق.
  - تجاوزات إعدادات لكل دور أو مجموعة في مجموعة `configs` في MongoDB.
  - صفحة المستخدمين معطّلة upstream، والبحث عن المستخدمين متاح فقط عند إضافة أعضاء. إنشاء الحسابات وحذفها غير موجود.
  - صلاحيات `USER`/`ADMIN` تُعاد من `librechat.yaml` عند كل إقلاع (`packages/api/src/app/permissions.ts:132`). إسناد دور مخصص يستبدل
    دور الحساب (دور واحد لكل حساب)، وحقول صلاحيات `interface` تُحذف من تجاوزات الإعدادات (تُدار بالأدوار). الأقسام الأخرى
    (`endpoints`، و`mcpServers` البعيدة، و`modelSpecs`…) قابلة للتجاوز.
  - السجل يسجّل منح الصلاحيات وسحبها فقط.
  - الواجهة إنجليزية فقط.
- الصورة: ملفات Compose في upstream v0.8.8 تستخدم `:latest`. التوثيق يشير إلى `ghcr.io/clickhouse/...`، وهي متوقفة منذ 2026-08-14.
  الصورة الحية منذ upstream #156 (2026-10-14) هي `ghcr.io/librechat-ai/librechat-admin-panel`. الوسم الإصداري الوحيد `1.0.0` أقدم من مخطط v0.8.8.
- **SC-18 (Trivy 0.76.0، 2026-10-23):** صورة `82fb4b6` (وكذلك `24c0670`، الأحدث) تحمل ثلاث CRITICAL و~47 HIGH:
  - **CVE-2026-102989** في `@tanstack/react-start` 1.167.30: XSS انعكاسي دون مصادقة في استجابات server functions. قابلة للوصول على رابط عام،
    ومحزومة داخل `dist/server`، ولا إصلاح upstream بعد.
  - **CVE-2026-9277** و**CVE-2026-102422** في `shell-quote`: أداة تطوير تعتمدها `launch-editor` فقط.
  - **CVE-2026-31789** في OpenSSL 3.5.5: منصات 32-bit فقط.

## Decision

1. **خدمة رابعة `admin-panel` في كل بيئة**، بلا بيانات ولا volume (الجلسة كوكي مشفّر بـ `SESSION_SECRET`):
   - **Compose:** الصورة الرسمية `82fb4b6` بالـ digest على شبكة `frontend` فقط (لا تصل MongoDB)، مع `read_only` و`cap_drop: ALL`.
     محلياً على `127.0.0.1:3000`. في الموقع عبر Caddy باسم داخلي ثانٍ `EFAIW_ADMIN_HOSTNAME`، بالشهادة نفسها (SAN).
   - **Railway `dev`:** صورة مشتقة (البند 3)، وحد 1 vCPU / 512 MB، و`SESSION_SECRET` بـ `preserve()`، ورابط `*.up.railway.app` يُولَّد يدوياً بعد
     SC-18 (تفويض المالك للتعريض العام، ADR-0009).
   - **الاتصال:** خادم اللوحة يصل LibreChat عبر الشبكة الخاصة (`librechat:3080` / `librechat.railway.internal:3080`). LibreChat يأخذ
     `ADMIN_PANEL_URL` لرابط «لوحة المسؤول» في الإعدادات، ولأصل موثوق في دخول المسؤول.
2. **سياسة الإعدادات (قرار المالك 2):** اللوحة للمجموعات والأدوار المخصصة والمنح فقط. الإعدادات تتغير عبر PR على `librechat.yaml`.
   `scripts/operations/admin-config-drift.sh` يفشل إن وُجدت وثيقة في `configs`، أو دور مخصص يسمح بما لا يسمح به دور `USER` المأخوذ من الملف.
3. **بناء أمني مؤقت لصورة Railway (قرار المالك 4، نمط ADR-0012):** `infrastructure/railway/admin-panel.Dockerfile`:
   - يبني اللوحة من **الـ commit نفسه** بعد تطبيق `patches/0001-security-dependency-bumps.patch`، الذي يغيّر `package.json` و`bun.lock` فقط:
     - `@tanstack/react-start` 1.168.61 (`start-server-core` 1.169.40)، و`react-router` 1.170.42، و`router-core` 1.171.35؛
     - `query` 5.104.5، و`seroval` 1.6.12، و`shell-quote` 1.11.0، و`zod` 4.6.7 (#165).
   - `patches/0003-import-yaml-requires-session.patch` (#165): استيراد YAML هو الدالة الوحيدة التي لا تستدعي LibreChat، فلم تفحص
     الجلسة، ومدخلها يصل إلى zod 3 داخل `librechat-data-provider` (CVE-2023-54404، بلا إصلاح 3.x). يشترط الآن جلسة مسؤول، ويبقى حتى يفحصها upstream.
   - يستبدل `dist/` و`node_modules/` و`src/server/` في الصورة الرسمية (الـ `FROM` النهائي = digest Compose)، ثم `apk upgrade` لـ OpenSSL وmusl وzlib.
   - يعمل بمستخدم `bun`، خلف حارس بدء يرفض غياب المتغيرات أو `SESSION_SECRET` أقصر من 32.
   - **حارس الخروج:** يفشل البناء إن لم تحمل الصورة الأساسية `react-start` 1.167.30. عند صورة upstream مُصلحة تُحذف الطبقة كلها
     ويُثبّت الـ digest الجديد، وتعود الخدمة إلى الصورة الرسمية كما هي. `1.169.x` مستبعد لأنه أزال `useSession` الذي يستخدمه الكود.
4. **اللغة (قرار المالك 3):** الواجهة الرسمية بالإنجليزية. الترجمة العربية مساهمة upstream لاحقة، بلا fork.
5. **الهوية (قرار المالك 2026-10-23، #160):** خط الصندوق وألوانه وشعاره على لوحة Railway، والواجهة تبقى بالإنجليزية (البند 4).
   - `patches/0002-ef-brand.patch` على المصدر نفسه، وملفات الهوية السبعة من `infrastructure/common/client/brand/` تُنسخ دون تعديل إلى
     `public/ef`، وwatch paths تشملها (ADR-0010).
   - الخط Aktiv Grotesk (400، 600، 700)، ومعه الاسم «Inter» الذي تكتبه Click UI 0.9.1 في متغيرات الخط، فلا تُنسخ تلك المتغيرات.
   - الألوان: متغيرات Click UI واللوحة في السمتين الفاتحة والداكنة، مولّدة من Click UI 0.9.1 بقواعد مكتوبة في `src/ef-brand.css`؛
     ألوان الرسوم والتحذير تبقى.
   - Compose يبقى بالصورة الرسمية كما هي، كواجهة Compose (ADR-0013، #17).
   - **الخروج:** حين تُزال الطبقة الأمنية (البند 3) يبقى البناء من المصدر للهوية وحدها (`0002`)، كتعديلات الواجهة في ADR-0013. ترقية
     Click UI تتطلب توليد الألوان من جديد.

## Rationale

- FR-014 (فصل المسؤول وإدارة الأدوار) يحتاج واجهة يفتحها المالك من الجوال. اللوحة الرسمية هي المسار المدعوم upstream، وهي عميل رقيق
  لا يمنح نفسه صلاحيات.
- SC-18 يمنع التعريض العام مع CRITICAL قابلة للوصول. رفع نسخ الحزم وحده يُسقطها كلها (0 CRITICAL في الصورة المشتقة)، ويُبقي كود
  اللوحة كما في upstream، ويُزال بخطوة واحدة.
- Git يبقى مصدر الحقيقة للإعدادات (ADR-0002). فحص الانحراف يجعل أي إعداد مخزّن في القاعدة ظاهراً ويمكن إزالته.

## Alternatives considered

- **الصورة الرسمية كما هي على Railway:** مرفوض. CRITICAL قابلة للوصول دون قبول مخاطر.
- **انتظار إصلاح upstream دون رابط عام:** يمنع استخدام المالك من الجوال، وموعد الإصلاح غير معروف.
- **قبول مخاطر مؤقت لكل ثغرة:** مرفوض. الـ XSS على مساحة المسؤول نفسها.
- **fork أو ترقية TanStack إلى 1.169.x:** تغيير كود upstream (ADR-0006 المستوى 5) وصيانة أكبر.
- **بناء الصورة نفسها لـ Compose:** `compose_checks.py` يشترط صوراً مثبتة لا `build:`. Compose داخلي فقط، كسابقة صورة LibreChat (ADR-0012).

## Consequences

- خدمة رابعة على Railway بحد 512 MB (قياس الجلسة ~0.1 GB)، ضمن تفويض المالك، وwatch paths تعيد نشرها عند تغيّر صورتها فقط (ADR-0010).
- صورة Compose تحمل CVE-2026-102989: لا تُعرَّض خارج loopback أو الشبكة الداخلية قبل صورة upstream مُصلحة أو قرار SC-18.
- الطبقة المؤقتة تحتاج صيانة: كل تحديث لـ commit اللوحة يتطلب توليد الـ patch من جديد، وTrivy، والاختبارات.
- كل محاولات الدخول عبر اللوحة تشترك في حد LibreChat (7 / 5 دقائق)، لأن الخادم يستدعي LibreChat دون `X-Forwarded-For`.
- السجل لا يغطي الأدوار والمجموعات والإعدادات، فتبقى فجوة SC-12. فحص الانحراف يعوّض جزئياً للإعدادات.
- SSO للوحة يأتي مع Entra (M6، #57)، ومعه `ADMIN_SSO_ONLY=true`.

## Verification

- `compose_checks.py` و`railway_checks.py`: الخدمة معزولة ومثبتة، والمتغيرات مراجع فقط، وحارس الخروج موجود. `negative-checks.sh` N26–N33.
- `compose-stack.sh` T42–T49 وO07، و`railway-emulation.sh` R40–R46، و`mock_chat.py` M76–M82.
- Trivy على الصورة الرسمية والمشتقة، وPlaywright على تدفقات اللوحة.
- النتائج في [#141](https://github.com/faenazi/ef-ai-workspace/issues/141) و[سجل الثغرات](../../security/vulnerability-register.md)، والحالة الحية في
  [CURRENT_STATE](../../../project/CURRENT_STATE.md).
