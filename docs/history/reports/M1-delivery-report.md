# تقرير تسليم M1 — LibreChat Platform Foundation & Coolify Deployment Readiness

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس حالة حالية ولا سياسة.** الحالة الحية: [project/CURRENT_STATE.md](../../../project/CURRENT_STATE.md)؛ الفهرس: [docs/history/README.md](../README.md).

> **ملاحظة تاريخية (2026-10-18):** هذا التقرير سجل M1 كما سُلّم ودُمج (PR #12، `0db80d9`) ويُحفظ دون تعديل في محتواه.
> هدف Coolify **مُستبدل** بـ [ADR-0008](../../../docs/architecture/adr/0008-multi-environment-hosting-railway-windows-ubuntu.md)؛ المسارات
> `infrastructure/coolify/` و`tests/smoke/m1-stack.sh` نُقلت (انظر [تقرير M1.1](M1.1-hosting-transformation-report.md)).

| الحقل | القيمة |
|---|---|
| Issue | [#2](https://github.com/faenazi/ef-ai-workspace/issues/2) |
| الفرع | `feature/m1-librechat-foundation` (من `main` @ `0eab526`) |
| التاريخ | 2026-10-18 |
| المنفّذ | Claude Code Cloud |
| النتيجة | الحزمة **مُنفّذة ومُختبرة في جلسة السحابة (35/35)**؛ **غير منشورة**؛ قرارات المالك **معتمدة** في [#11](https://github.com/faenazi/ef-ai-workspace/issues/11) (2026-10-18)؛ الدمج قرار المالك |

> **مستوى الأدلة:** كل النتائج `Tested (cloud session)` — نفّذها الوكيل المنفّذ في جلسة Claude Code Cloud. **ليست** تحققاً
> مستقلاً عبر GitHub CI (Actions غير متاح، #10). تُقبل بديلاً لـ CI على PR #12 فقط بموجب CI-EX-02 (**Approved**، #11) — دون أن تصبح تحققاً مستقلاً.

## 1. الإصدار المختار

| البند | القيمة | المصدر |
|---|---|---|
| أحدث إصدار منشور | **v0.8.8** (tag `e8f3be0`، 2026-09-30) — لا v0.8.9 ولا rc أحدث | `git ls-remote --tags` لـ `LibreChat-AI/LibreChat` |
| حالة الإصدار | upstream يصنّفه **stable** (`tag-images.yml`: `vX.Y.Z` دون `-rc`، ويمنحه `latest`)؛ لكن **صفحة GitHub تَسِم كل v0.8.x بـ "Pre-release"** ولا يوجد "Latest" | صفحة Releases (1–4)، workflow upstream |
| الصورة | `ghcr.io/librechat-ai/librechat:v0.8.8@sha256:5b706bcee1ca154a1e2987303aaeca0eb27f97919cccee4bb604226c2f8abf61` (amd64 `sha256:1e3bd3ac…`، arm64 `sha256:0dba606c…`) = `:latest` | `docker buildx imagetools inspect` |
| MongoDB | `mongo:8.0.34@sha256:4a4ab5d4834207389e0d7270fac988e21ffedccecba77991a552f755df229907` (upstream يختبر 8.0.20؛ 8.0.34 أحدث patch في السلسلة) | upstream `docker-compose.yml`، Docker Hub |
| `librechat.yaml` version | 1.3.17 | `librechat.example.yaml`، `CONFIG_VERSION` |
| ملاحظات أمنية/ترقية | إصلاحات أمنية في v0.8.8؛ ترحيل فهارس tenant يدوي لقواعد ≤ v0.8.7 (لا ينطبق على قاعدة جديدة) | صفحة الإصدار، `UPGRADING.md` |

**السبب:** أحدث إصدار مستقر وفق تعريف upstream، ويحمل إصلاحات أمنية؛ البديل غير الموسوم Pre-release أقدم من v0.8.0.
بسبب الوسم، احتاج القرار اعتماداً صريحاً: [ADR-0007](../../../docs/architecture/adr/0007-pin-librechat-v0.8.8-and-mongodb-8.0.md)
**Accepted** في #11 (2026-10-18) بنطاق محدود — بيانات اصطناعية/عرض فقط، ليس للإنتاج.

**قيد البيئة:** وكيل الشبكة يمنع تنزيل blobs من `pkg-containers.githubusercontent.com` (GHCR). سُحبت الصورة من
`docker.io/librechat/librechat@sha256:5b706bce…` — **نفس الـ index digest تماماً** (upstream يدفع نفس البناء للسجلين)؛ المحتوى
مُعنون بالمحتوى فهو مطابق بايت ببايت. الحاويات تعمل بالمرجع القانوني لـ GHCR (T04 يتحقق من الـ digest الفعلي).

## 2. المعمارية المُنفّذة

`librechat` (منفذ داخلي 3080، شبكتا `frontend` + `backend`) ← `mongodb` (شبكة `backend` **internal**، `--auth`).
التفاصيل والضوابط: [deployment.md §2](https://github.com/faenazi/ef-ai-workspace/blob/0db80d941d0ac6d5ea6f7b49674e913caaaab19f/docs/operations/deployment.md#2-مكونات-الحزمة-m1). قرارات إعداد مُتحقق منها أثناء التنفيذ:

| القرار | السبب / الدليل |
|---|---|
| مستخدم MongoDB للتطبيق بدور `readWrite` فقط عبر `mongo-init/` | LibreChat أنشأ مجموعاته وفهارسه بهذا الدور (سجل البدء)؛ T07–T09 |
| `environment` صريح بدل `env_file` | الحاوية تتلقى ما تحتاجه فقط؛ يعمل بنفس الشكل في Coolify وخارجه |
| `.env.example` بقيم **فارغة** | `${VAR:?}` يمنع النشر بقيم وهمية؛ `docker compose config` ينجح فقط بملف كامل (انحراف مقصود عن صياغة معيار #2 «ينجح مع `.env.example`») |
| `SCHEDULES_SINGLE_PROCESS=true` + `SCHEDULES_DISABLED=true` | بدونهما يسجّل LibreChat خطأ ERROR عند البدء (محرك الجدولة)؛ مُتحقق من مصدر upstream وسجل التشغيل؛ ميزة الجدولة تجريبية ومن نطاق M5 |
| `ALLOW_UNVERIFIED_EMAIL_LOGIN=false` | `create-user` يضبط `emailVerified=true` افتراضياً، فالدخول يعمل (T17) دون فتح دخول غير موثّق |

## 3. نتائج الاختبار الفعلية

### 3.1 الحزمة الحقيقية — `tests/smoke/m1-stack.sh`

commit **`97d74be`** (تسجيل اعتمادات #11) · 2026-10-18T08:16Z · Docker 29.8.2 · Compose 5.6.0 · **35/35 PASS** · exit 0
(رأس الـ PR النهائي بعده يغيّر ملفات السجلات فقط — نتيجته في تعليق التحقق على PR #12. تشغيلات سابقة: `c9fed2b` 35/35؛ `79da678` بعد إصلاحات المراجعة 35/35؛ `d5b4677` قبل المراجعة 35/35. الـ digests أُعيد التحقق منها من السجلات الحية في 2026-10-18 ولا يوجد إصدار أحدث من v0.8.8)

| # | الفحص | النتيجة |
|---|---|---|
| T01–T02 | `docker compose config` ينجح بملف كامل؛ يرفض غياب الأسرار ("required variable") | PASS |
| T03 | الخدمتان healthy (healthchecks + `service_healthy`) | PASS |
| T04–T05 | الحاويات تعمل بالـ digest المثبت بالضبط؛ LibreChat يبلغ v0.8.8 | PASS |
| T35 | لا أسطر ERROR في سجل بدء LibreChat | PASS |
| T06–T09 | MongoDB يرفض القراءة دون مصادقة؛ مستخدم التطبيق: قراءة/كتابة قاعدته، لا كتابة في قاعدة أخرى، لا إنشاء مستخدمين | PASS |
| T10–T12 | `GET /health` = `OK`؛ واجهة الويب؛ `/login` = 200 | PASS |
| T13–T15 | `/api/config`: التسجيل معطّل، الدخول بالبريد مفعّل، الاجتماعي معطّل؛ `POST /api/auth/register` مرفوض؛ لم يُنشأ مستخدم | PASS |
| T16–T19 | `create-user` ينشئ أول مسؤول ADMIN؛ الثاني USER؛ كلمة مرور خاطئة مرفوضة | PASS |
| T20–T24 | لا منفذ لـ MongoDB؛ LibreChat على 127.0.0.1 فقط (override)؛ MongoDB على شبكة internal فقط؛ لا egress؛ حاوية خارجية لا تصل إليه | PASS |
| T25–T27 | بعد `down`/`up`: healthy، دخول المسؤول، ملفات `uploads` و`data` باقية | PASS |
| T28–T33 | `backup.sh` ← إضافة مستخدم ← **حذف كل الـ volumes** ← حزمة جديدة ← `restore.sh` ← دخول المسؤول، 2 مستخدمين، مستخدم ما بعد النسخ غائب، ملفات `uploads` و`data` مُستعادة (السجلات مستبعدة عمداً) | PASS |
| T34 | لا قيمة سرية في سجلات الحاويات | PASS |

### 3.2 حساسية الفحوصات (اختبارات سلبية)

| الحزمة المُضعّفة عمداً | النتيجة |
|---|---|
| MongoDB بلا مصادقة + منفذ منشور، شبكة غير internal، التسجيل مفعّل | 18/35 — فشلت T06، T08، T09، T13–T15، T20، T22، T23 كما يجب (+ فشل متتابع متوقع: T17، T26، T28، T30–T33) |
| إزالة `SCHEDULES_SINGLE_PROCESS` | 34/35 — فشلت T35 فقط (خطأ `[schedules]`) |
| نسخ احتياطي لا يشمل `/app/data` (الإصدار قبل المراجعة) | 34/35 — فشلت T33 فقط (`/app/data/smoke-marker.txt` غير مُستعاد) |
| نفس الإضعافات على `compose_checks.py` | FAIL بأربع مخالفات (منفذ، `--auth`، شبكة، التسجيل) |
| ملاحظة | تمرير `--noauth` مع بيانات root يجعل صورة mongo ترفض البدء ("auth is not allowed when noauth is specified") — حماية إضافية من الصورة نفسها |

### 3.3 فحوصات المستودع والأمن — `scripts/validate/run-all.sh`

على رأس الـ PR النهائي (انظر تعليق التحقق في PR #12) · Python 3.12.13 · **كلها PASS**: repo_checks (9)، compose_checks، yamllint، check-jsonschema ×4، actionlint 1.7.12،
gitleaks 8.30.1 (التاريخ + الشجرة: no leaks)، zizmor 1.31.1 (No findings).

### 3.4 قياس الموارد (خمول، بعد البدء)

| الخدمة | الذاكرة | CPU |
|---|---|---|
| librechat | ~495 MiB | <1% |
| mongodb | ~251 MiB | <1% |
| الصور على القرص | ~5.7 GB | — |
| بيانات MongoDB الأولية | ~212 MB | — |

الحجم المقترح لخادم العرض (Coolify + الحزمة): **4 vCPU / 8 GB RAM / ≥ 60 GB SSD**؛ حد أدنى مطلق غير مُتحقق: 2 vCPU / 4 GB / 40 GB — انظر [deployment.md §3](https://github.com/faenazi/ef-ai-workspace/blob/0db80d941d0ac6d5ea6f7b49674e913caaaab19f/docs/operations/deployment.md#3-المتطلبات-المسبقة-لنشر-coolify-لا-يُفترض-وجودها) (يشمل متطلبات Coolify الرسمية). لم يُختبر تحت حمل.

### 3.5 ما لم يُنفّذ

| الفحص | الحالة | السبب والأثر |
|---|---|---|
| GitHub Actions | **NOT RUN** | غير متاح (#10) — لا تحقق مستقل |
| نشر Coolify، HTTPS، توجيه النطاق | **NOT RUN** | لا VPS/نطاق (#6) ولا موافقة نشر — سلوك شبكة Coolify وربط الملفات غير متحقق |
| سحب الصورة من GHCR مباشرة | **NOT RUN** | الوكيل يمنع blobs GHCR — استُخدم docker.io بنفس الـ digest |
| محادثة مع نموذج | **NOT APPLICABLE** | لا مزوّد معتمد (OD-01، M3) |
| فحص ثغرات الصور (Trivy) | **NOT RUN** | الأداة غير معتمدة/مثبتة — M6 |

## 4. النتائج الأمنية

**عولجت أثناء التنفيذ:** Compose الرسمي upstream (`--noauth`، منافذ منشورة، صور dev/`latest`، كلمات مرور افتراضية لـ pgvector)
لم يُستخدم؛ قالب LibreChat في Coolify (صورة dev، التسجيل مفعّل) لم يُستخدم؛ خطأ محرك الجدولة عولج وأضيف فحص T35؛ خطأ
تحليل الـ tag في `compose_checks.py` اكتُشف وأُصلح؛ حماية من تشغيل متزامن للاختبارات بعد إعادة تشغيل العامل.

**مخاطر متبقية:**

| الخطر | التخفيف / المتابعة |
|---|---|
| v0.8.8 موسوم Pre-release على GitHub | معتمد للعرض ببيانات اصطناعية فقط (#11)؛ الإنتاج يتطلب قراراً جديداً بعد M6/M8 |
| الأدلة غير مستقلة (الوكيل كتب واختبر) | استعادة Actions (#10) |
| Coolify قد يضيف شبكته لـ `mongodb` | يبقى دون منفذ ونطاق ومحمياً بالمصادقة؛ يُتحقق في أول نشر |
| أسرار MongoDB مرئية عبر `docker inspect` لمن يملك صلاحية Docker على الخادم | قصر صلاحيات الخادم؛ Docker secrets/مخزن أسرار في M6 |
| `CREDS_KEY/CREDS_IV` فقدانهما = فقدان البيانات المشفّرة | حفظها في مخزن أسرار معتمد (deployment.md §4) |
| النسخ الاحتياطي غير مجدول ولا مشفّر بعد | M6 (runbook §2) |
| حماية `main` غير مفعّلة | #3 |

## 5. جاهزية النشر على Coolify

المتطلبات الدقيقة والخطوات: [deployment.md §3–§5](https://github.com/faenazi/ef-ai-workspace/blob/0db80d941d0ac6d5ea6f7b49674e913caaaab19f/docs/operations/deployment.md#3-المتطلبات-المسبقة-لنشر-coolify-لا-يُفترض-وجودها):
VPS (#6)، نطاق، ربط GitHub App، تفويض نشر منفصل (#13)، إدخال المتغيرات المولّدة، النشر، `/health`، إنشاء أول مسؤول.

## 6. التراجع

لا بنية منشورة: إغلاق الـ PR دون دمج، أو `git revert` للدمج عبر PR جديد. بعد أي نشر: [runbook §4](../../../docs/operations/runbook.md#4-التراجع-rollback).

## 7. معالجة مراجعة المالك (PR #12، 2026-10-18)

| الملاحظة | التحقق من المصدر | المعالجة | الدليل |
|---|---|---|---|
| P1: Coolify يحتاج *Preserve repository during deployment* لربط ملفات المستودع | مؤكد — توثيق Coolify (`applications/builds/docker-compose`: "A file bind source must exist") | خطوة إلزامية في deployment.md §4 + تحقق ما بعد النشر من الربطين والسجلات | الحالة **NOT RUN** حتى أول نشر |
| P1: النسخ لا يشمل `/app/data` | مؤكد — `/app/data` يحمل `.env.temp` (توثيق dotenv) وبيانات agent plugins (`DEPLOYMENT_PLUGIN_DATA_DIR=data/plugins`)؛ فارغ في M1 | `backup.sh`/`restore.sh` يشملانه؛ السجلات مستبعدة عمداً وموثّقة؛ T27/T33 تتحقق من `uploads` و`data` | 35/35؛ الاختبار السلبي يفشل T33 بدون `data` |
| P2: عدد 34/34 في deployment.md وحجم القرص 20 GB | مؤكد — Coolify: 2 CPU / 2 GB / 10 GB لنفسه و30 GB إجمالي موصى به | 35/35؛ مقترح 4 vCPU / 8 GB / ≥ 60 GB SSD، وحد أدنى مطلق غير مُتحقق 2 / 4 / 40 | deployment.md §3 |

## 8. حالة القبول النهائي لـ M1 (2026-10-18)

| البند | الحالة |
|---|---|
| التنفيذ ومعايير القبول التقنية لـ #2 | **مكتمل — Tested (cloud session)** على `97d74be` (run-all PASS، smoke 35/35)؛ سابقاً `c9fed2b` |
| مراجعات المالك التقنية على PR #12 | مقبول تقنياً؛ لا ملاحظات P1/P2 متبقية (`5561911455`) |
| اعتماد LibreChat v0.8.8 (ADR-0007) | **Accepted** — D1 في #11 (2026-10-18): بيانات اصطناعية/عرض فقط، ليس للإنتاج |
| استثناء CI-EX-02 | **Approved** — D2 في #11: PR #12 فقط، ينتهي بدمجه/إغلاقه |
| مسار M1.1 (Coolify) | **Approved as a plan** — D3 في #11؛ التنفيذ يتطلب #6 وتفويضاً منفصلاً ([#13](https://github.com/faenazi/ef-ai-workspace/issues/13)) |
| GitHub CI المستقل | **NOT VERIFIED** — صفر تشغيلات لـ `CI`/`Security` على PR #12؛ تشغيلات Dependabot على `main` لا تُحتسب (#10) |
| النشر على Coolify / HTTPS / ربط الملفات | **NOT RUN** — خطة القبول التشغيلي في #13 (تتطلب #6 وتفويضاً منفصلاً) |
| **الخلاصة** | M1 **جاهز للمراجعة النهائية ودمج المالك** (PR #12 Ready for Review)؛ ليس مُعتمداً للإنتاج؛ M2 لا يبدأ قبل M1.1 |

