# دليل التشغيل (Operations Runbook)

| الحقل | القيمة |
|---|---|
| الحالة | Compose (Windows/Ubuntu): الأقسام 2–4 **Tested (cloud session)**؛ Railway: النشر وإعادة النشر Verified على `dev`، النسخ والاستعادة **NOT RUN** (#15). القسم 1 و5 مخطط |

> لا يُعتبر أي إجراء صالحاً للإنتاج قبل وسم قسمه بـ `Tested` مع تاريخ ورابط الدليل، وإعادة اختباره في البيئة المستهدفة.
> Compose: أسماء الحاويات `docker ps --format '{{.Names}}' | grep -E 'mongodb|librechat'`. Railway: لوحة المشروع أو `railway ssh --service <name>`.

## 1. السجلات والمراقبة — `Planned M6`

| البيئة | المُنفّذ الآن |
|---|---|
| Compose | سجلات الحاويات json-file (10 MB × 5 لكل خدمة)؛ ملفات LibreChat في volume `librechat-logs` (`/app/logs`)؛ healthchecks لكل خدمة |
| Railway | سجلات البناء والنشر في اللوحة/`railway logs`؛ `/health` عند النشر فقط (Railway لا يراقب بعد ذلك)؛ ملفات `/app/logs` عابرة |

- `/metrics` يعيد 401 ما لم يُضبط `METRICS_SECRET` (افتراضي آمن؛ غير مُفعّل).
- M6: أداة مراقبة وتجميع سجلات مركزية وتنبيهات توفر ومساحة (TBD — NFR-OBS-01).
- تصحيح عن M1: ملفات سجل LibreChat تُكتب في `/app/logs` (`getLogDirectory` upstream)؛ ربط M1 على `/app/api/logs` لم يلتقط شيئاً. صُحّح (T37).

## 2. النسخ الاحتياطي والاستعادة

| المكوّن | Compose (Windows/Ubuntu) — `Tested (cloud session) 2026-10-18` | Railway — `NOT RUN` |
|---|---|---|
| MongoDB (قاعدة `LibreChat`) | [`backup.sh`](../../scripts/operations/backup.sh) → `mongodump --archive --gzip` كمستخدم root داخل الحاوية | **Volume backup** لخدمة `mongodb` (Backups tab: يدوي + Daily/Weekly) — لقطة متسقة كتعافٍ من انهيار (WiredTiger journal) |
| الملفات | نفس السكربت → `tar` لـ `/app/uploads` و`/app/client/public/images` و`/app/data` | Volume backup لخدمة `librechat` (`/app/storage` كاملاً) |
| فهرس البحث (Meilisearch) | **مستبعد عمداً:** مشتق من MongoDB؛ `restore.sh` يعيد بناءه (`search-reindex.sh`) | لا volume backup لخدمة `meilisearch`: ضياعه يُصلحه إعادة نشر `librechat`؛ بعد استعادة MongoDB: [railway.md §3](railway.md#إضافة-البحث-في-المحادثات-إلى-بيئة-قائمة-125-adr-0014) |
| السجلات | **مستبعدة عمداً** | عابرة |
| الإعداد | Git | Git (`railway.ts`، Dockerfiles) |
| الأسرار | **ليست في النسخة** — مخزن أسرار معتمد (`CREDS_KEY/IV` لازمة للاستعادة) | **ليست في volume backups:** نسخة استرداد مشفّرة يملكها المالك (`railway-secrets.sh --recovery-file`)، تُستعاد بـ `--from-recovery` (مُتدرّب عليه: R28–R30) |

```sh
scripts/operations/backup.sh  <mongodb-container> <librechat-container> /path/to/encrypted/backups
scripts/operations/restore.sh <mongodb-container> <librechat-container> /path/to/backups/<timestamp>   # مُدمّر؛ يعيد تشغيل librechat
```

- **مُختبر (Compose local + on-prem):** فقدان كل الـ volumes ثم الاستعادة (T28–T33).
- **Railway:** الاستعادة تُنشئ volume جديداً مركّباً على نفس المسار (القديم يبقى غير مركّب)، داخل نفس المشروع والبيئة فقط؛ مسح الـ volume
  يحذف نسخه. نقل بيانات اصطناعية من Railway إلى Compose غير مطلوب ولم يُختبر.
- النسخة قد تحتوي بيانات حساسة؛ تُعامل كسرية وتُخزّن مشفّرة. **غير محسوم:** جدولة Compose (cron/systemd timer)، الوجهة المشفّرة وإقامتها، RTO/RPO (OD-04).

## 3. الترقية (Upgrade)

الحالة: الإجراء محدد؛ مُختبر لخط الأساس الحالي فقط. ترقية LibreChat بتفصيلها (فحص الإصدار الجديد بأداة، والتعديلات والترجمة وطبقة
ADR-0012) في [librechat-upgrade.md](librechat-upgrade.md)؛ الخطوات أدناه للصور عموماً.

1. Issue ترقية: الإصدار الجديد، ملاحظات الإصدار و[`UPGRADING.md`](https://github.com/LibreChat-AI/LibreChat/blob/main/UPGRADING.md) upstream، تغيير
   `librechat.yaml` version، وأي ترحيل يدوي. ترقية MongoDB major تتطلب ADR (Dependabot يتجاهلها).
2. PR واحد يحدّث tag + digest في `infrastructure/compose/compose.yaml` **و** `FROM` في `infrastructure/railway/*.Dockerfile`
   (`railway_checks.py` يفشل إن اختلفا) + `CONFIG_VERSION` في `compose_checks.py` + ADR عند تغيير جوهري.
3. التحقق: `scripts/validate/run-all.sh`، `tests/smoke/compose-stack.sh local|onprem`، `tests/smoke/railway-emulation.sh`، `scripts/validate/image-scan.sh`.
4. قبل النشر: نسخة احتياطية للبيئة (Compose: `backup.sh`؛ Railway: manual volume backup للخدمتين).
5. النشر: Compose `docker compose … pull && … up -d`؛ Railway: دمج في `main` (أو Deploy Latest Commit). ثم `/health`، دخول المسؤول،
   سجل البدء (`Custom config file loaded`، لا أخطاء).

## 4. التراجع (Rollback)

| الحالة | Compose | Railway |
|---|---|---|
| تغيير توثيق/CI | `git revert` عبر PR | نفسه |
| نشر فشل قبل كتابة بيانات جديدة | `git checkout <commit سابق>` ثم `up -d` (يعيد الـ digest السابق) | Deployments → النشر السابق → **Redeploy**، أو revert في Git |
| ترقية غيّرت المخطط/الفهارس | إيقاف `librechat` → `restore.sh` من نسخة ما قبل الترقية → الإصدار السابق → التحقق | استعادة volume backup للخدمتين (ما قبل الترقية) → Redeploy النشر السابق |
| تغيير IaC خاطئ | — | revert لـ `railway.ts` عبر PR → `railway config plan` → `apply` (الـ volumes لا تُحذف بـ apply أبداً) |
| إزالة بيئة عرض بالكامل | `docker compose … down -v` بعد نسخة إن لزم | حذف مشروع Railway (بتفويض المالك) |

## 5. الاستجابة للحوادث — `Requirement`

| الحادث | الإجراء الفوري |
|---|---|
| تسرب سر (مفتاح API في Git أو سجل) | إلغاء/تدوير المفتاح فوراً عند المزوّد → استبداله في `.env`/متغيرات Railway → توثيق في Issue خاص (دون نشر السر) → تقييم إعادة كتابة التاريخ بموافقة المالك |
| رفع بيانات حقيقية لبيئة غير معتمدة (خصوصاً Railway) | إيقاف الاستخدام، حذف البيانات من المنصّة **ومن نسخ الـ volumes**، إبلاغ مالك المشروع والأمن |
| توقف الخدمة | `/health` والسجلات؛ إعادة التشغيل/النشر؛ التراجع إن لزم |
| ثغرة في LibreChat/MongoDB upstream | تقييم الأثر (`image-scan.sh`)، الترقية للإصدار المصحح عبر §3 |

جهات التصعيد وقنوات الإبلاغ الرسمية: **TBD** (انظر [SECURITY.md](../../SECURITY.md)).

## 6. لوحة الإدارة (Admin Panel) — [ADR-0016](../architecture/adr/0016-librechat-admin-panel.md)

| البيئة | العنوان |
|---|---|
| Windows (WSL2) | `http://localhost:3000` (loopback فقط) |
| Ubuntu في الموقع | `https://<EFAIW_ADMIN_HOSTNAME>` (Caddy، داخلي فقط) |
| Railway `dev` | رابط `*.up.railway.app` الثاني (`ADMIN_PANEL_URL` في خدمة librechat)؛ ويظهر للمسؤول أيضاً في الإعدادات ← عام ← «لوحة المسؤول» |

- **الدخول:** بحساب LibreChat الذي يحمل دور `ADMIN` (أو منحة `access:admin`)، وبرمز 2FA إن فعّله الحساب. أي حساب آخر يُرفض.
  الجلسة تنتهي بعد 30 دقيقة خمول. محاولات الدخول عبر اللوحة تشترك في حد LibreChat (7 / 5 دقائق)، فبعد خطأ متكرر انتظر 5 دقائق.
- **المسموح (قرار المالك، #141):** في Access أدوار مخصصة ومجموعات وإضافة أعضاء (البحث عن الموظف يتم هنا)، وفي Grants منح إدارية وسجل التدقيق.
- **تنبيه — الأدوار المخصصة:** إسناد دور مخصص لموظف **يستبدل** دوره `USER` (دور واحد لكل حساب في v0.8.8). يفقد ما لا يمنحه الدور الجديد،
  والدور الجديد يبدأ بكل الصلاحيات مغلقة. امنح الدور ما يحتاجه من صلاحيات `USER` قبل الإسناد. المجموعات لا تغيّر الدور.
- **غير المسموح:** صفحة Configuration للقراءة فقط. أي إعداد يتغير عبر PR على `infrastructure/common/librechat.yaml`.
  صلاحيات الدورين `USER`/`ADMIN` تُعاد من الملف عند كل إقلاع، فتعديلها من اللوحة مؤقت.
- **إنشاء الحسابات وحذفها:** غير متاح في اللوحة على v0.8.8 (زر الحذف يظهر لكن مساره معلّق في الخادم: `api/server/routes/admin/users.js`).
  - الإنشاء عبر `create-user` ([deployment.md §3](deployment.md#3-إنشاء-أول-مسؤول-كل-البيئات))؛ التسجيل الذاتي مغلق (ADR-0024).
  - الحذف داخل حاوية `librechat`: `npm run delete-user -- <email>`. يحذف الحساب ومحادثاته ورسائله وسجلات ملفاته وذاكرته
    ووكلاءه وأوامره وروابطه، ويسأل عن سجل الاستهلاك. لا يحذف الملفات على القرص: احذف `/app/storage/uploads/<id>`
    و`uploads/temp/<id>` و`images/<id>` بعده.
  - Railway من جلسة الوكيل السحابية: المنفذ 22 مغلق، و`railway ssh` في CLI 4.30.0 يعمل عبر HTTPS بالرمز المضبوط (CLI 5.x يحتاج SSH).
  - بلا Redis يسأل السكربت عن إيقاف كل العمليات: تحقق أولاً أن آخر رسالة للحساب قديمة (لا رد قيد التوليد).
- **فحص الانحراف** بعد أي جلسة إدارة:
  - Compose: `scripts/operations/admin-config-drift.sh <mongodb-container>`؛
  - Railway: `scripts/operations/admin-config-drift.sh --railway`.
  - يفشل عند أي تجاوز إعدادات أو دور مخصص يسمح بأكثر من `USER`. الإصلاح من اللوحة: حذف التجاوز في Configuration، أو إلغاء الصلاحية في Access.
- **التراجع:** إيقاف الخدمة (Compose: `efc stop admin-panel`؛ Railway: حذف الرابط ثم revert + `config apply`). الأدوار والمجموعات
  المنشأة تبقى في MongoDB وتُحذف من اللوحة إن لزم.

## 7. استهلاك النماذج وتكلفتها (FinOps)

- **التقرير** (قراءة فقط، لا يقرأ نص المحادثات):
  - Compose: `scripts/operations/usage-report.sh <mongodb-container> [--month YYYY-MM] [--by-user] [--json]`؛
  - Railway: `scripts/operations/usage-report.sh --railway [--month YYYY-MM]` (عبر `railway ssh`، مفتاح SSH للمالك، #141).
- **ما يعرضه:** عدد الاستدعاءات وtokens الإدخال والإخراج لكل شهر، ولكل وضع (سريع / متأنٍّ / عميق، بالإنترنت ودونه)، ولكل نموذج،
  وللمهام الخلفية (العناوين والملخصات)، ولكل موظف مع `--by-user`. المصدر `transactions` في MongoDB، والوضع من `messages.endpoint`.
- **التكلفة تقديرية:** بأسعار القائمة في [qwen-list-prices.json](../../scripts/operations/qwen-list-prices.json) (المصدر وتاريخه في الملف)،
  حدٌّ أعلى لأنها تتجاهل خصم الإدخال المخزّن وأسعار خارج الذروة. **فاتورة Qwen Cloud هي المرجع.**
- **ما لا يقيسه** (مقاس 2026-10-25، [ai-safe-defaults.md §4.2](../architecture/ai-safe-defaults.md#42-البحث-والاستهلاك-على-qwen-cloud-2026-10-25)):
  عدد عمليات البحث المدفوعة (من الفاتورة فقط)، وtokens التفكير منفصلة (ضمن الإخراج)، واستدعاءات وكيل الذاكرة (لا يسجلها LibreChat).
- لا حدود استهلاك مفعّلة؛ أي حد رقمي قرار مالك (#39).
