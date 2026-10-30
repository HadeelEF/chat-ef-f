# هيكل نظام التصميم (Design System Structure)

| الحقل | القيمة |
|---|---|
| الحالة | القيم مطبّقة من دليل الهوية (D-04 بقرار المالك 2026-10-20، [#7](https://github.com/faenazi/ef-ai-workspace/issues/7))؛ المصدر الوحيد [`brand.css`](../../infrastructure/common/client/brand/brand.css) |

## 1. الهدف

تعريف **أين** و**كيف** تُدار قيم التصميم. القيم من دليل الهوية لصندوق البيئة، وتوزيعها على أدوار الواجهة موثّق في
[brand-guidelines.md §2](brand-guidelines.md#2-توزيع-الألوان-في-الواجهة-تخصيص-المشروع).

## 2. فئات الرموز (Design Tokens)

الموقع: [`infrastructure/common/client/brand/brand.css`](../../infrastructure/common/client/brand/brand.css) (مصدر وحيد)، بصيغة متغيرات
LibreChat (`--text-*`، `--surface-*`، `--border-*`، `--theme-font-family`) لمظهر فاتح واحد (#108).

| الفئة | أمثلة المفاتيح | القيمة |
|---|---|---|
| الألوان | `--text-*`، `--surface-*`، `--border-*`، `--surface-submit`، `--link`، `--ring-primary` | من لوحة الدليل؛ الحالات `--status-*` من LibreChat |
| الطباعة | `--theme-font-family`، `fontFamily.sans` | Aktiv Grotesk (عربي ولاتيني) ثم Tahoma؛ الأحجام من LibreChat |
| المسافات | `space.1…8` | تتبع LibreChat الافتراضية حتى M2 |
| الزوايا والظلال | `radius.*`, `shadow.*` | تتبع LibreChat الافتراضية |
| الأيقونات | مجموعة أيقونات LibreChat الحالية؛ رمز الصندوق لأيقونة التطبيق و«بصير» | لا مكتبة أيقونات رسمية في الدليل |

## 3. المكونات

لا مكتبة مكونات مخصصة: نستخدم مكونات LibreChat. أي مكوّن جديد يتطلب مبرراً في Issue وتقييماً ضمن ADR-0006.

## 4. آليات التطبيق في LibreChat

متحقق منها في مصدر وتوثيق v0.8.8 (2026-10-17):

| الحاجة | الآلية المدعومة | المستوى (ADR-0006) | ملاحظات |
|---|---|---|---|
| اسم التطبيق | `APP_TITLE` (`/api/config` → `appTitle`) | 1 | يغطي عنوان التبويب والنص البديل لشعار الدخول ومُصدِر 2FA؛ لا يغطي `<title>` الثابت واسم PWA والشعار؛ لا يظهر في متن صفحة الدخول — التفاصيل تحت الجدول |
| تذييل وروابط المساعدة | `CUSTOM_FOOTER`, `HELP_AND_FAQ_URL`؛ `interface.buildInfo` (تبويب «حول») | 1 | **مطبّق:** `CUSTOM_FOOTER` تنبيه ثقة تحت صندوق الكتابة «بصير قد يخطئ…» (#100؛ وعلى الجوال في شاشة الترحيب، #103)؛ «دليل الاستخدام» `HELP_AND_FAQ_URL=/assets/ef-help.html` (#103)؛ النصان `PROVISIONAL` (#7)؛ `buildInfo: false` (#43) |
| رسالة الترحيب، سياسة الخصوصية، الشروط | `interface.customWelcome`, `interface.privacyPolicy`, `interface.termsOfService` | 1 | — |
| الألوان وقت التشغيل | `interface.theme` | **غير متوفر في v0.8.8** | مدمج في فرع `dev`؛ متوقع في إصدار لاحق — يُعاد التحقق في M2 |
| الألوان والخط وقت البناء | `brand.css` يُلحق بـ `style.css` عند بناء الواجهة | 5 ([ADR-0013](../architecture/adr/0013-arabic-web-client-build.md)) | واجهة Railway فقط؛ Compose upstream حتى #17 |
| الشعار و favicon واسم PWA | لا آلية مدعومة؛ تستبدل `brand/assets/` ملفات upstream بالاسم نفسه عند البناء، والتعديل 0006 يضيف الشعار الداكن واسم التطبيق، و0007 لوحة الدخول وشعار اللوحة الجانبية وألوان الإجراء الرئيسي، و0011 وصف التطبيق واختصار «محادثة جديدة» (#105)، و0031 (#181) | 5 ([ADR-0013](../architecture/adr/0013-arabic-web-client-build.md)) | البناء يفشل إن غيّر upstream اسم ملف مستبدَل |
| اللغة العربية الافتراضية والترجمة | لا إعداد في v0.8.8؛ بناء الواجهة من المصدر المثبّت مع `ar.json` وتعديل اللغة الافتراضية | 5 ([ADR-0013](../architecture/adr/0013-arabic-web-client-build.md)) | واجهة Railway: ترجمة 100% يفرضها البناء والعربية افتراضية؛ Compose: upstream (~23%) حتى #17 |

**تفاصيل `APP_TITLE`** (متحقق في مصدر v0.8.8 `e8f3be0` وبمتصفح headless على حاوية محلية، AR/EN × جوال/سطح مكتب، 2026-10-19):

- **يغطي:** عنوان تبويب المتصفح بعد تحميل الواجهة (ما لم يُعرض عنوان المحادثة)، النص البديل لشعار صفحة الدخول، اسم المُصدِر في تطبيق 2FA
  (تُحذف المسافات: `بصير\|صندوقالبيئة`؛ القيود القائمة لا تتغير بتغيير الاسم)، رسائل البريد (غير مُفعّلة).
- **لا يغطي (build-time):** `<title>` الثابت في `index.html` ووصف الصفحة واسم تطبيق PWA — تضبطها واجهة Railway بالاسم نفسه
  (ADR-0013، التعديل 0006)؛ وعناوين صفحتي Insights وMarketplace (`… \| LibreChat`، مخفيتان).
- **لا يظهر الاسم في متن صفحة الدخول** (الترحيب نص ثابت مترجم)؛ على الجوال يُرى عادةً في مبدّل التبويبات والسجل فقط.

التدقيق التفصيلي لكل شاشة (الطريقة، المصدر، خطر الترقية، معايير القبول، الترقية والتراجع):
[audits/brand-implementation-matrix.md](audits/brand-implementation-matrix.md) ([#42](https://github.com/faenazi/ef-ai-workspace/issues/42)).

## 5. المراجعة

قائمة المراجعة في [ux-standards.md](ux-standards.md#6-مراجعة-التصميم-design-review).
