# مصفوفة تطبيق الهوية (Brand Implementation Matrix)

| الحقل | القيمة |
|---|---|
| الحالة | **Analysis** — جرد وتصنيف؛ **مطبّق منه:** إخفاء علامة upstream بإعداد L1 (#43 الجزء A: S-04 رابط المساعدة، S-05c التذييل، S-07 «حول»، §11) وتقييد الأدوات (#39). الهوية الرسمية مطبّقة في واجهة Railway بعد التدقيق ([#92](https://github.com/faenazi/ef-ai-workspace/issues/92)، [حوكمة الهوية](../brand-guidelines.md)) |
| Issue | [#42](https://github.com/faenazi/ef-ai-workspace/issues/42) (R0.3، Epic [#32](https://github.com/faenazi/ef-ai-workspace/issues/32)) |
| الاعتمادية | [#7](https://github.com/faenazi/ef-ai-workspace/issues/7) (D-04) أصول الهوية الرسمية — معتمدة من المالك 2026-10-20؛ قيم `TBD` هنا تعكس وقت التدقيق |
| إصدار upstream | LibreChat **v0.8.8** (`e8f3be0`)؛ الصورة `ghcr.io/librechat-ai/librechat:v0.8.8@sha256:5b706bce…` ([ADR-0007](../../architecture/adr/0007-pin-librechat-v0.8.8-and-mongodb-8.0.md)) |
| التاريخ | 2026-10-19 |
| مستوى الأدلة | مراجعة مصدر upstream + فحص ملفات الصورة المثبّتة محلياً (§2)؛ **خط أساس بصري جزئي** (12 لقطة، upstream كما هو، §8)؛ فحوص القبول §6 **NOT RUN** |
| المرجع | [ADR-0006](../../architecture/adr/0006-upstream-first-customization.md) · [design-system.md](../design-system.md) · [brand-guidelines.md](../brand-guidelines.md) · [ux-standards.md](../ux-standards.md) · FR-006/FR-015 ([FR](../../product/functional-requirements.md)) · NFR-MNT-01 ([NFR](../../product/non-functional-requirements.md)) |

> **ملاحظة:** هذا جرد 2026-10-19 قبل اعتماد الأصول. الهوية المعتمدة (#7، 2026-10-20) مطبّقة الآن في واجهة Railway وفي المخرجات:
> القيم وأين تُطبَّق في [حوكمة الهوية](../brand-guidelines.md)، والفجوات G-04 وG-05 وG-06 مغلقة هناك بتعديلات الواجهة
> ([ADR-0013](../../architecture/adr/0013-arabic-web-client-build.md)). واجهة Compose ما زالت upstream (#17).

## 1. الغرض والنطاق

جرد أسطح الواجهة في LibreChat v0.8.8 التي تحمل هوية أو نصاً أو اتجاهاً، وتصنيف آلية تخصيص كل سطح حسب ترتيب
[ADR-0006](../../architecture/adr/0006-upstream-first-customization.md)، مع خطر الترقية ومعايير القبول. ملخص الآليات يبقى في
[design-system.md §4](../design-system.md#4-آليات-التطبيق-في-librechat)؛ هذه الوثيقة هي التفصيل لكل شاشة، وتغذي
[#43](https://github.com/faenazi/ef-ai-workspace/issues/43) (تطبيق الهوية) و[#44](https://github.com/faenazi/ef-ai-workspace/issues/44) (الترجمة/RTL/الوصول).

## 2. منهجية التحقق والأدلة

| الدليل | ما تم | الحالة |
|---|---|---|
| مصدر upstream | استنساخ سطحي للوسم `v0.8.8` (`e8f3be08623663d4ad7f7241e693c94469b63bb0`) من [LibreChat](https://github.com/LibreChat-AI/LibreChat/tree/v0.8.8) في مساحة مؤقتة خارج المستودع؛ كل مسار `file:line` أدناه من هذا الوسم | Done |
| الصورة المثبّتة | `docker run --rm --entrypoint ls <image@digest> …` على الصورة المثبّتة محلياً: محتوى `/app/client/dist` و`dist/assets` و`manifest.webmanifest` و`sw.js` و`index.html` | Done |
| تغطية العربية | عدّ مفاتيح `client/src/locales/ar/translation.json` مقابل `en` (§5) | Done |
| لقطات الشاشة وخط الأساس البصري | 12 لقطة لـ v0.8.8 كما هو (دخول، ترحيب، محادثة × AR/EN × جوال/سطح مكتب، فاتح) على حزمة Compose محلية ونموذج #38 الوهمي؛ ليست رابط Railway (§8) | **Done (جزئي)** |
| فرع upstream `dev` | لم يُعَد التحقق من حالة `interface.theme` فيه؛ المرجع ما سجّله ADR-0006 (2026-10-17) | **NOT RUN** |

## 3. مفتاح طرق التنفيذ ودرجات الخطر

| الرمز | الطريقة (ADR-0006) | المعنى في هذا التدقيق |
|---|---|---|
| **L1** | إعداد مدعوم | متغيرات `.env` (`infrastructure/common/librechat.env` + `.railway/railway.ts`) أو `librechat.yaml`، أو بيانات عبر سكربت upstream |
| **L2** | أصول مُركّبة | ملف بنفس الاسم يُركّب read-only (Compose) أو يُنسخ بطبقة `COPY` في `infrastructure/railway/librechat.Dockerfile` (Railway بلا bind mounts — [ADR-0008](../../architecture/adr/0008-multi-environment-hosting-railway-windows-ubuntu.md)) دون تعديل كود |
| **L3** | بناء من المصدر غير المعدّل | صورة خاصة من وسم upstream مع متغيرات build-time مدعومة (`REACT_APP_THEME_*`)؛ digest يختلف عن الصورة الرسمية |
| **L4** | مساهمة upstream | Issue/PR أو ترجمة عبر Locize إلى LibreChat؛ تصل مع إصدار لاحق |
| **L5** | fork/patch | آخر خيار؛ يتطلب ADR مستقلاً بخطة صيانة وخروج — **لا يُقترح في هذا التدقيق** |

خطر الترقية: **Low** = مفتاح إعداد موثق في المخطط؛ **Medium** = يعتمد على اسم/مسار ملف داخلي أو حالة محفوظة؛
**High** = يعتمد على ناتج بناء مُولّد (hash/manifest) أو يتطلب خط بناء خاصاً.

## 4. مصفوفة تطبيق الهوية

المسارات نسبية لجذر upstream عند `v0.8.8`. «السلوك الحالي» = سلوك v0.8.8 مع إعدادنا الحالي
([`librechat.env`](../../../infrastructure/common/librechat.env)، [`librechat.yaml`](../../../infrastructure/common/librechat.yaml)).
لكل سطح: السلوك الحالي، التخصيص المطلوب (عام)، الطريقة، المصدر/موقع الإعداد، خطر الترقية، معايير القبول.

### S-01 — صفحة الدخول

- **السلوك الحالي:** شعار `assets/logo.svg` (LibreChat) ونصه البديل `com_ui_logo` + `appTitle`؛ العنوان نص مترجم ثابت
  `com_auth_welcome_back`؛ محدد المظهر فقط — **لا محدد لغة**؛ روابط الخصوصية/الشروط تظهر فقط إن ضُبطت؛ مكوّن `Banner`؛
  قبل الدخول يُرسل `/api/config` من `interface` الخصوصية والشروط و`buildInfo` فقط.
- **التخصيص المطلوب (عام):** شعار معتمد (TBD #7)؛ روابط سياسة الخصوصية والشروط (الروابط TBD — المالك)؛ إشعار
  «بيئة تجريبية — بيانات اصطناعية» موسوم `PROVISIONAL`؛ تسمية زر Entra ID في M6.
- **الطريقة:** الشعار L2 (S-02)؛ الروابط واللافتة وزر OpenID: L1؛ نص العنوان ومحدد اللغة: L4.
- **المصدر / موقع الإعداد:** `client/src/components/Auth/AuthLayout.tsx:64-96`، `Auth/Footer.tsx:9-42`،
  `api/server/routes/config.js:76,86-91,231-243`؛ `interface.privacyPolicy.externalUrl`، `interface.termsOfService.externalUrl`؛
  `OPENID_BUTTON_LABEL`، `OPENID_IMAGE_URL`؛ `npm run update-banner` (`config/update-banner.js`).
- **خطر الترقية:** Medium (الشعار)؛ Low (الإعداد).
- **معايير القبول:** لا شعار أو اسم LibreChat؛ النص البديل = `APP_TITLE`؛ الروابط تفتح العناوين المضبوطة؛ تخطيط صحيح
  AR/EN × جوال/سطح مكتب؛ كل عنصر مؤقت موسوم `PROVISIONAL`.

### S-02 — الشعار و favicon

- **السلوك الحالي:** ستة ملفات بأسماء ثابتة في `client/public/assets/` تُنسخ وقت البناء إلى `client/dist/assets/`: `logo.svg`،
  `favicon-16x16.png`، `favicon-32x32.png`، `apple-touch-icon-180x180.png`، `icon-192x192.png`، `maskable-icon.png` (512).
  الخادم يقدّم `client/dist` **قبل** `client/public/assets`، فاستبدال `public/assets` بلا أثر. في الصورة المثبّتة: الملفات
  موجودة **دون** نسخ `.gz/.br` (كان `express-static-gzip` سيفضّلها). الأيقونات (لا `logo.svg`) في precache لـ Service Worker
  بمراجعات وقت البناء؛ `Cache-Control: public, max-age=172800`.
- **التخصيص المطلوب (عام):** شعار رسمي (فاتح/داكن) وfavicon ومجموعة أيقونات PWA — TBD #7. `logo.svg` ملف واحد يُعرض
  على خلفيتي الوضعين الفاتح والداكن.
- **الطريقة:** **L2**: ملفات بنفس الأسماء والأبعاد على `/app/client/dist/assets/<name>`. لا L1 (لا مفتاح شعار/favicon
  في v0.8.8). المسار الدائم: L4 (شعار قابل للإعداد).
- **المصدر / موقع الإعداد:** `client/public/assets/*`، `client/vite.config.ts:92,475-494` (`copyPublicAssets`)،
  `api/config/paths.js:7-11`، `api/server/index.js:369-372`، `api/server/utils/staticCache.js:8,40-52`، `client/dist/sw.js` (precache).
- **خطر الترقية:** **Medium**: الأسماء والمواقع تفصيل بناء قد يتغير؛ precache يُبقي الأيقونات القديمة لدى المتصفحات المثبّتة
  حتى يتغير `sw.js` في إصدار لاحق.
- **معايير القبول:** الملفات الستة معتمدة؛ `GET /assets/<name>` = 200 بالـ checksum الجديد؛ favicon في التبويب وأيقونة
  الشاشة الرئيسية بعد مسح الكاش؛ قائمة `dist/assets` تُفحص عند كل ترقية (§7).

### S-03a — اسم التطبيق (تبويب المتصفح)

- **السلوك الحالي:** `APP_TITLE` = «بصير | صندوق البيئة» (`PROVISIONAL`، Configured) يغيّر عنوان التبويب بعد تحميل الواجهة؛
  استثناءات ثابتة: «… | LibreChat» في Insights وMarketplace. التفاصيل في
  [design-system.md §4](../design-system.md#4-آليات-التطبيق-في-librechat).
- **التخصيص المطلوب (عام):** الاسم الرسمي TBD (#7)؛ لا ظهور لـ LibreChat.
- **الطريقة:** L1؛ الاستثناءان: L4.
- **المصدر / موقع الإعداد:** `api/server/routes/config.js:76`، `client/src/hooks/Config/useAppStartup.ts:45-50`،
  `client/src/utils/documentTitle.ts:4`، `Insights/InsightsView.tsx:627`، `Agents/Marketplace.tsx:50`.
- **خطر الترقية:** Low.
- **معايير القبول:** العنوان = `APP_TITLE` في كل الشاشات عدا الاستثناءين الموثقين حتى دمج L4.

### S-03b — PWA (manifest، لون السمة، الأيقونات)

- **السلوك الحالي:** `client/dist/manifest.webmanifest` مُولّد وقت البناء: `name`/`short_name` = `LibreChat`، `theme_color`
  `#009688`، `background_color` `#000000`، `lang` `en`، بلا `dir`؛ يُقدَّم `no-store` لكنه في precache لـ SW. لا متغير بيئة
  ولا مفتاح إعداد.
- **التخصيص المطلوب (عام):** اسم PWA وألوانه وأيقوناته المعتمدة — TBD #7.
- **الطريقة:** L2 ممكن (استبدال الملف) لكنه **High**؛ L3 لا يكفي (القيم مكتوبة في `vite.config.ts`)؛ المفضّل L4: manifest
  يُولّده الخادم من `APP_TITLE`.
- **المصدر / موقع الإعداد:** `client/vite.config.ts:93-188`، `api/server/utils/staticCache.js:40-49`.
- **خطر الترقية:** **High**: ملف مُولّد قد يتغير شكله وأيقوناته مع كل إصدار؛ المتصفحات المثبّتة تحتفظ بالنسخة المخزّنة.
- **معايير القبول:** «إضافة للشاشة الرئيسية» (Android/iOS) تُظهر الاسم والأيقونة المعتمدين؛ مقارنة manifest الجديد عند كل ترقية.

### S-03c — رأس HTML الثابت

- **السلوك الحالي:** `client/index.html`: `<title>LibreChat</title>`، وصف «LibreChat - An open source chat application…»،
  `theme-color` `#171717`، روابط favicon. الخادم يقرأ `dist/index.html` مرة عند الإقلاع ويستبدل `lang` فقط (مع base href
  وfooter bootstrap وCSP nonce). يظهر في أول رسم وفي معاينات الروابط (لا تشغّل JS).
- **التخصيص المطلوب (عام):** لا ظهور لـ LibreChat في معاينة الرابط أو العنوان الأولي.
- **الطريقة:** لا L1. L2 (تركيب `index.html`) **مرفوض**: يحوي أسماء حزم مُجزّأة (`index.<hash>.js`) تتغير كل إصدار ⇐ واجهة
  فارغة. المسار: L4 (استبدال `<title>`/الوصف على الخادم كما يُستبدل `lang`).
- **المصدر / موقع الإعداد:** `client/index.html:6,11-17`، `api/server/index.js:279-325`.
- **خطر الترقية:** High (L2).
- **معايير القبول:** بعد L4: العنوان الأولي ومعاينة الرابط بلا LibreChat؛ قبله: قيد موثق مقبول من المالك.

### S-04 — الشريط الجانبي والتنقل

- **السلوك الحالي:** لا شعار ولا اسم تطبيق في الشريط. العناصر (الوكلاء، Prompts، الذاكرة، الإشارات، المعاملات، MCP، Skills،
  الجدولة) تظهر حسب صلاحيات الدور المُهيّأة من `interface.*` عند الإقلاع. قائمة الحساب: «Help & FAQ» → `HELP_AND_FAQ_URL`
  وافتراضيه **`https://librechat.ai`** (غير مضبوط حالياً)؛ يُخفى بالقيمة `/`.
- **التخصيص المطلوب (عام):** إخفاء ما خارج نطاق الإصدار؛ رابط المساعدة إلى صفحة داخلية معتمدة أو مخفي.
- **الطريقة:** L1.
- **المصدر / موقع الإعداد:** `client/src/hooks/Nav/useUnifiedSidebarLinks.ts`، `hooks/Nav/useSideNavLinks.ts`،
  `components/Nav/AccountSettings.tsx:35`، `api/server/routes/config.js:148`، `packages/api/src/app/permissions.ts`؛ مفاتيح
  `interface.agents`، `prompts`، `bookmarks`، `memories`، `parameters`، `mcpServers`، `skills`، `schedules`، `marketplace`.
- **خطر الترقية:** Low؛ تنبيه: الصلاحيات تُحفظ في MongoDB وحذف المفتاح لا يعيدها (§7.3).
- **معايير القبول:** العناصر المعتمدة فقط ظاهرة؛ لا رابط إلى librechat.ai؛ الشريط على اليمين في RTL.

### S-05a — المحادثة: شاشة الترحيب

- **السلوك الحالي:** تحية زمنية مترجمة، أو `interface.customWelcome` (نص **واحد** غير مترجم، يدعم `{{user.name}}`)؛ أو
  `label`/`description` لـ `modelSpecs` مع `showOnLanding` و`conversation_starters`.
- **التخصيص المطلوب (عام):** ترحيب معتمد بالعربية والإنجليزية (النص TBD).
- **الطريقة:** L1؛ ترحيب ثنائي اللغة يتطلب L4 (نمط `LocalizedString` الموجود في `mcpServers.trustCheckbox` و`useLocalizedConfig.ts`).
- **المصدر / موقع الإعداد:** `client/src/components/Chat/Landing.tsx:80-135`، `packages/data-provider/src/config.ts:2119,2265`.
- **خطر الترقية:** Low.
- **معايير القبول:** النص يظهر صحيحاً في الاتجاهين؛ لا نص بلغة واحدة يظهر في الواجهة الأخرى دون قرار.

### S-05b — المحادثة: الرسائل والمُدخل

- **السلوك الحالي:** حاوية الرسالة `dir="auto"` (اتجاه لكل رسالة)؛ اتجاه المُدخل من إعداد المتصفح `chatDirection` وافتراضيه
  **`LTR`** بغض النظر عن لغة الواجهة؛ `ChatForm` يطبّق `flex-row-reverse` عند RTL؛ الألوان من رموز السمة.
- **التخصيص المطلوب (عام):** المُدخل RTL افتراضياً في العربية؛ ألوان الهوية (TBD #7).
- **الطريقة:** الاتجاه الافتراضي: L4؛ الألوان: S-14.
- **المصدر / موقع الإعداد:** `client/src/components/Chat/Messages/Content/Container.tsx:9`، `client/src/store/settings.ts:79`،
  `components/Chat/Input/ChatForm.tsx:214-216,685,700`، `Nav/SettingsTabs/Chat/ChatDirection.tsx`.
- **خطر الترقية:** Medium.
- **معايير القبول:** FR-006 AC-3: عربي RTL، إنجليزي LTR، الكود LTR معزول؛ لا انعكاس مزدوج حين `dir=rtl` و`chatDirection=RTL`
  معاً (لم يُتحقق).

### S-05c — المحادثة: التذييل

- **السلوك الحالي:** تذييل شاشة الترحيب والدخول الافتراضي: `[LibreChat v0.8.8](https://librechat.ai) - Every AI for Everyone.`
  (`com_ui_latest_footer`) — **مخفي منذ #43 الجزء A** (`CUSTOM_FOOTER=` فارغ، §11). `CUSTOM_FOOTER` (Markdown، يُقسَّم بـ `|`،
  القيمة `""` تخفيه) نص واحد غير مترجم.
- **التخصيص المطلوب (عام):** تذييل معتمد أو مخفي (TBD)؛ لا رابط upstream.
- **الطريقة:** L1.
- **المصدر / موقع الإعداد:** `client/src/components/Chat/Footer.tsx:55-90`، `api/server/routes/config.js:128-129`،
  `api/server/index.js:300-303`.
- **خطر الترقية:** Low.
- **معايير القبول:** لا رابط/إصدار LibreChat في AR/EN.

### S-06 — اختيار النموذج

- **السلوك الحالي:** `ModelSelector` يظهر إن `interface.modelSelect` (افتراضي true) أو وُجدت `modelSpecs`؛ `modelSpecs.list[]`:
  `label`، `description`، `iconURL`، `group`، `groupIcon`، `showIconInMenu/Header`، `default`، `order`؛ `enforce`/`prioritize`؛
  `endpoints.custom[].modelDisplayLabel`/`iconURL`. التسميات نصوص غير مترجمة. لا endpoint حالياً (OD-01
  [#5](https://github.com/faenazi/ef-ai-workspace/issues/5)).
- **التخصيص المطلوب (عام):** أسماء عرض معتمدة بدل معرّفات النماذج؛ أيقونات ضمن الهوية.
- **الطريقة:** L1؛ الأيقونات قد تشير لأصل L2؛ تسميات ثنائية اللغة: L4.
- **المصدر / موقع الإعداد:** `client/src/components/Chat/Menus/Endpoints/ModelSelector.tsx:137`،
  `packages/data-provider/src/models.ts:179-216`، `config.ts:1752-1753`.
- **خطر الترقية:** Low (مرتبط بـ `version: 1.3.17`).
- **معايير القبول:** المستخدم يرى أسماء العرض المعتمدة فقط؛ مرهون بـ #5 (أو المحاكاة #38).

### S-07 — الإعدادات

- **السلوك الحالي:** نافذة تبويبات: المظهر (system/dark/light/high-contrast)، اللغة (`ar-EG` → `ar`)، اتجاه المحادثة، حجم الخط؛
  تبويب «حول» يعرض `LibreChat version` والـ commit — يُخفى بـ `interface.buildInfo: false`. تفضيل اللغة يُحفظ في cookie `lang`
  وlocalStorage (لكل متصفح لا لكل حساب).
- **التخصيص المطلوب (عام):** قرار إظهار «حول»؛ نصوص عربية كاملة.
- **الطريقة:** L1 (`buildInfo`)؛ النصوص L4.
- **المصدر / موقع الإعداد:** `client/src/components/Nav/Settings/registry.tsx`، `Nav/Settings/context.tsx:36`،
  `Nav/SettingsTabs/About/About.tsx:30`، `Nav/Settings/controls.tsx:34-48`، `Appearance/Selectors.tsx`.
- **خطر الترقية:** Low.
- **معايير القبول:** تبويب «حول» حسب القرار؛ تبديل اللغة يعمل ويبقى بعد إعادة التحميل.

### S-08 — النوافذ والحوارات

- **السلوك الحالي:** مكونات `@librechat/client` (Radix/Ariakit/Headless UI) بألوان رموز السمة؛ نافذة شروط اختيارية
  `interface.termsOfService.modalAcceptance/modalTitle/modalContent` (نص واحد؛ القبول يُحفظ لكل مستخدم)؛ لافتات `/api/banner`
  (بيانات عبر `update-banner`/`delete-banner`).
- **التخصيص المطلوب (عام):** نصوص شروط معتمدة إن طُلبت (TBD)؛ لافتة بيئة تجريبية `PROVISIONAL`.
- **الطريقة:** L1؛ النمط: S-14.
- **المصدر / موقع الإعداد:** `client/src/components/ui/TermsAndConditionsModal.tsx`، `client/src/routes/Root.tsx:119,211`،
  `packages/data-provider/src/config.ts:2108-2114`، `config/update-banner.js`، `config/reset-terms.js`.
- **خطر الترقية:** Low–Medium (حالة القبول محفوظة).
- **معايير القبول:** زر الإغلاق والأزرار منعكسة في RTL؛ حبس التركيز وEscape؛ نص عربي كامل.

### S-09 — الوكلاء (المنشئ/السوق)

- **السلوك الحالي:** المنشئ في اللوحة الجانبية حسب `interface.agents` {use, create, share, public}؛ السوق بـ `interface.marketplace.use`
  (افتراضي false) وعنوانه ثابت «… | LibreChat»؛ الفئات تُزرع في MongoDB بمفاتيح ترجمة؛ صور الوكلاء في `/images` (حجم بيانات
  المستخدم). العربية `com_agents_*` 17.3%.
- **التخصيص المطلوب (عام):** إظهار/إخفاء حسب نطاق M5 (FR-010)؛ لا ظهور لـ LibreChat.
- **الطريقة:** L1 للإظهار؛ العنوان والنصوص L4.
- **المصدر / موقع الإعداد:** `client/src/components/SidePanel/Agents/`، `SidePanel/Builder/`، `Agents/Marketplace.tsx:50`،
  `packages/data-schemas/src/methods/agentCategory.ts:179-197`.
- **خطر الترقية:** Medium.
- **معايير القبول:** حالة الإظهار في R0.3 مقررة صراحة؛ التدقيق الكامل مؤجل إلى M5.

### S-10 — العربية و RTL

- **السلوك الحالي:** 41 لغة؛ حزمة `ar` تُحمّل كسولاً (`assets/locale-ar.<hash>.js`)؛ المفاتيح الناقصة تعود إلى `en` ⇐ واجهة مختلطة؛
  **التغطية 22.6%** (§5)؛ `<html dir>` يُضبط بـ `i18n.dir()` بعد تحميل JS، والخادم يضبط `lang` فقط؛ اللغة الأولى: cookie `lang`
  ← localStorage ← `navigator.language` ← `en` — **لا افتراضي على مستوى الخادم**؛ لا محدد لغة في صفحة الدخول؛ CSS بأغلبه
  فيزيائي (`ml-/mr-/left-/right-/text-left`): ≈725 مقابل ≈10 منطقية، ولا قواعد `[dir=rtl]` في `style.css` (عدّ تقريبي بـ grep)؛
  الخط Inter لاتيني فقط ⇐ العربية بخط النظام.
- **التخصيص المطلوب (عام):** العربية افتراضية مع RTL صحيح (FR-006 AC-1)؛ مسرد مصطلحات (TBD)؛ خط عربي معتمد (TBD #7).
- **الطريقة:** الترجمة واللغة الافتراضية مطبّقتان في واجهة Railway بالمستوى L5 ([ADR-0013](../../architecture/adr/0013-arabic-web-client-build.md))، والمسار الدائم L4؛ محدد الدخول L4؛ الخط L4؛ الترجمات مُضمّنة في حزم JS مُجزّأة ⇐ استبدالها
  L2 مرفوض (High).
- **المصدر / موقع الإعداد:** `client/src/locales/i18n.ts:8-50,197-222,279-296`، `client/src/store/language.ts:23-27`،
  `api/server/index.js:312-314`، `client/src/style.css:259`، `client/public/fonts/`، `.github/workflows/locize-i18n-sync.yml`.
- **خطر الترقية:** **High** (فجوة).
- **معايير القبول:** FR-006 AC-1..AC-3؛ نسبة تغطية مستهدفة لشاشات P0 يحددها المالك (TBD)؛ نتائج #44.

### S-11 — الإنجليزية و LTR

- **السلوك الحالي:** `en` لغة المصدر (3059 مفتاحاً، 100%) والاحتياط؛ `dir="ltr"`. نصوص الإعداد (`customWelcome`، `CUSTOM_FOOTER`،
  الشروط، `modelSpecs`) لغة واحدة تظهر في الواجهتين.
- **التخصيص المطلوب (عام):** تكافؤ وظيفي كامل (FR-006 AC-2).
- **الطريقة:** لا تغيير؛ النصوص ثنائية اللغة L4.
- **المصدر / موقع الإعداد:** `client/src/locales/en/translation.json`، `i18n.ts:288-296`.
- **خطر الترقية:** Low.
- **معايير القبول:** التبديل AR ⇄ EN دون فقدان وظيفة؛ لا نص عربي غير مقصود في EN.

### S-12 — الاستجابة والجوال

- **السلوك الحالي:** `viewport` مع `interactive-widget=resizes-content`؛ `apple-mobile-web-app-capable` وشريط حالة
  `black-translucent`؛ درج جانبي للجوال بسحب يراعي RTL؛ نقاط كسر Tailwind الافتراضية.
- **التخصيص المطلوب (عام):** لا تخصيص؛ التحقق فقط (المالك يراجع من الهاتف).
- **الطريقة:** لا تغيير (اتباع upstream).
- **المصدر / موقع الإعداد:** `client/index.html:7-9,18-21`، `client/src/components/UnifiedSidebar/mobile/`،
  `client/src/hooks/Nav/useDrawerSwipe.ts:182`.
- **خطر الترقية:** Low.
- **معايير القبول:** 360–430px قابلة للاستخدام؛ الدرج يفتح من الجهة الصحيحة في RTL؛ لمس ≥ 44px للعناصر المخصصة.

### S-13 — إمكانية الوصول

- **السلوك الحالي:** سمات `high-contrast-light/dark`، محدد حجم الخط، `LiveAnnouncer`، نافذة اختصارات لوحة المفاتيح؛ تسميات
  ARIA مترجمة (العربية `com_a11y_*` 3/10).
- **التخصيص المطلوب (عام):** WCAG 2.1 AA للعناصر المخصصة (NFR-ACC-01)؛ تباين ≥ 4.5:1 لألوان الهوية.
- **الطريقة:** لا تغيير؛ الألوان S-14؛ ترجمات ARIA L4.
- **المصدر / موقع الإعداد:** `client/src/components/Appearance/Selectors.tsx:28-29`، `packages/client/src/theme/highContrast.css`،
  `client/src/App.jsx:53`.
- **خطر الترقية:** Medium (ألوان مخصصة قد تكسر التباين).
- **معايير القبول:** فحص تباين وتنقل لوحة المفاتيح وقارئ شاشة AR/EN — NOT RUN.

### S-14 — الألوان والخطوط (عابر للشاشات)

- **السلوك الحالي:** **لا مفتاح سمة وقت التشغيل** في مخطط v0.8.8 (`interfaceSchema` و`configSchema` بلا `theme`). الألوان: 92 رمز
  `rgb-*` تُستبدل وقت البناء بـ `REACT_APP_THEME_*` (`envPrefix`؛ من بيئة البناء أو `.env` في جذر المصدر). الخط
  `--theme-font-family: Inter, sans-serif` يُغيَّر بكود `ThemeDefinition` فقط. `theme-color` وخلفية التحميل مكتوبة في `index.html`.
- **التخصيص المطلوب (عام):** لوحة ألوان وخطوط معتمدة — TBD #7.
- **الطريقة:** الألوان L3 (أو انتظار سمة runtime upstream)؛ الخطوط L4 (أو L5 بـ ADR).
- **المصدر / موقع الإعداد:** `packages/data-provider/src/config.ts:2256,3125`، `packages/client/src/theme/themes/default.ts`،
  `client/src/utils/getThemeFromEnv.js`، `client/src/App.jsx:47-57`، `client/vite.config.ts:70-71`، `client/src/style.css:259`.
- **خطر الترقية:** **High**: L3 يعني خط بناء خاصاً وdigest مختلفاً (يمس ADR-0007/0008 وفحص SC-18)؛ سلوك `REACT_APP_THEME_*` في
  الوضع الداكن لم يُتحقق منه.
- **معايير القبول:** محجوب على #7؛ تباين AA في الوضعين؛ قرار ADR قبل أي L3.

## 5. تغطية الترجمة العربية (مقاسة)

مقاسة على `v0.8.8` بمقارنة وجود المفاتيح (مكتبة Python القياسية، داخل نسخة upstream):

```bash
python3 -c 'import json;e=json.load(open("client/src/locales/en/translation.json"));a=json.load(open("client/src/locales/ar/translation.json"));print(len(e),len(a),sum(k in a for k in e))'
# 3059 695 692
```

| المجال (بادئة المفتاح) | en | ar | التغطية |
|---|---|---|---|
| **الإجمالي** | **3059** | **692** | **22.6%** |
| الدخول `com_auth_` | 71 | 63 | 88.7% |
| التنقل والإعدادات `com_nav_` | 250 | 148 | 59.2% |
| النماذج `com_endpoint_` | 150 | 100 | 66.7% |
| الواجهة العامة `com_ui_` | 2180 | 291 | 13.3% |
| الوكلاء `com_agents_` | 98 | 17 | 17.3% |
| الأخطاء `com_error_` | 115 | 12 | 10.4% |
| الوصول `com_a11y_` | 10 | 3 | 30.0% |
| Insights `com_insights_` | 42 | 0 | 0% |

ملاحظات: 3 مفاتيح عربية لم تعد في `en`؛ 24 قيمة عربية مطابقة للإنجليزية (تُحتسب موجودة). المفاتيح الناقصة تُعرض بالإنجليزية
(`fallbackLng`). للمقارنة في الوسم نفسه: `he` 67.0%، `fa` 46.8%. الترجمات upstream تُدار عبر Locize
(`.github/workflows/locize-i18n-sync.yml`، و«Translation Guide» في README upstream)؛ يُتحقق من مسار المساهمة عند التنفيذ.

## 6. مصفوفة قبول الشاشات (AR/EN × RTL/LTR × جوال/سطح مكتب)

كل خلية = لقطة + فحص يدوي على بيئة محلية ببيانات اصطناعية. الجوال 390×844، سطح المكتب 1440×900 (§8).
النتائج 2026-10-19 (`Tested (cloud session)`، حزمة محلية بإعداد #39/#43، 70 لقطة + axe): التفصيل والأدلة في
[تقرير العربية وRTL §4](arabic-rtl-audit.md#4-مصفوفة-القبول-6-في-مصفوفة-الهوية). PASS/PARTIAL/FAIL بحسب المعيار؛ أرقام B-xx في التقرير §3.

| الشاشة | ما يُتحقق منه | AR · RTL · جوال | AR · RTL · سطح مكتب | EN · LTR · جوال | EN · LTR · سطح مكتب |
|---|---|---|---|---|---|
| الدخول `/login` | الشعار، النص البديل، العنوان، الروابط، محدد المظهر، رسائل الخطأ، اتجاه الحقول | PARTIAL (B-10، B-14) | PARTIAL (B-10، B-14) | PASS | PASS |
| الترحيب (محادثة جديدة) | التحية، التذييل (S-05c)، موضع المُدخل، اتجاه placeholder | FAIL (B-04) | FAIL (B-04) | FAIL لاسم عربي (B-04) | FAIL لاسم عربي (B-04) |
| محادثة (رسائل + مُدخل) | اتجاه الرسائل، النص المختلط، كتل الكود LTR، أزرار المُدخل، `chatDirection` | FAIL (B-07، B-13) | FAIL (B-07، B-13) | PARTIAL (B-13 لرد عربي) | PARTIAL (B-13، B-16) |
| منتقي النموذج | أسماء العرض، البحث، المحاذاة، الأيقونات | PARTIAL (B-08) | PARTIAL (B-08) | PARTIAL (B-08) | PARTIAL (B-08) |
| الشريط الجانبي / الدرج | جهة الفتح، العناصر الظاهرة، قائمة المحادثات، السحب على الجوال | PARTIAL (B-06، B-11) | PARTIAL (B-06، B-11) | PASS | PASS |
| قائمة الحساب | رابط المساعدة (S-04)، الخروج، الترجمة | PARTIAL (نصوص إنجليزية) | PARTIAL (نصوص إنجليزية) | PASS | PASS |
| الإعدادات (عام، المحادثة، حول) | النصوص، المحددات، تبديل اللغة وبقاؤه، تبويب «حول» | FAIL (B-17، B-12) | FAIL (B-17، B-12) | PASS | PASS |
| الحوارات (حذف محادثة، الاختصارات، الشروط إن فُعّلت) | انعكاس الأزرار والإغلاق، التركيز، Escape | PARTIAL (B-10) | PARTIAL (B-10) | PASS | PASS |
| الوكلاء (المنشئ) والسوق إن فُعّل | النماذج والحقول والتسميات، عنوان التبويب | مخفي (#39) | مخفي (#39) | مخفي (#39) | مخفي (#39) |
| حالات الخطأ والفراغ | لا نماذج متاحة، خطأ خادم الدخول، صفحة 404 | PARTIAL (رسائل إنجليزية) | PARTIAL (رسائل إنجليزية) | PASS | PASS |
| التبويب و PWA | عنوان التبويب، favicon، «إضافة للشاشة الرئيسية» (الاسم والأيقونة — الجوال فقط)، معاينة الرابط | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| الوصول (عابر) | لوحة المفاتيح، قارئ الشاشة، التباين في الوضعين الفاتح والداكن والتباين العالي | PARTIAL | PARTIAL (axe: 22/24 بلا مخالفة؛ B-16) | PARTIAL | PARTIAL (B-16)؛ قارئ الشاشة NOT RUN |

## 7. الترقية والترحيل والتراجع

يكمّل إجراءات [runbook §3](../../operations/runbook.md#3-الترقية-upgrade) و[§4](../../operations/runbook.md#4-التراجع-rollback) (NFR-MNT-01).

### 7.1 ما يرتبط بالإصدار

| الصنف | العناصر | سلوك الترقية |
|---|---|---|
| إعداد L1 | `librechat.yaml` (`version: 1.3.17` + المفاتيح)، متغيرات `librechat.env` | المخطط قد يضيف/يحذف مفاتيح؛ يُراجع مع `UPGRADING.md` |
| أصول L2 | `/app/client/dist/assets/{logo.svg,favicon-16x16.png,favicon-32x32.png,apple-touch-icon-180x180.png,icon-192x192.png,maskable-icon.png}` | **مرتبطة بالإصدار**: يُتحقق من بقاء الأسماء والمواقع وغياب نسخ `.gz/.br` في الصورة الجديدة |
| حالة في MongoDB | صلاحيات الأدوار من `interface.*`، اللافتات، فئات الوكلاء، قبول الشروط | لا تُعاد تلقائياً بحذف المفتاح من الإعداد |
| حالة في المتصفح | cookie/localStorage `lang`، `chatDirection`، `color-theme`، precache لـ Service Worker، كاش الأصول (يومان) | قد يرى المستخدم الأصل القديم بعد التغيير أو التراجع |

### 7.2 فحص الفرق عند كل ترقية LibreChat

1. فرق upstream بين الوسمين على الأسطح المعنية:
   `git diff v0.8.8..<new> -- client/index.html client/vite.config.ts client/public/assets client/src/components/Auth client/src/components/Chat/Footer.tsx client/src/components/Chat/Landing.tsx api/server/routes/config.js api/server/index.js api/config/paths.js packages/data-provider/src/config.ts client/src/locales/ar client/src/locales/en`
2. قائمة الملفات في الصورة الجديدة: `docker run --rm --entrypoint ls <image@digest> /app/client/dist /app/client/dist/assets` — وجود أهداف L2 وغياب `<name>.gz/.br`.
3. إعادة قياس تغطية العربية (§5) ومقارنة المفاتيح الجديدة في الشاشات P0.
4. هل أصبح المطلوب متاحاً على مستوى أدنى (سمة runtime، شعار قابل للإعداد، لغة افتراضية)؟ إن نعم يُستبدل L2/L3 بـ L1 ويُحدّث هذا الجدول.
5. إعادة التقاط خط الأساس البصري (§8) ومقارنته قبل الدمج.

### 7.3 التراجع

| ما يُتراجع عنه | الإجراء | ملاحظة |
|---|---|---|
| متغير بيئة / مفتاح `librechat.yaml` | `git revert` عبر PR؛ Railway عبر `railway.ts` و`config plan/apply` (ADR-0009) أو النشر التلقائي للمسارات المراقبة (ADR-0010) | مفاتيح `interface.*` للصلاحيات: تُضبط **صراحةً** بالقيمة السابقة، لأن حذفها يُبقي القيمة المحفوظة في MongoDB (`packages/api/src/app/permissions.ts`: «Preserving existing permissions») |
| أصل L2 | حذف سطر التركيب (Compose) أو `COPY` (Railway) ثم إعادة النشر — ملف upstream الأصلي يعود لأن طبقة الصورة الرسمية لم تُمس | المتصفحات قد تحتفظ بالنسخة المستبدلة حتى انتهاء الكاش أو تحديث SW؛ تحديث قسري أو إلغاء تسجيل SW عند الحاجة |
| صورة L3 | العودة إلى الصورة الرسمية بالـ digest نفسه | يتطلب ADR مسبقاً يحدد خط البناء والتراجع |
| L4 | لا تراجع محلي؛ يصل مع إصدار upstream ويُعامل كترقية | — |

## 8. خطة أدلة خط الأساس البصري

الحالة: **Done (جزئي) — المرحلة (1)** 2026-10-19: 12 لقطة لـ v0.8.8 كما هو
([`baseline/v0.8.8/` عند commit `86d6546`](https://github.com/faenazi/ef-ai-workspace/tree/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/baseline/v0.8.8))
— الدخول والترحيب والمحادثة × `ar`/`en` × 390×844/1440×900، الوضع الفاتح.
البيئة: حزمة Compose محلية بالـ digest المثبّت + overlay النموذج الوهمي (#38، `tests/integration/compose.mock-llm.yaml`)،
مستخدم اصطناعي؛ الأداة Playwright 1.56.1 (Chromium مثبّت مسبقاً) بلغة المتصفح `ar` أو `en-US` ودون تفضيل محفوظ. لم يُستخدم رابط
Railway. **أُكمل في #44 (2026-10-19)** بإعدادنا L1: الوضع الداكن، الإعدادات، الحوارات، الدرج على الجوال، المُدخل، Markdown مختلط،
axe — 70 لقطة، المختار منها في
[`screens/v0.8.8-l1/` عند commit `86d6546`](https://github.com/faenazi/ef-ai-workspace/tree/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1)
([تقرير RTL](arabic-rtl-audit.md)). الوكلاء مخفيون منذ #39؛ قارئ الشاشة NOT RUN.

**الحفظ (قرار المالك 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75)):** لا تُحفظ لقطات الشاشة في شجرة
المستودع. خط الأساس وأدلة القبول يُشار إليها بروابط دائمة إلى commit الدمج على GitHub، ولقطات القبول اللاحقة تُرفع في الـ PR
أو الـ Issue ([ux-standards.md §6](../ux-standards.md#6-مراجعة-التصميم-design-review)).

### 8.1 ملاحظات من خط الأساس (upstream كما هو)

| ID | الملاحظة | اللقطة | الصلة |
|---|---|---|---|
| B-01 | لغة المتصفح العربية تكفي لواجهة عربية RTL (`<html dir="rtl" lang="ar">`) في الدخول والمحادثة | `login_ar_*`، `chat_ar_*` | S-10؛ G-08 يبقى لمتصفح غير عربي |
| B-02 | عنوان التبويب = `APP_TITLE` «بصير \| صندوق البيئة» في التوليفات الأربع | (فحص `document.title`) | S-03a — `Tested (cloud session)` محلياً |
| B-03 | شعار LibreChat (الريشة) في الدخول والترحيب | `login_*`، `landing_*` | S-02، G-01 |
| B-04 | تحية الترحيب في العربية: «Winding down,» إنجليزية، واسم المستخدم العربي يُرسم بحروف **منفصلة** أثناء حركة الكتابة (كسر وصل الحروف العربية) | `landing_ar_*` | **عيب RTL/عربي** لـ #44 (S-05a، G-07، G-11) |
| B-05 | تذييل «LibreChat v0.8.8 - …» ظاهر في الترحيب | `landing_ar_desktop`، `landing_en_desktop` | S-05c — يُعالج بـ `CUSTOM_FOOTER` (#43 الجزء A) |
| B-06 | عناصر الشريط «Projects» و«Chats» و«New Chat» غير مترجمة في العربية | `landing_ar_desktop`، `chat_ar_desktop` | G-07 (#44) |
| B-07 | المُدخل في العربية يبقى LTR (النص البديل يسار الحقل) | `chat_ar_*`، `landing_ar_*` | S-05b، G-09 |
| B-08 | منتقي النموذج يعرض المعرّف الخام `baseer-mock-echo`؛ الترحيب يطلب «تحديد الوكيل» قبل اختيار نموذج | `chat_*`، `landing_*` | S-06 — أسماء عرض `modelSpecs` مع #37/#39 |
| B-09..B-17 | عيوب إضافية من تدقيق #44 (أيام التحيات، ARIA ثابتة، مؤشر RTL، قيم خام، كود RTL، ترتيب Tab، ترقيم القوائم، تباين الكود الداكن، الإعدادات غير معكوسة) | [`screens/v0.8.8-l1/`](https://github.com/faenazi/ef-ai-workspace/tree/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1) | [تقرير RTL §3](arabic-rtl-audit.md#3-العيوب-قبل) |

| البند | الخطة |
|---|---|
| البيئة | حاوية محلية بالـ digest المثبّت (`tests/smoke/compose-stack.sh local`)، حساب مسؤول اصطناعي، بلا بيانات حقيقية |
| الأداة | متصفح headless (مثل Playwright/Chromium) — توفرها في الجلسة يُتحقق منه عند التنفيذ |
| التوليفات | الشاشات في §6 × `ar`/`en` (cookie `lang`) × 390×844 / 1440×900 × الوضع الفاتح/الداكن (الداكن مهم للشعار) |
| التسمية | `<screen>_<ar\|en>_<mobile\|desktop>_<light\|dark>.png` |
| الحفظ | خارج الشجرة: في الـ PR/Issue المعني، أو برابط دائم إلى commit عند الحاجة لمرجع ثابت |
| المراحل | (1) upstream v0.8.8 كما هو قبل أي تغيير؛ (2) بعد كل PR هوية؛ (3) بعد كل ترقية LibreChat |
| المقارنة | مراجعة جنباً إلى جنب وفق [قائمة مراجعة التصميم](../ux-standards.md#6-مراجعة-التصميم-design-review) |

## 9. القيود والفجوات (تتطلب upstream PR أو fork ADR)

لا فجوة في v0.8.8 تُلزم بـ fork الآن؛ كل ما يلي له مسار L4 (أو L2/L3 مؤقت) موثق:

| # | الفجوة | الأثر | المسار المقترح |
|---|---|---|---|
| G-01 | لا إعداد للشعار وfavicon وأيقونات PWA | علامة upstream في الدخول والتبويب والشاشة الرئيسية | L2 الآن (S-02)؛ L4: مسار شعار/أيقونات قابل للإعداد |
| G-02 | manifest مكتوب وقت البناء (`LibreChat`، `#009688`) | اسم التطبيق المثبّت على الجوال | L4: manifest يُولّده الخادم من `APP_TITLE`؛ L2 فقط بقبول صريح للخطر High |
| G-03 | `<title>` والوصف و`theme-color` ثابتة في `index.html` | العنوان الأولي ومعاينات الروابط | L4: استبدال على الخادم في `sendIndexHtml` (كما يُستبدل `lang`) |
| G-04 | «\| LibreChat» ثابتة في Insights وMarketplace | عنوان التبويب في شاشتين | L4: استخدام `appTitle`؛ مغلقة في Railway (تعديل 0025، #152) |
| G-05 | لا سمة ألوان وقت التشغيل | ألوان الهوية | انتظار إصدار upstream (ADR-0006 يذكر دمجها في `dev`؛ يُعاد التحقق عند الترقية)؛ L3 بقرار ADR فقط؛ مغلقة في Railway بـ L5 (`brand.css`، ADR-0013) |
| G-06 | لا إعداد للخط؛ Inter لاتيني فقط | الخط العربي الرسمي | L4؛ مغلقة في Railway بـ L5 (ADR-0013: تعديلا 0006 و0025، #152) |
| G-07 | تغطية العربية 22.6% مع احتياط إنجليزي | واجهة مختلطة | L5 في Railway ([ADR-0013](../../architecture/adr/0013-arabic-web-client-build.md)): 100%؛ الدائم L4 عبر Locize |
| G-08 | لا لغة افتراضية على الخادم؛ لا محدد لغة في الدخول؛ التفضيل لكل متصفح | العربية ليست افتراضية مضمونة (FR-006 AC-1) | L5 في Railway: العربية افتراضية بلا اختيار محفوظ (ADR-0013)؛ محدد الدخول L4 |
| G-09 | اتجاه المُدخل الافتراضي `LTR` مستقل عن لغة الواجهة | تجربة كتابة عربية | L5 في Railway: `dir=auto` (ADR-0013)؛ الدائم L4 |
| G-10 | نصوص الإعداد لغة واحدة (`customWelcome`، `CUSTOM_FOOTER`، الشروط، `modelSpecs`، اللافتة) | ثنائية اللغة | L4: توسيع `LocalizedString` الموجود |
| G-11 | CSS اتجاهي فيزيائي في أغلب المكونات | عيوب RTL محتملة | L4: إصلاح كل عيب يُكتشف في #44 upstream |
| G-12 | `logo.svg` واحد للوضعين | قيد تصميم على الشعار | متطلب في #7 (شعار مقروء على الخلفيتين) أو L4 |

## 10. التوصية المرتّبة لـ #43 و#44

1. **#44 الآن (لا يعتمد على #7):** إكمال خط الأساس (§8: الداكن، الإعدادات، الحوارات، الدرج) وتنفيذ مصفوفة §6، بدءاً بـ B-04 وB-06 وB-07،
   ثم المساهمة upstream (Locize للترجمات بدءاً بـ `com_ui_`/`com_nav_`/`com_error_`، وIssues/PRs لـ G-08 وG-09 وG-11).
2. **#43 — الجزء A (L1، لا يعتمد على #7) — منفّذ للإخفاء (§11):** إزالة تسرّب علامة upstream: `HELP_AND_FAQ_URL=/` أو رابط داخلي معتمد،
   و`CUSTOM_FOOTER` مؤقت موسوم `PROVISIONAL` أو `""`، وقرار `interface.buildInfo`، وضبط `interface.marketplace` صراحة،
   ولافتة «بيئة تجريبية — بيانات اصطناعية». التغيير في `librechat.env` و`railway.ts` معاً ويُعامل كتغيير بنية (ADR-0011).
3. **#43 — الجزء B (L2، بعد #7):** الأصول في `assets/brand/` تُركّب read-only في Compose وتُنسخ في Dockerfile الخاص بـ Railway
   على أهداف S-02، مع تحديث watch paths (ADR-0010) وفحوص التطابق، وقرار مكتوب (ADR جديد أو ملحق ADR-0006) يوثق أهداف L2
   وفحص الترقية (§7.2).
4. **L4 بالتوازي:** Issues/PRs upstream لـ G-01 إلى G-04 وG-10 — تقلل الاعتماد على L2 في الترقيات اللاحقة.
5. **الألوان والخطوط:** لا L3 ولا fork دون ADR؛ يُعاد تقييمها عند اعتماد #7 وعند كل ترقية (G-05، G-06).

## 11. المطبّق بإعداد L1 — #43 الجزء A (2026-10-19)

إخفاء لا استبدال: لا نص تذييل ولا صفحة مساعدة ولا هوية معتمدة بعد ([#7](https://github.com/faenazi/ef-ai-workspace/issues/7)). ملف
`LICENSE` (MIT) يبقى في الصورة؛ الترخيص يشترط الإشعار في نسخ البرنامج لا في الواجهة.

| السطح | الإعداد | قبل | بعد | الدليل (لقطات عند commit `86d6546`) |
|---|---|---|---|---|
| S-05c التذييل (الترحيب والدخول) | `CUSTOM_FOOTER=` (فارغ) في `librechat.env` + `railway.ts` | رابط «LibreChat v0.8.8» إلى librechat.ai | لا تذييل | [`landing_ar_desktop_light`][l1-landing_ar_desktop_light]، [`landing_en_mobile_light`][l1-landing_en_mobile_light]، [`login_ar_mobile_light`][l1-login_ar_mobile_light] |
| S-04 «Help & FAQ» | `HELP_AND_FAQ_URL=/` | رابط إلى `https://librechat.ai` | قائمة «Help» فيها «Keyboard Shortcuts» فقط | [`account_menu_en_desktop_light`][l1-account_menu_en_desktop_light] |
| S-07 تبويب «حول» + `/api/config` | `interface.buildInfo: false` | «LibreChat version» والـ commit والفرع وتاريخ البناء، **حتى لغير المسجلين** في `/api/config` | لا تبويب «حول»؛ لا `buildInfo` في `/api/config` | [`settings_ar_desktop_light`][l1-settings_ar_desktop_light]؛ `mock_chat.py` M37 |

الشاشات في [`screens/v0.8.8-l1/` عند commit `86d6546`](https://github.com/faenazi/ef-ai-workspace/tree/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1)
= v0.8.8 بإعدادنا (L1: #39 + #43 الجزء A)، بيانات اصطناعية، Playwright 1.56.1 على حزمة محلية؛ المقارنة مع خط الأساس
[`baseline/v0.8.8/`](https://github.com/faenazi/ef-ai-workspace/tree/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/baseline/v0.8.8).
باقٍ في #43: الشعار وfavicon وPWA وعنوان `index.html` (L2/L4، بعد #7). `HELP_AND_FAQ_URL` قيمة ثابتة مسموحة استثناءً في
`compose_checks.py` (`/` فقط؛ أي URL يُرفض — N18).

## 12. تبسيط الواجهة بأسلوب ChatGPT بإعداد L1 — المرحلة 1 ([#87](https://github.com/faenazi/ef-ai-workspace/issues/87)، 2026-10-20)

بالإعداد فقط (`librechat.yaml`)، دون أصول هوية ([#7](https://github.com/faenazi/ef-ai-workspace/issues/7)). الفحص الآلي `mock_chat.py` M39–M45.

| السطح | الإعداد | قبل | بعد |
|---|---|---|---|
| قائمة النماذج | `modelSpecs` بلا `group`؛ `interface.modelSelect: false` | الخيارات داخل مجموعة فرعية «بصير»، والقائمة الخام ظاهرة | ثلاثة خيارات مباشرة، واسم المختار على الزر |
| شاشة البداية | `interface.customWelcome` + `preset.greeting` + `conversation_starters` | تحية upstream وصف النموذج فقط | «كيف أساعدك اليوم؟»، سطر لكل خيار فيه «استخدم بيانات اصطناعية فقط»، وأربعة اقتراحات ≤ 56 حرفاً |
| عناصر متقدمة | `presets` = `false`؛ `parameters` (#108) و`multiConvo` و`contextUsage` (#125) = `true` | إعدادات النموذج والإعدادات المسبقة والمقارنة ومؤشر السياق | الإعدادات المسبقة مخفية؛ المعلمات والمقارنة (زر «+» على الكمبيوتر) ومؤشر السياق ظاهرة (المؤشر على الجوال من نصف السياق، #175)؛ تبقى المحادثة المؤقتة والقوالب والمشاريع والإشارات المرجعية والتقييم |

- **الفحص البصري:** Playwright على حزمة محلية بنموذج وهمي، عربي RTL (`dir=rtl`، `lang=ar`) بعرض 390 و320 وسطح المكتب؛ الاقتراحات كاملة بعرض 320.
  اللقطات أُرسلت للمالك ولا تُحفظ في المستودع.
- **باقٍ للمرحلة 2 (نصوص upstream إنجليزية):** «Search models»، «Projects»، «Chats»، «Thoughts». نصوص المواصفات ليست حسب اللغة في
  v0.8.8، فالعربية هي اللغة الأساسية.

<!-- لقطات الشاشة: روابط دائمة إلى commit 86d6546 (reference-style لإبقاء الصفوف قصيرة) -->

[l1-account_menu_en_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/account_menu_en_desktop_light.png
[l1-landing_ar_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/landing_ar_desktop_light.png
[l1-landing_en_mobile_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/landing_en_mobile_light.png
[l1-login_ar_mobile_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/login_ar_mobile_light.png
[l1-settings_ar_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/settings_ar_desktop_light.png
