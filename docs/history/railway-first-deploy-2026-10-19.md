# Railway `dev` — سجل أول نشر (2026-10-19)

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75))؛ ليس Runbook.** المصدر: `docs/operations/railway.md` §3 عند `main@14edcb2`.
> البيئة أُنشئت مرة واحدة؛ لا تُعد هذه الخطوات على مشروع Railway `dev` القائم. التشغيل الحالي:
> [railway.md §4](../operations/railway.md#4-النشر--تلقائي-من-main-adr-0010)؛ الفهرس: [docs/history/README.md](README.md).

> **هذا سجل إجراءات إنشاء البيئة لأول مرة (تم في 2026-10-19)، وليس Runbook لتشغيلها من جديد.**
> المشروع والخدمتان والـ volumes والأسرار موجودة بالفعل، والنشر التلقائي من `main` مفعّل (ADR-0010).
> **لا تُعد** `railway config apply` لإنشاء الموارد ولا `railway-secrets.sh` لتوليد أسرار جديدة بغرض فحص الحالة؛
> ذلك قد يسبب تغييراً غير مقصود/فقدان القدرة على الاستعادة. التشغيل الحالي في §4 و[مصفوفة #15](https://github.com/faenazi/ef-ai-workspace/issues/15).
> للقراءة دون تغيير: `railway status` و`railway config plan` بتفويض وصلاحية بيئة dev. نتيجة الفحص من دون token لا تساوي واقع اللوحة.


من طرفية فيها Railway CLI ≥ 5.42.1 وNode ≥ 22.6 (حاسوب المالك أو جلسة مفوّضة بـ project token):

```bash
# HISTORICAL BOOTSTRAP ONLY — do not replay against the existing Railway dev project.
railway login && railway link            # المشروع ef-ai-workspace، البيئة dev
npm ci --prefix .railway                 # SDK المثبت (railway@3.16.0)
railway config plan                      # تاريخياً: أول خطة بلا source أو domain؛ الوضع الحالي مصدر main ورابط LibreChat العام
railway config apply                     # التاريخ الأول فقط: أنشأ الموارد؛ تطبيق التغييرات الآن قد يعيد النشر ويتطلب بوابات
scripts/setup/railway-secrets.sh --recovery-file ~/efaiw-railway-dev-secrets.enc
#   يولّد الأسرار محلياً، يكتب أولاً نسخة استرداد مشفّرة (AES-256، PBKDF2، عبارة مرور تُكتب عند الطلب) ويتحقق منها،
#   ثم يمررها لـ Railway عبر stdin؛ لا يكتب فوق قيم موجودة. خزّن الملف وعبارة المرور منفصلين في مخزن يملكه المالك.
```

أنماط أخرى للسكربت: `--prompt` (إدخال قيم مولّدة مسبقاً في مدير كلمات مرور/خزنة معتمدة دون عرضها)،
`--from-recovery <file>` (استعادة نفس القيم لبيئة أُعيد بناؤها — مُتدرّب عليه في المحاكاة R28–R30)،
`--accept-no-recovery` (عرض اصطناعي قابل للرمي فقط؛ فقدان المفاتيح = فقدان البيانات المشفّرة).

ثم من اللوحة (يعمل من الجوال):
1. **تحقق المصدر (ADR-0010):** لكل من `mongodb` و`librechat` → Settings → **Source**: المستودع `faenazi/ef-ai-workspace`، الفرع `main`،
   autodeploy **Enabled**، Wait for CI **مُطفأ**، وWatch Paths كما في `railway.ts`. سجّل ذلك على #15.
2. (اختياري، موصى به) **Seal** لكل سر: Variables → ⋯ → Seal. لا يمكن قراءته بعدها — نسخة الاسترداد المشفّرة هي الطريق الوحيد لاستعادة نفس المفاتيح.
3. **النشر:** تلقائي من `main` (§4)؛ أو يدوياً للطوارئ: `scripts/setup/railway-deploy.sh --commit <SHA مراجَع على main>`.
   التحقق دون نطاق عام: سجلات النشر و`railway ssh`.
4. **بوابة التعريض العام (SC-18):** فحص جديد قبل التعريض **و**قرار المالك لكل ثغرة حرجة ([السجل §2](../security/vulnerability-register.md#2-سجل-الثغرات-الحرجة-critical): معالجة أو تصنيف لكل ثغرة). بعد ذلك فقط:
   `librechat` → Settings → Networking → **Generate Domain** → المنفذ **3080** (أو `railway domain --service librechat --port 3080`). لا نطاق مخصص (DNS) دون قرار منفصل.
5. Backups لكل خدمة: **Daily + Weekly**.
6. أول مسؤول: `railway ssh --service librechat` ثم أمر `create-user` ([deployment.md §3](../operations/deployment.md#3-إنشاء-أول-مسؤول-كل-البيئات)).
7. راجع اختبارات القبول **المحدّثة** RW1–RW13 وAD01/AD02 في #15؛ RW14 التاريخي superseded بـ ADR-0010. حدّث `CURRENT_STATE.md` بالأدلة عبر PR.
