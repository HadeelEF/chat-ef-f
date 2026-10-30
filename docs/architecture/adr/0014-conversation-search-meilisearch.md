# ADR-0014 — البحث في المحادثات: خدمة Meilisearch خاصة في كل بيئة

| Field | Value |
|---|---|
| Status | **Accepted** — تعليمات المالك 2026-10-21 («نفذ الدفعة الاولى»، [#125](https://github.com/faenazi/ef-ai-workspace/issues/125)) |
| Date | 2026-10-21 |
| Deciders | مالك المشروع (@faenazi) في جلسة Claude Code Cloud؛ اختيار الإصدار هندسي (الوكيل) |
| Related | OD-02 ([#4](https://github.com/faenazi/ef-ai-workspace/issues/4))؛ FR-003 AC-1/AC-2؛ ADR-0007 §4، ADR-0008، ADR-0010؛ SC-06، SC-18 |

## Context

- OD-02 أجّل Meilisearch إلى M3، فاستبعده ADR-0007 (§4) ونشر ADR-0008 خدمتين فقط على Railway. R0.2 (M3) جارٍ الآن.
- قرار المالك 2026-10-21: تفعيل الدفعة الأولى من مزايا LibreChat، ومنها البحث في المحادثات، بعد أن قيل له إنها خدمة إضافية على Railway.
- LibreChat v0.8.8 يبحث عبر Meilisearch فقط (`SEARCH=true` و`MEILI_HOST` و`MEILI_MASTER_KEY`)، ويعرض مربع البحث حين يراها سليمة.
- upstream v0.8.8 يثبّت `getmeili/meilisearch:v1.35.1` (2026-02). Trivy 0.76.0 في 2026-10-21: **2 CRITICAL و27 HIGH**.
- LibreChat يحفظ علامة «مُفهرس» (`_meiliIndex`) في MongoDB، لا في Meilisearch (`api/db/indexSync.js`). الفهرس الفارغ يُعاد بناؤه
  عند الإقلاع التالي (M55)، لكن بعد استعادة قاعدة البيانات قد تبقى محادثات مستعادة خارج الفهرس (M56).

## Decision

1. **خدمة ثالثة `meilisearch` في كل بيئة**، خاصة مثل MongoDB:
   - Compose: شبكة `backend` الداخلية فقط، بلا منفذ، `read_only`، `cap_drop: ALL`، وvolume `meilisearch-data`.
   - Railway `dev`: Dockerfile مشتق بحارس يرفض البدء دون المفتاح، ويستمع على IPv6. بلا نطاق، وvolume 5 GB، وحد 1 vCPU / 1 GB (حدود MongoDB نفسها).
2. **الإصدار `v1.54.3` بالـ digest** (آخر patch في 1.54، 2026-10-01): 0 CRITICAL و10 HIGH (كلها في curl). هذا انحراف مقصود عن pin
   upstream. واجهة البحث في 1.x مستقرة، ويثبتها `mock_chat.py` (M49–M56).
3. **مفتاح رئيسي لكل بيئة** (64 hex)، مع `MEILI_ENV=production` و`MEILI_NO_ANALYTICS=true`. على Railway يشير LibreChat إلى مفتاح
   خدمة `meilisearch` بمرجع `${{meilisearch.MEILI_MASTER_KEY}}`، لا بنسخة منه.
4. **الفهرس بيانات مشتقة** فلا يُنسخ احتياطياً. ضياع volume الخدمة يُصلحه إقلاع LibreChat التالي. بعد الاستعادة يمسح
   `scripts/operations/search-reindex.sh` علامات `_meiliIndex` كما يفعل upstream (`batchResetMeiliFlags`)، ثم يعيد تشغيل
   LibreChat فيفهرس كل شيء. `restore.sh` يشغّله تلقائياً.
5. **ما يتغيّر في القرارات السابقة:** «لا Meilisearch» في ADR-0007 §4، و«خدمتان» في ADR-0008 وADR-0010 صارت ثلاث خدمات. بقية
   القرارات الثلاثة كما هي، ومنها مصدر النشر وwatch paths ومساواة الـ digest.

## Rationale

- البحث (FR-003 AC-1) دون إخراج نص المحادثات من المنصة: Meilisearch هي الآلية الوحيدة المدعومة في v0.8.8، وتعمل داخل الشبكة الخاصة.
- الفلترة بالمستخدم (`user = "<id>"`) تتم في الخادم، فلا يرى الموظف إلا محادثاته (FR-003 AC-2؛ M51، M55).
- إصدار بلا CRITICAL أولى من مطابقة pin upstream حرفياً، ما دام المسار الذي يستخدمه LibreChat مختبراً.

## Alternatives considered

- **v1.35.1 كما في upstream:** مرفوض بسبب الثغرتين الحرجتين (libssl/libcrypto).
- **v1.55.0 (الأحدث):** نتيجة Trivy نفسها، لكنه إصدار `.0` عمره 9 أيام. 1.54.3 هو الـ patch الثالث في سلسلته.
- **Meilisearch Cloud أو خدمة بحث خارجية:** مرفوض، لأن نص المحادثات يخرج من المنصة.
- **ترك البحث معطلاً:** يخالف FR-003 AC-1 وقرار المالك.

## Consequences

- خدمة إضافية بكلفة صغيرة على Railway (ذاكرة وvolume) تُقاس بعد النشر، ضمن حد الإنفاق القائم.
- في volume Meilisearch نسخة من نص المحادثات: سياسة الاحتفاظ والحذف (OD-07) تشمله قبل أي بيانات حقيقية. LibreChat يحذف من
  الفهرس ما يُحذف من MongoDB.
- إن توقفت Meilisearch أثناء التشغيل يختفي مربع البحث فقط وتستمر المحادثة (M54). في Compose يبدأ LibreChat بعد أن تصبح
  Meilisearch سليمة (`depends_on`)؛ على Railway لا ينتظرها.
- ترقية Meilisearch بين إصدارات بصيغة بيانات مختلفة: حذف الـ volume ثم إعادة تشغيل LibreChat، بدل dump/import.
- الفحص الأسبوعي SC-18 يشمل الصورة الجديدة (`image-scan.sh` يقرأ كل صور Compose).

## Verification

- `compose_checks.py` و`railway_checks.py`: الخدمة خاصة ومثبتة وبمفتاح، والمراجع صحيحة.
- `mock_chat.py` M49–M56: البحث بالعربية والإنجليزية، والعزل بين المستخدمين، والتعطل، وإعادة البناء.
- `compose-stack.sh` T38–T41، و`railway-emulation.sh` R34–R39، وTrivy على الصورة.
- النتائج والتاريخ في [#125](https://github.com/faenazi/ef-ai-workspace/issues/125)، والحالة الحية في [CURRENT_STATE](../../../project/CURRENT_STATE.md).
