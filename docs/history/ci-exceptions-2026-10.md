# بوابة الجودة اليدوية واستثناءات CI (2026-10) — سجل تاريخي

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ غير سارٍ.** المصدر: §4 من
> [تعريف الإنجاز](../quality/definition-of-done.md) عند `main@8f40476`. السياسة الحالية:
> [ADR-0011](../architecture/adr/0011-production-only-quality-gates.md) (لا بوابة جودة رسمية في التطوير).

## بوابة الجودة اليدوية لكل PR — D2 المعدّل (2026-10-18 → استُبدلت بـ ADR-0011 في 2026-10-19)

قرار المالك (2026-10-18): «ما احتاج Actions github» — بدلاً من GitHub Actions كان على الوكيل **لكل PR** وعلى **SHA الرأس النهائي**
تشغيل `scripts/validate/run-all.sh` (كل PR)، و`tests/smoke/compose-stack.sh local|onprem` (تغيّر البنية)، و`tests/smoke/railway-emulation.sh`
(تغيّر Railway/الصور/الأسرار)، و`tests/smoke/windows-helper.sh` (تغيّر `scripts/windows/` أو Compose؛ أُزيل لاحقاً بقرار المالك، #75)،
و`image-scan.sh --include-railway` (تغيّر digest)، وتسجيل `PASS/FAIL/SKIP/NOT RUN` بإصدارات الأدوات في الـ PR و`CURRENT_STATE.md`.
نتائج PRs التي طُبقت عليها (مثل #18، #25، #27) تبقى كما سُجّلت؛ وما لم يُشغَّل في PRs #61 و#63 يبقى **NOT RUN** ولا يصبح PASS
بإلغاء البوابة ([#60](https://github.com/faenazi/ef-ai-workspace/issues/60) أُغلقت Not planned / Superseded).

## استثناءات مؤقتة معتمدة من مالك المشروع

كانت هذه الاستثناءات تعفي PRs محددة من شرط GitHub CI الذي أُلغي بقرار D2 المعدّل؛ تُحفظ كما هي.
الاستثناء كان لا يُنشأ إلا بقرار صريح من مالك المشروع مسجّل في GitHub (Issue/PR)، بنطاق وتاريخ انتهاء،
ولم يكن يسمح أبداً بحذف أو تعطيل أو تخطي أي workflow أو فحص، ولا ينطبق على النشر، أو وسم إصدار، أو بوابات الإنتاج (M6/M8).

### CI-EX-01 — GitHub Actions غير متاح لمرحلة M0

| البند | القيمة |
|---|---|
| الحالة | **Expired** — انتهى بدمج PR #9 في 2026-10-17 (merge commit `0eab526`) |
| الاعتماد | قرار مالك المشروع (@faenazi) بتاريخ 2026-10-17، مسجّل في Issue [#10](https://github.com/faenazi/ef-ai-workspace/issues/10)؛ **التأكيد النهائي = موافقة المالك على PR #9 ودمجه** |
| السبب | ميزانية GitHub Actions في الحساب تمنع بدء الوظائف ("The job was not started because an Actions budget is preventing further use") |
| النطاق | PR [#9](https://github.com/faenazi/ef-ai-workspace/pull/9) فقط (M0: توثيق وإعدادات حوكمة، بلا كود قابل للنشر ولا بنية تحتية) |
| البديل المقبول | تشغيل **كل** الفحوصات المعرّفة في `ci.yml` و`security.yml` بنفس الإصدارات المثبتة في جلسة Claude Code Cloud على SHA رأس الـ PR، مع تسجيل الأوامر والنتائج في [تقرير M0](reports/M0-delivery-report.md#3-نتائج-التحقق-validation-results) وفي الـ PR |
| ما لا يغطيه | التحقق المستقل؛ سلوك GitHub الفعلي (تحليل workflows، الصلاحيات، الجدولة)؛ الفحوصات الإلزامية في حماية الفرع |
| الانتهاء | ينتهي عند دمج PR #9 أو إغلاقه. أي PR لاحق (M1 فما بعد) يتطلب CI أخضر على GitHub، أو اعتماداً **جديداً وصريحاً** من المالك لاستثناء جديد مُدرج هنا |
| شرط الإغلاق | عند استعادة GitHub Actions: تشغيل workflows على `main` وتسجيل النتيجة في `CURRENT_STATE.md`؛ أي فشل يُعالج كـ bug بأولوية عالية |

### CI-EX-02 — GitHub Actions غير متاح لمرحلة M1

| البند | القيمة |
|---|---|
| الحالة | **Expired** — انتهى بدمج PR #12 في 2026-10-18 (`0db80d9`). **لا يُمدَّد** |
| الاعتماد | قرار مالك المشروع (@faenazi) D2 بتاريخ 2026-10-18، مسجّل في Issue [#11](https://github.com/faenazi/ef-ai-workspace/issues/11) (مغلق Completed) — السجل القانوني للقرار |
| السبب | GitHub Actions ما زال غير متاح ([#10](https://github.com/faenazi/ef-ai-workspace/issues/10)): صفر تشغيلات لـ `CI`/`Security` على PR #12 |
| النطاق | PR [#12](https://github.com/faenazi/ef-ai-workspace/pull/12) (M1، Issue [#2](https://github.com/faenazi/ef-ai-workspace/issues/2)) **فقط** |
| البديل المقبول | `scripts/validate/run-all.sh` (يشمل `compose_checks.py`) + `tests/smoke/m1-stack.sh` (35 فحصاً) على SHA رأس الـ PR، مع تسجيل الأوامر والنتائج في [تقرير M1](reports/M1-delivery-report.md) — `Tested (cloud session)`، **ليس** تحققاً مستقلاً |
| ما لا يغطيه | التحقق المستقل؛ تعطيل أي workflow (ممنوع)؛ أي نشر (M1.1 #13 يتطلب تفويضاً منفصلاً)؛ وسم الإصدارات؛ الإنتاج؛ أي PR آخر |
| الانتهاء | فور دمج PR #12 أو إغلاقه؛ بعدها يعود شرط GitHub CI أخضر أو اعتماد جديد صريح |

### CI-EX-03 — GitHub Actions غير متاح لـ PR الاستضافة متعددة البيئات (ADR-0008)

| البند | القيمة |
|---|---|
| الحالة | **Superseded / Not applicable — لم يُعتمد قط.** لم يُعتمد في D2 الأول (2026-10-18: استعادة Actions)، ثم صار غير ذي صلة بقرار D2 المعدّل ([#16](https://github.com/faenazi/ef-ai-workspace/issues/16)، 2026-10-18: Actions غير مطلوب؛ بوابة الجودة اليدوية لكل PR، المستبدلة لاحقاً بـ ADR-0011). **لا يُعتمد بأثر رجعي**؛ النص سجل تاريخي فقط |
| السبب | بعد دمج PR #12 لم تُشغَّل أي workflows للمشروع (`CI`/`Security`) على `main` (`0db80d9`)؛ تشغيلات Dependabot فقط ([#10](https://github.com/faenazi/ef-ai-workspace/issues/10)) |
| النطاق المقترح | PR الاستضافة متعددة البيئات (M1.1، [#15](https://github.com/faenazi/ef-ai-workspace/issues/15)) **فقط** |
| البديل المقترح | `scripts/validate/run-all.sh` (يشمل `compose_checks.py` و`railway_checks.py`) + `tests/smoke/compose-stack.sh local` و`onprem` + `tests/smoke/railway-emulation.sh` + `tests/smoke/windows-helper.sh` على SHA رأس الـ PR، مسجّلة في [تقرير M1.1](reports/M1.1-hosting-transformation-report.md) — `Tested (cloud session)`، **ليس** تحققاً مستقلاً |
| ما لا يغطيه | التحقق المستقل؛ تعطيل أي workflow؛ أي `railway config apply` أو نشر (#15 يتطلب تفويضاً منفصلاً)؛ وسم الإصدارات؛ الإنتاج؛ أي PR آخر |
| البديل الموصى به | استعادة Actions (#10) وتشغيل `CI` و`Security` و`Smoke` و`Image scan` على الـ PR |
| الانتهاء (إن اعتُمد) | فور دمج ذلك الـ PR أو إغلاقه |
