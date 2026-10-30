# تدقيق العربية وRTL وإمكانية الوصول (Arabic / RTL / Accessibility Audit)

| الحقل | القيمة |
|---|---|
| الحالة | **Audit + evidence `Tested (cloud session)`** (2026-10-19). الإصلاحات والترجمات **مطبّقة في واجهة Railway** عبر [ADR-0013](../../architecture/adr/0013-arabic-web-client-build.md) (#89)؛ المسار الدائم upstream (L4) |
| Issue | [#44](https://github.com/faenazi/ef-ai-workspace/issues/44) (R0.3، P0) · FR-006، NFR-I18N-01، NFR-ACC-01 · [مصفوفة الهوية §6](brand-implementation-matrix.md#6-مصفوفة-قبول-الشاشات-aren--rtlltr--جوالسطح-مكتب) |
| البيئة | حزمة Compose محلية: LibreChat v0.8.8 بالـ digest المثبّت + إعدادنا (`main@6dddb67`: #39 + #43 الجزء A) + النموذج الوهمي (#38، ومنه `baseer-mock-markdown`)؛ مستخدم اصطناعي «سارة الاختبار»؛ **ليس Railway** |
| الأدوات | Playwright 1.56.1 (Chromium 1194)؛ axe-core 4.10.3 (قواعد `wcag2a`، `wcag2aa`، `wcag21a`، `wcag21aa`)؛ 390×844 و1440×900؛ الوضعان الفاتح والداكن |
| الحجم | **70 لقطة «قبل»** (9 شاشات × AR/EN × جوال/سطح مكتب × فاتح/داكن)، 24 فحص axe لشاشات سطح المكتب، ولقطات «بعد» للشاشات المتأثرة (الفاتح) من البناء التجريبي |
| التاريخ | 2026-10-19 |
| اللقطات | خارج الشجرة بقرار المالك (2026-10-20): روابط دائمة إلى commit `86d6546` على GitHub ([`screens/`](https://github.com/faenazi/ef-ai-workspace/tree/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens)) |

## 1. الخلاصة

- **ما يعمل:** `<html dir="rtl" lang="ar">` في العربية؛ الرسائل `dir="auto"` فتُعرض الفقرات المختلطة والجداول والروابط صحيحة؛ القوائم
  والحوارات تُغلق بـ Escape؛ حلقة التركيز ظاهرة؛ axe لم يجد مخالفات WCAG آلية في 22 من 24 شاشة.
- **ما لا يعمل (13 عيباً، §3):** التحية بحروف منفصلة وبالإنجليزية (B-04) — **حتى في الواجهة الإنجليزية لأي اسم عربي**؛ المُدخل يبقى LTR
  مع نص عربي (B-07)؛ كتل الكود تنقلب RTL وتُقرأ مشوهة (B-13)؛ نافذة الإعدادات غير معكوسة (B-17)؛ تسميات ARIA ونصوص شائعة بالإنجليزية.
- **سبب كل العيوب في كود الواجهة أو حزم الترجمة المبنية** — لا يحلها أي إعداد في v0.8.8. المطبّق في بصير بالإعداد فقط: إخفاء الأسطح
  غير المعتمدة (الوكلاء، Skills، الذاكرة — وكلها غير مترجمة، #39) وتذييل upstream (#43 الجزء A).
- **الإصلاح المقترح جاهز ومُختبر:** 21 سطراً في 6 ملفات + 158 ترجمة من [المسرد](../arabic-glossary.md)، بُنيت محلياً من مصدر v0.8.8 وأثبتت
  إصلاح B-04 وB-06 وB-07 وB-13 وتسميات ARIA (§6). **لم تُنشر**؛ مسارها upstream (ADR-0006 L4).

## 2. ما فُحص وكيف

| الفحص | الطريقة | النتيجة |
|---|---|---|
| اتجاه المستند واللغة | `document.documentElement.lang/dir` في كل لقطة | `ar`/`rtl` و`en`/`ltr` في 70/70 |
| المُدخل | `dir` و`direction` المحسوب، فارغاً ثم بنص عربي | `ltr/ltr` في 16/16 (B-07) |
| Markdown مختلط | رد `baseer-mock-markdown` (عنوان، قائمة، رابط، كود فيه عربي، جدول) | الفقرات والجدول صحيحة؛ الكود RTL (B-13)؛ التخزين مطابق بايتاً ببايت (`mock_chat.py` M38) |
| الحوارات | حذف محادثة: فتح ثم Escape | يُغلق في 8/8 |
| لوحة المفاتيح | 4× Tab في صفحة الدخول | التركيز يصل كلمة المرور بعد زري المظهر؛ الحلقة ظاهرة ([لقطة][l1-focus_login_ar_desktop_light]) |
| WCAG آلياً | axe-core على 24 شاشة سطح مكتب (دخول، ترحيب، محادثة، Markdown، إعدادات، حذف × AR/EN × فاتح/داكن) | مخالفة واحدة: `color-contrast` (serious) لعنوان الكود `.hljs-title` في الوضع الداكن (B-16) |
| قارئ الشاشة | — | **NOT RUN** (لا قارئ شاشة في الجلسة)؛ تسميات ARIA فُحصت نصياً |
| Railway / الهاتف الحقيقي | — | **NOT RUN** (الرابط العام غير متاح من الجلسة)؛ فحص المالك من الجوال مقترح |

## 3. العيوب (قبل)

`B-01..B-08` من [خط الأساس](brand-implementation-matrix.md#81-ملاحظات-من-خط-الأساس-upstream-كما-هو)؛ B-09 فما بعد جديدة. المسارات نسبية لجذر upstream v0.8.8.
اللقطات بروابط دائمة إلى commit `86d6546`.

| ID | العيب | السبب الجذري | الدليل | المسار |
|---|---|---|---|---|
| B-04 | التحية إنجليزية («Winding down,») والاسم العربي بحروف منفصلة وترتيب مقلوب؛ **في الواجهة الإنجليزية أيضاً** | (1) مفاتيح `com_ui_greeting_*` الـ 48 غائبة عن `ar`؛ (2) `SplitText.tsx:48-59,157-165` يضع كل حرف في `inline-block` فينقطع الوصل؛ (3) `customWelcome` لا يفيد (أدناه) | [AR][l1-landing_ar_desktop_light]، [EN داكن][l1-landing_en_desktop_dark] | L4: كلمة كاملة + ترجمة |
| B-06 | «Projects» و«Chats» و«New Chat» إنجليزية | `com_ui_chats`/`com_ui_projects` غائبان؛ «New Chat» عنوان افتراضي **مخزّن** لا مفتاح (`client/src/hooks/useNewConvo.ts:368`) | [الدرج][l1-drawer_ar_mobile_light] | L4: ترجمة + عرض العنوان الافتراضي بلغة الواجهة |
| B-07 | المُدخل LTR حتى مع نص عربي (الترقيم والكلمات اللاتينية تنزاح) | `dir` الحقل من `chatDirectionAtom` (Jotai) افتراضيه `'ltr'` ولا يكتبه أي كود (`packages/client/src/store.ts:4-6`، `TextareaAutosize.tsx:29-31`)؛ إعداد «اتجاه الدردشة» يعكس الأزرار فقط | [جوال][l1-composer_ar_mobile_light] | L4: `auto` |
| B-08 | منتقي النموذج يعرض المعرّف الخام | لا `modelSpecs` بعد | — | L1 مع #37 |
| B-09 | تحيات «أسبوع جديد» الإثنين و«فترة المساء» الجمعة | جدول أيام ثابت (`client/src/utils/greeting.ts:108-113,140`) | المسرد §5 | L4: بداية أسبوع حسب اللغة |
| B-10 | تسميات ARIA إنجليزية: «Show/Hide secret»، `aria-label="cancel"`، «Toggle theme»، «Toggle high contrast»، «Message input» | نص ثابت في `SecretInput.tsx:137` و`ConvoOptions/DeleteButton.tsx:105` و`Chat/Menus/PresetsMenu.tsx:138`؛ والباقي مفاتيح غير مترجمة | فحص DOM | L4 |
| B-11 | مؤشر المحادثة النشطة على اليسار في RTL | `before:left-0` فيزيائي (`client/src/components/Conversations/Convo.tsx:317`) | [الدرج][l1-drawer_ar_mobile_light] | L4: `before:start-0` |
| B-12 | قيم خام في الإعدادات: اللغة `ar`، الاتجاه `ltr` | `ChatDirection.tsx:31` يعرض `direction.toLowerCase()`؛ محدد اللغة يعرض الرمز | [الإعدادات][l1-settings_ar_desktop_dark] | L4 |
| B-13 | كتلة الكود داخل رد عربي تصبح RTL فتنقلب الأقواس والنقطتان والسلاسل | الرسالة `dir="auto"` والكود يرث الاتجاه (`client/src/components/Messages/Content/CodeBlock.tsx:101-104` بلا `dir`) | [AR][l1-chat_md_ar_desktop_light]، [EN داكن][l1-chat_md_en_desktop_dark] | L4: `dir="ltr"` |
| B-14 | ترتيب Tab في الدخول يبدأ بزري المظهر المرسومين أسفل الصفحة | ترتيب DOM | فحص لوحة المفاتيح | L4 (منخفض) |
| B-15 | سطر إنجليزي داخل قائمة عربية تنتقل نقطته لليسار | `li` يرث RTL؛ لا `dir="auto"` لعناصر القائمة | [AR][l1-chat_md_ar_desktop_light] | L4 (منخفض) |

B-04: المكوّن المقصود `packages/client/src/components/SplitText.tsx`؛ `customWelcome` يمر بنفس المكوّن فلا حل بالإعداد.
| B-16 | تباين `.hljs-title` في الكود بالوضع الداكن دون AA | لون سمة الإبراز | axe `color-contrast` (2 عقدتان) | L4 |
| B-17 | نافذة الإعدادات غير معكوسة في RTL: التبويبات يساراً، التسميات يساراً والتحكم يميناً؛ عناوين الأقسام وعدة إعدادات إنجليزية | CSS فيزيائي في `client/src/components/Nav/Settings/` + مفاتيح غائبة | [الإعدادات][l1-settings_ar_desktop_dark] | L4 |

نصوص أخرى غير مترجمة رُصدت في الشاشات: «Help»، «Keyboard Shortcuts»، «Data & Privacy»، «Search settings»، «Filter and sort chats» — كلها
في [المسرد](../arabic-glossary.md). رسائل الخطأ إنجليزية فقط (انظر [ai-safe-defaults §4](../../architecture/ai-safe-defaults.md#4-سلوك-فشل-المزوّد-مقاس-على-النموذج-الوهمي)).

## 4. مصفوفة القبول (§6 في مصفوفة الهوية)

PASS = يحقق المعيار؛ PARTIAL = يعمل مع عيوب محددة؛ FAIL = المعيار الأساسي لا يتحقق. الجوال وسطح المكتب نفس النتيجة ما لم يُذكر.

| الشاشة | AR · RTL | EN · LTR | ملاحظات |
|---|---|---|---|
| الدخول | PARTIAL (B-10، B-14) | PASS | لا تذييل upstream (#43)؛ الحقول والزر مترجمة |
| الترحيب | **FAIL** (B-04) | **FAIL** لاسم عربي (B-04) | لا تذييل |
| المحادثة (رسائل + Markdown) | PARTIAL (B-13، B-15) | PARTIAL (B-13 لرد عربي، B-16 داكن) | الفقرات المختلطة والجدول والرابط صحيحة |
| المُدخل | **FAIL** (B-07) | PASS | — |
| منتقي النموذج | PARTIAL (B-08) | PARTIAL (B-08) | يعرض الـ endpoints المضبوطة فقط (#39) |
| الشريط الجانبي / الدرج | PARTIAL (B-06، B-11) | PASS | الدرج يعمل بالسحب والزر |
| قائمة الحساب | PARTIAL (نصوص إنجليزية) | PASS | لا «Help & FAQ» إلى librechat.ai (#43) |
| الإعدادات | **FAIL** (B-17، B-12) | PASS | لا تبويب «حول» (#43) |
| حوار الحذف | PARTIAL (B-10) | PASS | Escape يُغلق |
| حالات الخطأ | PARTIAL (نص إنجليزي) | PASS | سريعة وعامة (#39) |
| الوضع الداكن | PARTIAL (B-16) | PARTIAL (B-16) | — |
| التبويب و PWA | NOT RUN | NOT RUN | الاسم/الأيقونة في #43 الجزء B |
| قارئ الشاشة | NOT RUN | NOT RUN | — |

## 5. إصلاحات upstream المقترحة (L4)

حزمة واحدة صغيرة على وسم `v0.8.8` (21 سطراً في 6 ملفات)، تُقدَّم PR/PRs إلى LibreChat مع ترجمات المسرد عبر Locize:

```diff
--- packages/client/src/components/SplitText.tsx   (B-04)
+const JOINING_SCRIPT = /[\p{Script=Arabic}\p{Script=Syriac}\p{Script=Nko}\p{Script=Mongolian}\p{Script=Adlam}]/u;
+const splitUnits = (word: string): string[] => (JOINING_SCRIPT.test(word) ? [word] : splitGraphemes(word));
+const prefersReducedMotion = (): boolean =>
+  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true;
-  const words = text.split(' ').map(splitGraphemes);
+  const words = text.split(' ').map(splitUnits);
+      immediate: prefersReducedMotion(),
--- packages/client/src/store.ts   (B-07)
-} = atom<string>('ltr');
+} = atom<string>('auto');
--- client/src/components/Messages/Content/CodeBlock.tsx   (B-13)
       ref={containerRef}
+      dir="ltr"
--- client/src/components/Conversations/ConvoLink.tsx   (B-06: stored default title)
-  const displayTitle = title || localize('com_ui_untitled');
+  const displayTitle = !title ? localize('com_ui_untitled') : title === 'New Chat' ? localize('com_ui_new_chat') : title;
--- client/src/components/Conversations/ConvoOptions/DeleteButton.tsx   (B-10)
-          <Button aria-label="cancel" variant="outline">
+          <Button aria-label={localize('com_ui_cancel')} variant="outline">
--- packages/client/src/components/SecretInput.tsx   (B-10; new keys com_ui_show_secret / com_ui_hide_secret)
-            aria-label={isVisible ? 'Hide secret' : 'Show secret'}
+            aria-label={localize(isVisible ? 'com_ui_hide_secret' : 'com_ui_show_secret')}
```

لم تُبنَ بعد في هذه الحزمة (مقترحة فقط): B-11 (`before:start-0`)، B-12، B-14، B-15 (`dir="auto"` لعناصر القائمة)، B-16، B-17، B-09،
و`aria-label="cancel"` في `PresetsMenu.tsx`. **تقديم الـ PR إلى upstream إجراء خارجي باسم المالك** — ينتظر موافقته (§7).

## 6. التحقق «قبل/بعد» — بناء محلي تجريبي فقط

بُنيت الواجهة من مصدر v0.8.8 (`e8f3be0`) + الحزمة أعلاه + 158 ترجمة من المسرد ومفتاحا ARIA الجديدان
(`npm run frontend:ci`، Node 22.22.0)، ورُكّبت للقراءة فقط على `/app/client/dist` في حاوية الاختبار المحلية فقط. التغطية العربية في هذا
البناء: **852/3061 (27.8%)** بدلاً من 692 (22.6%). أيقونة React في الزاوية أداة تطوير يُظهرها وضع `ci` وليست جزءاً من الإصلاح.
**لم يُنشر هذا البناء في أي بيئة** ولا يُقترح تشغيله (ADR-0006: L5 يتطلب ADR). اللقطات بروابط دائمة إلى commit `86d6546`.

| العيب | قبل (v0.8.8 + إعدادنا) | بعد (البناء التجريبي) | النتيجة |
|---|---|---|---|
| B-04 التحية | [«Winding down, سارة» بحروف منفصلة][l1-landing_ar_desktop_light] | [«نختم اليوم يا سارة الاختبار؟» موصولة][l4-landing_ar_desktop_light] | مُصلح |
| B-06 الشريط | [«Projects/Chats/New Chat»][l1-drawer_ar_mobile_light] | [«المشاريع/الدردشات/دردشة جديدة»][l4-landing_ar_desktop_light] | مُصلح |
| B-07 المُدخل | [`ltr`: «Baseer.» منزاحة][l1-composer_ar_mobile_light] | [`auto` → `rtl` مع نص عربي][l4-composer_ar_mobile_light] | مُصلح (الحقل الفارغ يبقى LTR — تجميلي) |
| B-13 الكود | [مقلوب][l1-chat_md_ar_desktop_light] | [LTR مقروء، والعربي داخله صحيح][l4-chat_md_ar_desktop_light] | مُصلح |
| B-10 ARIA الدخول | «Toggle theme / Toggle high contrast / Show secret» | «تبديل المظهر / تبديل التباين العالي / إظهار القيمة السرية» | مُصلح (فحص DOM) |

## 7. القرارات والخطوات التالية

| البند | المالك | ملاحظة |
|---|---|---|
| مراجعة لغوية للمسرد | المالك أو مراجع يحدده | الحالة الآن Proposed |
| تقديم الإصلاحات والترجمات upstream (PR + Locize) | **موافقة المالك** (إجراء خارجي باسم حساب GitHub/Locize) | الحزمة جاهزة في §5 |
| تطبيق قبل وصولها upstream | المالك (2026-10-20، #89) | **معتمد:** [ADR-0013](../../architecture/adr/0013-arabic-web-client-build.md) — upstream يتراجع (18.7% في `main`)؛ يشمل B-04 وB-06 وB-07 وB-10 وB-11 وB-12 وB-13 وB-17 |
| فحص من الجوال على Railway `dev` | المالك | الترحيب والمُدخل والإعدادات بالعربية — لتأكيد ما سبق على الهدف |
| قارئ الشاشة (NVDA/VoiceOver) | لاحقاً (#45) | NOT RUN |

<!-- لقطات الشاشة: روابط دائمة إلى commit 86d6546 (reference-style لإبقاء الصفوف قصيرة) -->
[l1-chat_md_ar_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/chat_md_ar_desktop_light.png
[l1-chat_md_en_desktop_dark]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/chat_md_en_desktop_dark.png
[l1-composer_ar_mobile_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/composer_ar_mobile_light.png
[l1-drawer_ar_mobile_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/drawer_ar_mobile_light.png
[l1-focus_login_ar_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/focus_login_ar_desktop_light.png
[l1-landing_ar_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/landing_ar_desktop_light.png
[l1-landing_en_desktop_dark]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/landing_en_desktop_dark.png
[l1-settings_ar_desktop_dark]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/v0.8.8-l1/settings_ar_desktop_dark.png
[l4-chat_md_ar_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/l4-validation/chat_md_ar_desktop_light.png
[l4-composer_ar_mobile_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/l4-validation/composer_ar_mobile_light.png
[l4-landing_ar_desktop_light]: https://github.com/faenazi/ef-ai-workspace/blob/86d6546cd0af712a537ec614532cd8dcd4e491e6/docs/design/screens/l4-validation/landing_ar_desktop_light.png
