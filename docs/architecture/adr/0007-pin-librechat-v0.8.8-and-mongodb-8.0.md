# ADR-0007 — تثبيت LibreChat v0.8.8 و MongoDB 8.0.34 لمرحلة M1

| Field | Value |
|---|---|
| Status | **Accepted — بنطاق محدود:** تطوير وعرض ببيانات **اصطناعية فقط**، مع الإقرار بوسم "Pre-release" على GitHub؛ **ليس اعتماداً للإنتاج المؤسسي** (بوابات M6/M8) — قرار المالك D1 في [#11](https://github.com/faenazi/ef-ai-workspace/issues/11) (مغلق Completed في 2026-10-18) |
| Date | 2026-10-18 (اقتُرح واعتُمد) |
| Deciders | مالك المشروع (@faenazi) — اعتماد صريح مسجّل في #11 |
| Related | Issue #2، #11، ADR-0001، ADR-0004، ADR-0005، OD-02 (#4) |

## Context

تتطلب M1 اعتماد أحدث إصدار LibreChat **مستقر ومناسب للإنتاج**، مثبتاً بالـ digest، دون استخدام وسم `latest` العائم،
ودون اعتماد إصدار pre-release بلا موافقة صريحة. التحقق تم في 2026-10-17/18 من المصادر الرسمية مباشرة:

| الحقيقة | الدليل |
|---|---|
| أحدث tag منشور: **v0.8.8** (commit `e8f3be0`، 2026-09-30)؛ لا يوجد v0.8.9 ولا rc أحدث | `git ls-remote --tags https://github.com/LibreChat-AI/LibreChat` |
| صفحة GitHub Releases تَسِم **كل** إصدارات v0.8.x (من v0.8.0 حتى v0.8.8) بـ "Pre-release"، ولا يوجد إصدار موسوم "Latest" | github.com/LibreChat-AI/LibreChat/releases (الصفحات 1–4) |
| آلية النشر الرسمية upstream (`.github/workflows/tag-images.yml` عند v0.8.8) تعرّف أي tag بصيغة `vX.Y.Z` دون `-rc` بأنه **stable**، وتمنح وسم `latest` لأحدث stable فقط | `STABLE_TAG_REGEX='^v[0-9]+[.][0-9]+[.][0-9]+$'` |
| `ghcr.io/librechat-ai/librechat:v0.8.8` = `:latest` = index digest `sha256:5b706bcee1ca154a1e2987303aaeca0eb27f97919cccee4bb604226c2f8abf61` (linux/amd64 + linux/arm64) | `docker buildx imagetools inspect` |
| نفس الـ digest تماماً على `docker.io/librechat/librechat:v0.8.8` (upstream يدفع نفس البناء للسجلين) | `imagetools inspect --raw` + `docker-publish.yml` |
| إصدار config المطلوب: `librechat.yaml` **1.3.17** | `librechat.example.yaml`، `CONFIG_VERSION` في `packages/data-provider` |
| upstream v0.8.8 يستخدم `mongo:8.0.20`؛ أحدث patch في سلسلة 8.0 هو **8.0.34** (digest `sha256:4a4ab5d4834207389e0d7270fac988e21ffedccecba77991a552f755df229907`) | `docker-compose.yml` upstream؛ Docker Hub API |
| ملاحظات الإصدار v0.8.8: إصلاحات أمنية ("stronger credential boundaries, tenant-scoped endpoints, 2FA management limits"، "Reject Invalid AES Credentials Before Startup")؛ config v1.3.15–1.3.17 | صفحة الإصدار |
| `UPGRADING.md`: ترحيل فهارس tenant مطلوب يدوياً لقواعد بيانات v0.8.7 وما قبلها — لا ينطبق على قاعدة جديدة | `UPGRADING.md` عند v0.8.8 |

## Decision

1. **LibreChat v0.8.8** بالمرجع القانوني `ghcr.io/librechat-ai/librechat:v0.8.8@sha256:5b706bce…abf61`.
2. **MongoDB 8.0.34** بالمرجع `mongo:8.0.34@sha256:4a4ab5d4…29907` (أحدث patch من السلسلة التي يختبرها upstream).
3. `librechat.yaml` version **1.3.17**؛ الفحص `compose_checks.py` يربط الإصدارين.
4. لا Meilisearch (OD-02)، ولا RAG/Agents/MCP/SSO/هوية (مراحلها).

## Rationale

- v0.8.8 هو أحدث إصدار **مستقر وفق تعريف upstream نفسه** (ليس RC)، ويحمل إصلاحات أمنية؛ وسم "Pre-release" على GitHub
  ممارسة عامة لكل سلسلة 0.8.x وليس مؤشراً على أن v0.8.8 أقل استقراراً من سابقيه.
- البديل الوحيد غير الموسوم Pre-release يسبق v0.8.0 (أكثر من سنة) ويفتقد إصلاحات أمنية — غير مناسب للإنتاج.
- 8.0.34 يضيف إصلاحات patch على 8.0.20 دون تغيير السلسلة؛ **التوافق مُختبر فعلياً** (smoke test 35/35، انظر تقرير M1).

## Alternatives considered

| البديل | سبب عدم الاختيار |
|---|---|
| آخر إصدار غير موسوم Pre-release (قبل v0.8.0) | قديم، يفتقد إصلاحات أمنية وميزات (Skills، config الحالي) |
| `latest` أو صور dev (`librechat-dev`, `registry.librechat.ai/...:latest`) | غير مثبتة؛ تتغير دون مراجعة |
| `mongo:8.0.20` كما في upstream | أقدم بـ 14 patch؛ لا فائدة توافقية مقابل فقدان الإصلاحات |
| صورة `librechat-api` (API فقط) | تتطلب خادماً منفصلاً للواجهة؛ تعقيد غير مبرر |

## Consequences

- اعتمد المالك القرار (#11، D1) لبيئة التطوير والعرض ببيانات اصطناعية فقط. أي استخدام إنتاجي أو ببيانات حقيقية يتطلب
  قراراً جديداً بعد بوابات M6/M8.
- الترقيات اللاحقة عبر Dependabot (`docker-compose`) + runbook الترقية + smoke test.
- ملفات Compose الرسمية upstream لا تُستخدم (dev images، `--noauth`، منافذ منشورة، بلا healthchecks).

## Verification

`tests/smoke/m1-stack.sh` (T04: الحاويات تعمل بالـ digest المثبت بالضبط؛ T05: الإصدار v0.8.8) — النتائج في
[تقرير M1](../../history/reports/M1-delivery-report.md).
