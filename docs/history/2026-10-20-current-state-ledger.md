# الحالة الحالية المتحقق منها (Current Verified State)

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس حالة حالية ولا سياسة.** الحالة الحية: [project/CURRENT_STATE.md](../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](README.md).

| الحقل | القيمة |
|---|---|
| آخر تحقق | 2026-10-19 (21:55Z) — `main@6ffb954` (PR [#73](https://github.com/faenazi/ef-ai-workspace/pull/73)، ADR-0012): librechat `afccdaa6` **SUCCESS** على Railway `dev` — R-01–R-04 **Remediated** (`Verified (target environment)`)، R-05 غير متأثرة؛ mongodb `SKIPPED`. قبلها `main@86d6546`: Railway `dev` **Verified (target environment)** بعد #39 و#43 الجزء A (librechat `f30b263f` ثم `82465ffe` و`5389d1d2` SUCCESS، `config apply` لمتغيرين، سجل الإقلاع يُظهر السياسة والإعداد)؛ `mock_chat.py` **38/38** على `904d797`، محاكاة Railway 31/31 (+2 IPv6 SKIP)، اختبارات سلبية 18/18 — `Tested (cloud session)`. سابقاً `main@ad687c8`: `run-all.sh` 51/51 (ADR-0011، اختياري)؛ تفاصيل الأيام السابقة في §1 وسجل #15 |
| المرحلة الحالية | **Product R0.2 AI Activation NEXT** (غير منفّذ؛ قرار LLM #5 مفتوح)، بالتوازي مع **M1.1 closure**: Railway `dev` منشور، بعض RW غير منفذة، Windows/Ubuntu target (#17) غير متحقق. [Roadmap](planning-2026-10-19/PRODUCT_ROADMAP.md) · [Delivery Plan](planning-2026-10-19/DELIVERY_PLAN.md). |
| الفرع | **`main`:** `86d6546` (PR [#70](https://github.com/faenazi/ef-ai-workspace/pull/70) #44)؛ قبله `6dddb67` (PR [#69](https://github.com/faenazi/ef-ai-workspace/pull/69) #43 الجزء A) و`e147738` (PR [#68](https://github.com/faenazi/ef-ai-workspace/pull/68) #39) و`b30a86e` (PR #67) و`ad687c8` (PR #66 #42). آخر نشر Railway لصورة librechat: `5389d1d2` (`6dddb67`)؛ `86d6546` توثيق فقط `SKIPPED`. [PR #19](https://github.com/faenazi/ef-ai-workspace/pull/19) أُغلق دون دمج؛ ترقية مضبوطة [#62](https://github.com/faenazi/ef-ai-workspace/issues/62). افحص HEAD الحالي دائمًا. |
| المراحل السابقة | **M0 مكتملة**: PR [#9](https://github.com/faenazi/ef-ai-workspace/pull/9) (`0eab526`)؛ **M1 مكتملة**: PR [#12](https://github.com/faenazi/ef-ai-workspace/pull/12) دُمج 2026-10-18 (`0db80d9`)؛ **M1.1 المرحلة أ**: PR #18 دُمج 2026-10-18 (`bccd408`) |
| الاستضافة | Railway (عرض سحابي، **بيانات اصطناعية فقط**) + Windows 11 (**Ubuntu WSL2 + Docker Engine** مفضّل) + Ubuntu في الموقع. **Coolify مُستبدل** (ADR-0004 → Superseded؛ #6 و#13 مغلقان). **D1–D4 وسياسة SC-18 (D5) معتمدة، وD2 معدّل (لا GitHub Actions؛ النشر الآلي لمدخلات الصور من `main` وفق ADR-0010 (حل محل النشر اليدوي فقط))** في [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) (2026-10-18) — اعتماد معماري/سياسات فقط |
| التطبيق | LibreChat v0.8.8 + MongoDB 8.0.34 **منشوران في Railway `dev`** على `https://librechat-dev-3477.up.railway.app`؛ آخر Deploy تلقائي موثق لهما من `main@60b93e0` و`SUCCESS` (librechat `860d2369`، mongodb `5aa3c7f3`)؛ ليس هذا تحققًا جديدًا من الرابط اليوم. حساب المسؤول المحلي `fahad` (owner-reported)، التسجيل مغلق؛ **لا مزوّد نماذج** ولا Entra ID، Windows/Ubuntu الفعليان NOT RUN. |
| اسم العمل | اختار المالك «بصير» في 2026-10-19 اسماً مؤقتاً قابلاً للتغيير (`PROVISIONAL`). `APP_TITLE=بصير \| صندوق البيئة` في `librechat.env` و`railway.ts` (PR #27). **مطبّق على Railway `dev`** (2026-10-19T10:19Z): القيمة مطابقة بايتاً ببايت، librechat `8a434473` `SUCCESS` — `Verified (target environment)` ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6264988990)). **ظهوره في عنوان التبويب على الرابط العام: owner-check معلّق** (الجلسة لا تصل `*.up.railway.app`)؛ مُختبر محلياً AR/EN × جوال/سطح مكتب. لا يظهر في متن صفحة الدخول ولا يغيّر الشعار أو اسم PWA ([design-system.md §4](../design/design-system.md#4-آليات-التطبيق-في-librechat)). اعتماد الاسم والهوية المؤسسية مفتوح ([#7](https://github.com/faenazi/ef-ai-workspace/issues/7)) |
| النشر على Railway | **تلقائي من `main`** بقرار المالك 2026-10-19 ([ADR-0010](../architecture/adr/0010-railway-dev-autodeploy-from-main.md)): مصدر GitHub `faenazi/ef-ai-workspace` فرع `main`، Wait for CI مُطفأ، watch paths = مدخلات صورة كل خدمة؛ المتغيرات بـ `config apply`. **مُفعّل على Railway `dev`** (2026-10-19T10:33Z، `Verified (target environment)`): المصدر والفرع وwatch paths ظاهرة في `railway status`، وأول نشر تلقائي من GitHub لـ `60b93e0` نجح للخدمتين (librechat `860d2369`، mongodb `5aa3c7f3`) — [#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6265230900). **Verified (target environment) لدمج توثيقي PR #30**: الخدمتان `SKIPPED` ولم يحدث restart ([الدليل](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6265302353)). أثر PR #61 على لوحة Railway لم يُعد فحصه |

> قاعدة هذه الوثيقة: كل ادعاء إنجاز مرفق بدليل. الوثائق الموجودة ≠ وظائف تعمل.
> مستويات الأدلة: `Tested (cloud session)` = نفّذه الوكيل في السحابة (غير مستقل) · `Verified (GitHub CI)` = GitHub Actions (**غير مستخدم**، D2 المعدّل) ·
> `Verified (target environment)` = في Railway/Windows/Ubuntu الحقيقي.

> **سياسة الجودة الحالية ([ADR-0011](../architecture/adr/0011-production-only-quality-gates.md)، 2026-10-19):** لا بوابة جودة
> رسمية إلزامية في التطوير/الاختبار/العرض؛ تحقق مناسب للمهمة. البوابات الرسمية قبل الإنتاج فقط. الضوابط الأمنية وSC-18 دون تغيير.

## 0. اعتماد خارطة المنتج وتسلسل التنفيذ (2026-10-19)

**تم اعتماد التخطيط فقط، لا وظائف المنصة:** [خارطة المنتج R0.1–R1.0](planning-2026-10-19/PRODUCT_ROADMAP.md)،
[خطة R0.2/R0.3](planning-2026-10-19/DELIVERY_PLAN.md)، [ربط GitHub Issues](planning-2026-10-19/ISSUE_MAP.md)،
[دليل أي جلسة جديدة](../../project/START_HERE.md)،
[حوكمة التسليم](planning-2026-10-19/delivery-governance.md).
**6 Epics + 22 execution Issues (#31–#58)** منشأة؛ العمل الأصلي #5/#7/#15/#16/#17 محفوظ ومربوط؛
إنشاء **native GitHub Projects/Milestones ليس منجزاً** وتُتابعه [#59](https://github.com/faenazi/ef-ai-workspace/issues/59).

| بُعد | الحقيقة |
|---|---|
| أساس R0.1 | منصة Railway `dev` تعمل ببيانات اصطناعية، مسؤول `fahad` محلي؛ إغلاق RW/Windows/Ubuntu/backup/limits معلق |
| R0.2 | **In progress:** اختبار انحدار المحادثة بنموذج وهمي [#38](https://github.com/faenazi/ef-ai-workspace/issues/38) منفّذ ومختبر (cloud session)؛ الإعدادات الآمنة [#39](https://github.com/faenazi/ef-ai-workspace/issues/39) (أدوات مغلقة للدورين، فشل مزوّد سريع بلا نص المزوّد) **Tested (cloud session)** — القيم الخاصة بالمزوّد الحي معلقة على #37؛ **لا provider حي ولا محادثات LLM حقيقية**؛ قرار [#5](https://github.com/faenazi/ef-ai-workspace/issues/5) مطلوب |
| R0.3 | تدقيق الأسطح [#42](https://github.com/faenazi/ef-ai-workspace/issues/42) منجز؛ #43 الجزء A (إخفاء تذييل/مساعدة/إصدار upstream) **منشور على Railway `dev`**؛ تدقيق [#44](https://github.com/faenazi/ef-ai-workspace/issues/44) RTL/الترجمة/الوصول منجز ([التقرير](../design/audits/arabic-rtl-audit.md)، [المسرد](../design/arabic-glossary.md)) — العيوب تتطلب upstream (L4)، الإصلاحات مُختبرة محلياً فقط؛ الاسم مؤقت؛ أصول الهوية الرسمية [#7](https://github.com/faenazi/ef-ai-workspace/issues/7) غير متاحة |
| الاختبارات هنا | **توثيق وخطة GitHub فقط**؛ لا يدّعي هذا التحديث تنفيذ `run-all.sh` أو اختبار Railway أو تفعيل LLM |
| النشر | ADR-0010 يتيح autodeploy `dev` عند watched image-input changes؛ ملفات خطة `docs/` و`project/` ليست من مدخلات صور Docker |

## 0.1 تدقيق الإغلاق المستقل عن منفذ المراحل — 2026-10-19

[تقرير تدقيق M0/M1/M1.1/R0.1](reports/2026-10-19-foundation-closure-audit.md) راجع أدلة التسليم وGitHub
وشجرة التهيئة دون تشغيل الحاويات. **M0 وM1 مكتملتان حسب نطاقهما الأصلي واختبارات cloud-session التاريخية**؛
**M1.1 Phase A مدمجة، Phase B لا تُغلق** حتى تحقق #15/#17؛ **R0.1 Foundation Delivered لكن Gate OPEN**.
فحص remote static: 58 ملفات Markdown و319 مسار رابط نسبي بدون فقد، 17 FR/21 NFR، 10 ADR،
50 ملفاً إلزامياً، صور Compose/Railway بنفس digests، لا مشاكل بنيوية مكتشفة.
**NOT RUN:** `run-all.sh` الفعلي على [PR #61](https://github.com/faenazi/ef-ai-workspace/pull/61)،
Docker/Trivy/target healthchecks؛ [#60](https://github.com/faenazi/ef-ai-workspace/issues/60) **Superseded بـ ADR-0011** (§0.2) — ما لم يُشغَّل يبقى NOT RUN.
GitHub rulesets API أعاد `[]`؛ **حماية `main` غير متحققة** ([#3](https://github.com/faenazi/ef-ai-workspace/issues/3)).
[#62](https://github.com/faenazi/ef-ai-workspace/issues/62) يتابع ترقية MongoDB المنضبطة بعد إغلاق PR #19 دون دمج.

## 0.2 قرار المالك: بوابات الجودة الرسمية للإنتاج فقط — 2026-10-19

| بُعد | الحقيقة |
|---|---|
| القرار | تعليمات المالك المكتوبة (2026-10-19) → [ADR-0011](../architecture/adr/0011-production-only-quality-gates.md) **Accepted**؛ يعدّل شرط الدمج في ADR-0009 ونتيجة «بوابة الجودة قبل النشر» في ADR-0010 |
| ما أُلغي في التطوير | بوابة الجودة اليدوية لكل PR (D2 المعدّل): `run-all.sh` الكامل، الـ smoke/فحص الصور لتغييرات التوثيق، جداول NOT RUN الشاملة، المراجعة الرسمية لكل PR |
| ما بقي | تحقق مناسب للمهمة، صدق الأدلة، الأسرار، البيانات الاصطناعية، SC-18، التعريض العام والإنفاق واعتماد الإنتاج بيد المالك؛ لا حذف أو تعطيل لأي فحص/workflow |
| الإنتاج | بوابات جودة رسمية + مراجعة مستقلة + اعتمادات قبل أي go-live ([DoD §2](../quality/definition-of-done.md#2-الإنتاج--بوابات-الجودة-الرسمية-planned-قبل-أي-go-live)، [#58](https://github.com/faenazi/ef-ai-workspace/issues/58)) |
| [#60](https://github.com/faenazi/ef-ai-workspace/issues/60) | **Closed — Not planned / Superseded** (2026-10-19، بعد دمج PR #64)؛ `run-all.sh` على PR #61/#63 يبقى **NOT RUN** تاريخياً (ليس PASS) |
| حماية `main` ([#3](https://github.com/faenazi/ef-ai-workspace/issues/3)) | 2026-10-19: `GET /rulesets` و`/rules/branches/main` = `[]` (لا قواعد فعّالة)؛ `GET /branches/main/protection` = 403 للتكامل؛ محاولة إنشاء ruleset من الجلسة **رُفضت** (البروكسي لا يسمح بالكتابة على هذا المسار) → **إجراء مالك**، الإعدادات المطلوبة في #3 |

## 1. ما تم التحقق منه

| البند | الحالة | الدليل |
|---|---|---|
| M0: أساس المستودع والحوكمة | **Merged** | PR #9، [تقرير M0](reports/M0-delivery-report.md) |
| M1: حزمة LibreChat + MongoDB الآمنة افتراضياً | **Merged** (تحت CI-EX-02، الآن **Expired**) | PR #12، [تقرير M1](reports/M1-delivery-report.md) |
| M1.1 المرحلة أ: استضافة متعددة البيئات (ADR-0008) وتنفيذ قرارات #16 | **Merged** (`bccd408`)، تحت بوابة الجودة اليدوية (D2 المعدّل)، ليس CI مستقلاً | PR #18، [تقرير M1.1](reports/M1.1-hosting-transformation-report.md) |
| Compose — Windows profile (loopback): 37 فحصاً | **Tested (cloud session)** | `tests/smoke/compose-stack.sh local` — [تقرير M1.1 §3.1](reports/M1.1-hosting-transformation-report.md#31-compose--windows-profile-testssmokecompose-stacksh-local--pass-3737) |
| Compose — Ubuntu on-prem مع Caddy HTTPS: 43 فحصاً | **Tested (cloud session)** | `compose-stack.sh onprem` — §3.2 |
| Railway IaC: تقييم offline + type-check + سياسة (DB خاص، أسرار `preserve()`، volume واحد، digest مطابق) | **Tested (cloud session)** | `railway_checks.py` — §3.5 |
| صور Railway وقيوده (volume واحد مملوك لـ root، لا bind mounts، `*.railway.internal`، non-root، إعادة نشر، نسخة استرداد مشفّرة للأسرار واستعادة بنفس المفاتيح، كشف انحراف المفاتيح، خدمة الصور بالمصادقة) | **Tested (cloud session)** — 30/30، **IPv6 NOT RUN** (2 SKIP) | `railway-emulation.sh` — [تقرير M1.1 §3.3](reports/M1.1-hosting-transformation-report.md) |
| مساعد Windows PowerShell | **Tested (cloud session)** على Linux/pwsh 7.6.7 — 10/10 | `windows-helper.sh` — §3.4 |
| الفحوصات تكتشف الإعدادات الضعيفة (اختبار سلبي) | **Tested (cloud session)** — آلي: 17/17 حالة مرفوضة (مصدر نشر غير معتمد، watch paths ناقصة، انحراف D3، تعريض القاعدة، نطاق عام، أسرار، Compose) | `tests/policy/negative-checks.sh` — [تقرير M1.1 §9](reports/M1.1-hosting-transformation-report.md) |
| مسار نشر Railway اليدوي (طوارئ/رجوع بعد ADR-0010؛ `railway-deploy.sh`) | **Tested (cloud session)** بـ CLI وهمي — 8/8 | `tests/smoke/railway-manual-deploy.sh` — [railway.md §4](../operations/railway.md#4-النشر--تلقائي-من-main-adr-0010) |
| **R0.2 [#38](https://github.com/faenazi/ef-ai-workspace/issues/38): انحدار المحادثة بنموذج وهمي حتمي** (`tests/integration/mock_chat.py`، PR [#65](https://github.com/faenazi/ef-ai-workspace/pull/65)) — حزمة Compose الحقيقية + نموذج OpenAI-compatible وهمي على شبكة `backend` الداخلية: التسجيل مغلق، دخول مستخدمَين، اختيار النموذج، ردود متدفقة AR/EN حرفية، الحتمية، السجل، الحفظ وإعادة الفتح بعد إعادة التشغيل، الإيقاف، خطأ المزوّد/الشبكة، العزل، لا أسرار | **Tested (cloud session)** 2026-10-19 — **21/21** على `f4a21fb` (Docker 29.8.2، Compose 5.6.0)؛ اختبار طفرة: 5 فحوصات تفشل كما يجب. **نموذج وهمي فقط — لا مزوّد حي ولا Railway** | [#38](https://github.com/faenazi/ef-ai-workspace/issues/38) |
| **R0.3 [#44](https://github.com/faenazi/ef-ai-workspace/issues/44): تدقيق العربية وRTL والوصول** ([التقرير](../design/audits/arabic-rtl-audit.md)، [المسرد](../design/arabic-glossary.md)) — 70 لقطة AR/EN × جوال/سطح مكتب × فاتح/داكن + axe-core 4.10.3، مصفوفة القبول §6 معبأة، 13 عيباً بسببها الجذري في upstream (B-04 التحية بحروف منفصلة حتى في الإنجليزية، B-07 المُدخل LTR، B-13 الكود RTL، B-17 الإعدادات غير معكوسة، ARIA إنجليزية)؛ 158 ترجمة مقترحة | **Tested (cloud session)** 2026-10-19 — axe: 22/24 شاشة بلا مخالفة (B-16 تباين كود داكن)؛ `mock_chat.py` 38/38 (M38). **إصلاحات L4 (21 سطراً + الترجمات) مُختبرة في بناء محلي قبل/بعد فقط — غير منشورة**؛ قارئ الشاشة وRailway NOT RUN؛ تقديمها upstream ينتظر موافقة المالك | [#44](https://github.com/faenazi/ef-ai-workspace/issues/44) |
| **R0.3 [#43](https://github.com/faenazi/ef-ai-workspace/issues/43) الجزء A: إخفاء علامة upstream بإعداد L1** — `CUSTOM_FOOTER=` فارغ، `HELP_AND_FAQ_URL=/`، `interface.buildInfo: false` ([المصفوفة §11](../design/audits/brand-implementation-matrix.md#11-المطبّق-بإعداد-l1--43-الجزء-a-2026-10-19)) | **Tested (cloud session)** 2026-10-19 — `mock_chat.py` M37 (لا `buildInfo` حتى لغير المسجلين، لا رابط librechat.ai)، لقطات AR/EN × جوال/سطح مكتب بلا تذييل أو «Help & FAQ» أو «حول»، `compose_checks`/`railway_checks` PASS، اختبارات سلبية 18/18. **Railway `dev` Verified (target environment)**: نشر `82465ffe`، `config apply` (`CUSTOM_FOOTER=''`، `HELP_AND_FAQ_URL=/`)، إعادة نشر `5389d1d2`/`8fa4a337` SUCCESS، السجل `"buildInfo": false` ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6277008799))؛ الفحص البصري للرابط العام NOT RUN؛ الهوية الرسمية (الجزء B) محجوبة على #7 | [#43](https://github.com/faenazi/ef-ai-workspace/issues/43) |
| **R0.2 [#39](https://github.com/faenazi/ef-ai-workspace/issues/39): إعدادات ذكاء اصطناعي آمنة افتراضياً** ([ai-safe-defaults.md](../architecture/ai-safe-defaults.md)) — `librechat.yaml`: `interface` بصيغة الكائن للدورين USER وADMIN (الوكلاء/المنشئ/الأفعال، MCP، Skills، الذاكرة، البحث، تشغيل الكود، مفاتيح API، المشاركة، الجدولة مغلقة؛ Prompts دون مشاركة)، `endpoints.agents`: `capabilities: []`، `disableBuilder`، `maxProviderErrorChars: 0`؛ قيم إعادة المحاولة/المهلة لكل endpoint (الوهمي `maxRetries: 1`، `timeout: 8000`) | **Tested (cloud session)** 2026-10-19 — `mock_chat.py` **36/36** (M22–M36 جديدة): 403 لـ USER وADMIN على المسارات المحمية، المحادثة العادية تعمل (API وواجهة AR/EN)، أدوات مُصطنعة تُسقط، 503 → 1.1 ث (محاولتان)، 429/401/404 → 0.1 ث، مهلة → 18 ث، «إيقاف» أثناء إعادة المحاولة 0.6 ث دون طلبات لاحقة، لا نص مزوّد (canary)، الملف يُعاد تطبيقه بعد إعادة التشغيل؛ طفرة بلا السياسة: 8 فحوصات تفشل. قيد upstream: علم Artifacts لا يُفحص في الخادم. **Railway `dev` Verified (target environment)**: librechat `f30b263f` SUCCESS وسجل الإقلاع: الإعداد محمّل و45 تحديث صلاحية (USER 15، ADMIN 30) ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6275132663))؛ فحوص 403 عبر الرابط العام NOT RUN؛ حدود المعدل وقيم المزوّد الحي قرار المالك (#5/#37) | [#39](https://github.com/faenazi/ef-ai-workspace/issues/39) |
| **R0.3 [#42](https://github.com/faenazi/ef-ai-workspace/issues/42): تدقيق أسطح الهوية في LibreChat v0.8.8** — [مصفوفة تطبيق الهوية](../design/audits/brand-implementation-matrix.md): 14 سطحاً مصنّفة L1–L5 (ADR-0006) بالمصدر وخطر الترقية ومعايير القبول؛ تغطية العربية **22.6%** (692/3059 مفتاحاً)؛ لا سطح يُلزم بـ fork؛ 12 فجوة تحتاج upstream PR؛ خط أساس بصري 12 لقطة (دخول/ترحيب/محادثة × AR/EN × جوال/سطح مكتب) | **Analysis + baseline `Tested (cloud session)`** 2026-10-19 (محلي، upstream كما هو، Playwright 1.56.1)؛ عيوب مرصودة B-04..B-08 (مثل كسر وصل الحروف العربية في تحية الترحيب)؛ **لا هوية مطبّقة**، فحوص القبول §6 NOT RUN، الهوية الرسمية #7 مفتوحة | [#42](https://github.com/faenazi/ef-ai-workspace/issues/42) |
| فحص ثغرات الصور + سجل الثغرات | **السياسة SC-18 Approved**؛ التنفيذ Implemented (report-only)؛ الصور الأساسية والمشتقة مفحوصة 2026-10-18؛ فحص جديد 2026-10-19 (نفس النتائج)؛ **منذ 2026-10-19 (21:55Z): R-01–R-04 Remediated على Railway `dev`** (ADR-0012)، **R-05 غير متأثرة** (قرار المالك)؛ لا قبول مؤقت سارٍ. صور Compose upstream ما زالت تحملها (غير معرّضة) | [vulnerability-register.md](../security/vulnerability-register.md) |
| **خطة معالجة الثغرات الحرجة قبل 2026-11-18** ([الخطة](../security/cve-remediation-plan.md)، [ADR-0012](../architecture/adr/0012-temporary-security-patch-layer.md) **Accepted** 2026-10-19؛ R-05 **غير متأثرة** بقرار المالك، [السجل §2.2](../security/vulnerability-register.md#22-تصنيف-r-05-cve-2025-68121-غير-متأثر--not-affected)) — upstream: R-01–R-03 مُصلحة في `main` لـ LibreChat فقط (غير مُصدَرة)، R-04 غير مُصلحة حتى في `main`، R-05 لن تُصلح (gosu 1.19، و`crypto/tls` غير مرتبطة في الملف) | **Tested (cloud session)** 2026-10-19 — فحص Trivy جديد (قاعدة 19:08Z): نفس النتائج؛ تجربة طبقة الترقيع في scratchpad فقط: **0 CRITICAL / 22 HIGH**، `mock_chat.py` 38/38، `railway-emulation.sh` 31/31 (+2 IPv6 SKIP). `govulncheck` نفسه NOT RUN (403). **التنفيذ (PR [#73](https://github.com/faenazi/ef-ai-workspace/pull/73)، `Tested (cloud session)`):** Trivy 0 CRITICAL / 22 HIGH على بناء الـ Dockerfile نفسه، حارس الخروج يُفشل البناء على قاعدة مُرقّعة، `mock_chat.py` 38/38، محاكاة Railway 30/31 (R02 أثر إعداد الاختبار؛ نجح على الفرع)، `railway_checks`/`compose_checks` PASS، سلبية 18/18. **Railway `dev` Verified (target environment):** librechat `afccdaa6` SUCCESS 21:55Z؛ سجل البناء: sha256 `OK` للحزم الثلاث و`changed 34 packages`؛ سجل الإقلاع: "Server listening"، "No changes needed" للدورين، `buildInfo: false` ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15)) | [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) |
| إعداد Railway من طرف المالك: 2FA، حد إنفاق $15/$30، مشروع `ef-ai-workspace` فارغ، بيئة `dev` فارغة، project token لـ `dev` فقط في إعدادات بيئة السحابة | **Done (owner-reported)**؛ حد الإنفاق **NOT VERIFIED** من وكيل | [#15 تعليق](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6255701285) |
| `railway config plan` الأول (قراءة فقط، CLI 5.70.0 من مصدر crates.io بـ `--locked`) على `9aa1437` | **Tested (cloud session)** 2026-10-18 — `4 to add, 0 to change, 0 to destroy` (خدمتان `empty` بلا مصدر + volumeان 5000 MB، لا نطاق ولا TCP proxy، الأسرار `preserve` فقط، 0 diagnostics) | [#15 تعليق](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6256063097) |
| `railway config apply` في `dev` (بتفويض المالك على #15، 2026-10-19T06:21Z) | **Verified (target environment)** 2026-10-19: 4 موارد أُنشئت؛ الخدمتان **بلا مصدر** ولا نطاق (`railway status`)؛ volumeان 5000 MB READY. فرق شكلي باقٍ: `restartPolicy` الافتراضي يظهر `null` | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| الأسرار السبعة في Railway (`railway-secrets.sh --accept-no-recovery`، غير مختومة) | **Verified (target environment)** — طُبعت الأسماء فقط | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| النشر اليدوي لـ `bd98194`: mongodb | **Verified (target environment)** — `SUCCESS`؛ يصادق LibreChat عبر الشبكة الخاصة | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| النشر اليدوي لـ `bd98194`: librechat | **FAILED** (healthcheck): `DOMAIN_CLIENT` = `https://` دون نطاق عام → `Invalid URL`؛ أُصلح في PR [#22](https://github.com/faenazi/ef-ai-workspace/pull/22) | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| النشر اليدوي لـ `a9fcacf` (PR #22): librechat | **Verified (target environment)** 2026-10-19 — `SUCCESS`، healthcheck `/health` ناجح؛ يعمل على العنوان الخاص | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| Railway AD01/AD02 (ADR-0010) | **Verified (target environment) سابقاً**: `main@60b93e0` أعاد نشر الصورتين تلقائياً، و`main@62d736c` لتوثيق فقط `SKIPPED` للخدمتين | [#15 auto](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6265230900) · [#15 skip](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6265302353) |
| Railway RW1/RW3/RW4/RW10/RW11/RW13 | **Verified سابقاً على target** وفق دليل #15 (النشر والصحة، DB خاص، سجلات وsecret sampling، انتشار سياسة) | [#15 — مصفوفة القبول المحدثة](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| الرابط العام `https://librechat-dev-3477.up.railway.app` (بقبول SC-18 المؤقت) وأول مسؤول | **Configured** 2026-10-19: النطاق مُولّد، `DOMAIN_*` أخذت النطاق تلقائياً؛ التسجيل فُتح مؤقتاً (~06:58–07:36Z) فأنشأ المالك حسابه المحلي `fahad` (أول مستخدم = ADMIN في مصدر v0.8.8 `AuthService.js`)، ثم أُغلق بـ `config apply` (`ALLOW_REGISTRATION=false`)؛ الدخول من الجوال owner-reported | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| RW13 — انتشار تغيير السياسة (plan → apply → redeploy) بتغيير `APP_TITLE` | **Verified (target environment)** 2026-10-19: plan `0/3/0` → apply → librechat `8a434473` وmongodb `a31b020e` `SUCCESS` → plan بعده: الفرق الشكلي فقط | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15#issuecomment-6264988990) |
| RW2/RW5/RW6 الجزئي/RW7–RW9/RW12 + backups وحد الإنفاق | **NOT RUN أو PARTIAL** على Railway target؛ سجل #15 يحدد الدليل/المانع بدقة؛ RW14 التاريخي **SUPERSEDED** بـ ADR-0010 | [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) |
| Windows 11 حقيقي / خادم Ubuntu حقيقي | **NOT RUN** | [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) |
| GitHub CI | **غير مستخدم** بقرار المالك (D2 المعدّل)؛ لم يُشغَّل قط للمشروع — لا ادعاء `Verified (GitHub CI)`؛ [#10](https://github.com/faenazi/ef-ai-workspace/issues/10) مغلق Not Planned | [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) |
| توافق Codex | Configured — غير مختبر | #8 |

## 2. قيد التنفيذ

اسم العمل «بصير» (PR [#27](https://github.com/faenazi/ef-ai-workspace/pull/27)) مدموج ومطبّق على Railway `dev`؛ بقي تأكيد المالك لعنوان التبويب على الرابط العام. العمل التالي ينتظر قرار المالك في OD-01 (§5).

قرارات [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) (اعتماد سياسات):

| القرار | المعتمد | الحالة في المستودع |
|---|---|---|
| D1 | ADR-0008 (Railway اصطناعي + Windows WSL2/Engine + Ubuntu)؛ Coolify مُستبدل | ADR-0008 **Accepted** (اعتماد معماري فقط) |
| D2 (معدّل) | **GitHub Actions غير مطلوب**؛ ~~بوابة جودة يدوية على SHA النهائي لكل PR~~ → **تحقق مناسب للمهمة في التطوير، وبوابات رسمية قبل الإنتاج فقط** ([ADR-0011](../architecture/adr/0011-production-only-quality-gates.md)، 2026-10-19)؛ Railway لا ينتظر CI؛ ~~نشره يدوي فقط~~ → **تلقائي من `main`** ([ADR-0010](../architecture/adr/0010-railway-dev-autodeploy-from-main.md)، 2026-10-19)؛ حماية `main` لمطوّر منفرد دون فحوصات إلزامية (#3) | DoD مُعاد كتابته؛ CI-EX-03 = **Superseded / Not applicable (لم يُعتمد)**؛ `railway.ts`: مصدر GitHub `main` دون Wait for CI وwatch paths (ADR-0010)؛ `railway-deploy.sh` للطوارئ + اختبار D01–D08؛ اختبارات سلبية N01–N17 |
| D3 | EU West، نسخة واحدة، 2 vCPU/2 GB و1 vCPU/1 GB، 5 GB/volume، MongoDB خاص، Daily+Weekly، نشر dev من `main` (الأصل يدوياً، استُبدل وفق ADR-0010)؛ إنفاق $30 hard / $15 alert | مفروض في `railway.ts`/`railway_checks.py` و**مُطبّق في `dev`** (2026-10-19)؛ Backups وحد الإنفاق **NOT VERIFIED** (لوحة المالك) |
| D4 | Ubuntu WSL2 + Docker Engine مفضّل؛ Docker Desktop بترخيص مُتحقق فقط | `windows-local.md` مُحدّث؛ تشغيل Windows حقيقي **NOT RUN** (#17) |
| D5 | سياسة SC-18 **Approved**؛ الثغرات الحرجة الخمس: قبول مؤقت (2026-10-19) **حلّت محله** المعالجة (R-01–R-04، ADR-0012) والتصنيف «غير متأثر» (R-05) | الرابط العام لـ `dev` قائم على المعالجة لا على القبول المؤقت؛ فحص أسبوعي |

- **مُفوَّض للوكيل ([ADR-0009](../architecture/adr/0009-development-phase-agent-delegation.md)، 2026-10-19؛ معدّل بـ [ADR-0011](../architecture/adr/0011-production-only-quality-gates.md)):** دمج PRs بعد مراجعة ذاتية وتحقق مناسب للمهمة، و`apply`/الأسرار/النشر في Railway `dev`. **يبقى للمالك:** أي نطاق عام، بيئات أخرى، الإنفاق، DNS، البيانات الحقيقية، قبول مخاطر الثغرات الحرجة، الإنتاج.
- **تسجيل الدخول — توجّه مقترح (ليس قراراً معتمداً)، جلسة 2026-10-19:**
  - Railway `dev`: حسابات محلية فقط والتسجيل مغلق؛ أي حساب تجريبي إضافي بنافذة تسجيل قصيرة وبريد غير حقيقي.
  - المالك أفاد بوجود App Registration في **tenant الصندوق الحقيقي** (client ID/secret، وصلاحيات Graph واسعة لقراءة الدليل والمجموعات والهيكل التنظيمي). **غير مربوط** بـ Railway: قاعدة البيانات الاصطناعية (AGENTS.md القاعدة 2)، Railway خارج المملكة، ونطاق قبول SC-18 بيانات اصطناعية فقط. طلب المالك تجربة كل الموظفين بحساباتهم الحقيقية على Railway **لم يُنفّذ** لهذه الأسباب.
  - المسار المقترح: Entra ID للموظفين في بيئة تجريبية/إنتاجية **داخل المملكة** (#17، OD-05)، بصلاحيات أقل امتياز (تسجيل الدخول: `openid profile email`؛ البحث في الدليل والمجموعات فقط عند تفعيله)، ودور المسؤول من Entra App Role (`OPENID_ADMIN_ROLE`)، و1–2 حساب طوارئ محلي.
  - متحقق في مصدر v0.8.8: `OPENID_ADMIN_ROLE` يرقّي ويخفّض تلقائياً؛ الحساب المحلي بنفس بريد مستخدم Entra **يمنع** دخوله بـ Entra، لذا حسابات الطوارئ ببريد مختلف.
- **NOT VERIFIED:** حماية فرع `main` (#3)، Windows 11 حقيقي، خادم Ubuntu حقيقي، الشبكة الخاصة IPv6-only، حد إنفاق Railway.

## 3. العوائق والاعتماديات

| البند | يعيق | Issue |
|---|---|---|
| بيئة داخل المملكة + رأي حماية البيانات في الصندوق | دخول الموظفين الحقيقيين بـ Entra ID وأي بيانات حقيقية | [#17](https://github.com/faenazi/ef-ai-workspace/issues/17)، OD-05 |
| جهاز Windows 11 وخادم Ubuntu داخلي (DNS، شهادة CA) | التحقق في البيئة المستهدفة | [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) |
| حماية فرع `main` (PR إلزامي، منع force-push/الحذف، حل المحادثات؛ دون فحوصات إلزامية) | SC-04 | [#3](https://github.com/faenazi/ef-ai-workspace/issues/3) |
| مزوّدو النماذج المعتمدون (OD-01) — **الأولوية التالية** | تشغيل المحادثة (M3)، ثم RAG (M4) | [#5](https://github.com/faenazi/ef-ai-workspace/issues/5) |
| أصول الهوية (D-04) | M2 (الهوية الرسمية) | [#7](https://github.com/faenazi/ef-ai-workspace/issues/7) |

## 4. مشكلات معروفة / فجوات

- **Quality gate post-merge (تاريخي):** `run-all.sh` لم يُشغَّل على `main@e2b8cb1`/PR #63؛ المتطلب أُلغي بـ ADR-0011 و[#60](https://github.com/faenazi/ef-ai-workspace/issues/60) Superseded — النتيجة تبقى NOT RUN، لا PASS.
- **Branch rules:** GitHub API أعاد `[]` لـ rulesets وللقواعد الفعّالة على `main` (تحقق ثانٍ 2026-10-19)؛ إنشاء ruleset من الجلسة غير متاح (403 من البروكسي)؛ [#3](https://github.com/faenazi/ef-ai-workspace/issues/3) **P0 إجراء مالك** لأن مدخلات صور `main` تنشر إلى Railway dev تلقائياً.
- **Upgrade control:** [PR #19](https://github.com/faenazi/ef-ai-workspace/pull/19) أُغلق دون دمج؛ تحديث MongoDB في Compose فقط يكسر تطابق `mongodb.Dockerfile FROM`. خطة تحديث منضبطة [#62](https://github.com/faenazi/ef-ai-workspace/issues/62).


- Dependabot PR [#14](https://github.com/faenazi/ef-ai-workspace/pull/14) (mongo 8.0 → 9.0) **أُغلق دون دمج** (ترقية major خارج ADR-0007)؛ Dependabot صار يتجاهل major لـ MongoDB.
- Trivy: الصور upstream ما زالت تُظهر 5 CRITICAL (LibreChat 4، mongo 1)؛ على Railway `dev` R-01–R-04 مُعالجة بطبقة ADR-0012 المؤقتة (تُزال عند ترقية LibreChat؛ حارس البناء يفرض ذلك) وR-05 غير متأثرة. Compose المحلي/الداخلي بلا الطبقة.
- Railway خارج المملكة (لا منطقة في الشرق الأوسط): بيانات اصطناعية فقط؛ ليس مرشحاً للإنتاج (OD-05).
- Docker Desktop يتطلب اشتراكاً مدفوعاً للجهات الحكومية؛ المسار المعتمد Ubuntu WSL2 + Docker Engine (D4).
- لا مزوّد نماذج مُفعّل — الدخول يعمل على Railway (حساب `fahad`) والمحادثة غير ممكنة حتى M3. بحث المحادثات (M3) وRAG (M4) غير متاحين.
- upstream: ترجمة عربية جزئية، لا ألوان/شعار وقت التشغيل، سجل تدقيق محدود، Artifacts من CDN عام افتراضياً.
- النسخ الاحتياطي: جدولة Compose ووجهة التخزين المشفّرة غير محسومة (M6)؛ volume backups على Railway غير مُختبرة.
- سياسة شبكة جلسة السحابة تمنع `pkg-containers.githubusercontent.com` (طبقات صور ghcr) و`*.up.railway.app`: المحاكاة الكاملة وRW2 من الجلسة NOT RUN؛ الفحص الأمني يسحب الصور بنفس الـ digest من `mirror.gcr.io`. الحل: إضافة النطاقين إلى Allowed domains للبيئة.
- `railway config plan` يُظهر فرقاً شكلياً دائماً: `restartPolicy` (`ON_FAILURE`/10، افتراضي Railway) يعود `null` بعد كل apply.
- نافذة التسجيل المفتوحة (~06:58–07:36Z، 2026-10-19): لا يمكن من الجلسة التحقق من عدد المستخدمين (لا `railway ssh`)؛ يتحقق المالك من زر «إعدادات المسؤول» في قسم «الأوامر».

## 5. الأولوية التالية — Product R0.2

لا عائق جودة إداري قبل R0.2 (ADR-0011)؛ حماية `main` في [#3](https://github.com/faenazi/ef-ai-workspace/issues/3) إجراء أمني عاجل بيد المالك.

1. **المالك — [#5 OD-01](https://github.com/faenazi/ef-ai-workspace/issues/5):** اعتماد مزوّد LLM التجريبي ونماذجه/نطاق بياناته وملكيته وتكلفته؛ **لا ينفَّذ ربط حي في [#37](https://github.com/faenazi/ef-ai-workspace/issues/37) قبل القرار**.
2. ~~**[#38](https://github.com/faenazi/ef-ai-workspace/issues/38)** اختبارات mock للمحادثات~~ **منفّذ** (PR [#65](https://github.com/faenazi/ef-ai-workspace/pull/65)، 21/21 cloud session)؛ يُعاد تشغيله بعد ربط المزوّد الحي (#37) وأي ترقية لـ LibreChat.
3. ~~**[#42]**~~ و~~**[#44]**~~ و~~**#43 الجزء A**~~ **منجزة** (PR #66، [#70](https://github.com/faenazi/ef-ai-workspace/pull/70)، [#69](https://github.com/faenazi/ef-ai-workspace/pull/69))؛ متبقٍ لـ #44: مراجعة لغوية [للمسرد](../design/arabic-glossary.md) و**موافقة المالك على تقديم الإصلاحات upstream** ([التقرير §7](../design/audits/arabic-rtl-audit.md#7-القرارات-والخطوات-التالية))؛ الهوية الرسمية تنتظر [#7](https://github.com/faenazi/ef-ai-workspace/issues/7).
4. **R0.2 بعد القرار:** [#37](https://github.com/faenazi/ef-ai-workspace/issues/37) Provider (حزمة القرار في [#5](https://github.com/faenazi/ef-ai-workspace/issues/5#issuecomment-6277200347)) → إكمال [#39](https://github.com/faenazi/ef-ai-workspace/issues/39) (قيم المزوّد الحي فقط؛ الجزء المستقل منجز) →
   [#40](https://github.com/faenazi/ef-ai-workspace/issues/40) synthetic files review →
   [#41](https://github.com/faenazi/ef-ai-workspace/issues/41) gate.
5. **بوابات أمان وتشغيل بالتوازي:** [#15](https://github.com/faenazi/ef-ai-workspace/issues/15) Railway،
   [#3](https://github.com/faenazi/ef-ai-workspace/issues/3) branch rules،
   [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) فحص SC-18 أسبوعي ومتابعة إصدار LibreChat لإزالة طبقة ADR-0012 ([خطة المعالجة](../security/cve-remediation-plan.md))،
   [#17](https://github.com/faenazi/ef-ai-workspace/issues/17) target tests،
   [#59](https://github.com/faenazi/ef-ai-workspace/issues/59) Project/Milestones.
6. **التصميم المؤسسي:** لا ربط Entra tenant الحقيقي ولا بيانات الصندوق في Railway خارج السعودية؛ R1.0 يتطلب موافقة أمن واستضافة سعودية.
