# ADR-0024 — إغلاق التسجيل الذاتي في LibreChat

| Field | Value |
|---|---|
| Status | **Accepted** — قرار المالك 2026-10-27 في جلسة Claude Code Cloud: «وقف التسجيل الان» ([#245](https://github.com/faenazi/ef-ai-workspace/issues/245)) |
| Date | 2026-10-27 |
| Deciders | مالك المشروع (@faenazi)؛ الإعداد والفحوص هندسية (الوكيل، ADR-0009) |
| Related | يحل محل ADR-0020؛ FR-001، FR-014؛ SC-10، SC-17؛ ADR-0008، ADR-0009؛ [#39](https://github.com/faenazi/ef-ai-workspace/issues/39) |

## Context

- ADR-0020 فتح نموذج التسجيل في LibreChat لكل البيئات بلا حدود استهلاك.
- لا حدود للرسائل أو التزامن ولا رصيد لكل مستخدم (#39)، فأي حساب يستهلك من رصيد Qwen Cloud بلا سقف.
- طلب المالك إيقاف التسجيل فوراً.
- **في LibreChat v0.8.8** (من المصدر عند الوسم):
  - `api/server/middleware/validateRegistration.js`: مسار `/api/auth/register` يرد 403 ما لم يكن `ALLOW_REGISTRATION` مفعّلاً (أو الطلب بدعوة).
  - `api/server/routes/config.js`: `registrationEnabled` يتبع المتغير نفسه، فيختفي رابط التسجيل من صفحة الدخول.

## Decision

1. **`ALLOW_REGISTRATION=false`** في `infrastructure/common/librechat.env`، ومرآته في `.railway/railway.ts`، لكل البيئات (ADR-0008).
   - `compose_checks.py` يثبّت القيمة، فأي انحراف عنها يُرفض (N12، N14).
2. **الحسابات:** ينشئها المسؤول بـ `npm run create-user` ([deployment.md §3](../../operations/deployment.md#3-إنشاء-أول-مسؤول-كل-البيئات)). الحسابات الموجودة تبقى وتدخل بالبريد وكلمة المرور.
3. **بلا تغيير:** الدخول الاجتماعي مغلق، واستعادة كلمة المرور مغلقة (لا خدمة بريد).

## Rationale

- يوقف استهلاكاً بلا سقف من حسابات مجهولة فوراً، دون انتظار حدود الاستهلاك (#39).
- يحصر ما بعد الدخول، وثغراته ومنها R-09 المعلّقة (#16)، بمستخدمين معروفين.
- متغير واحد مدعوم في LibreChat، يُطبَّق بـ `config apply` ويُرجع بالطريقة نفسها.

## Alternatives considered

- **إبقاء التسجيل مع حدود استهلاك ورصيد:** يحتاج قيماً يقررها المالك (#39)؛ لم يُختر لأن المطلوب الإيقاف الآن.
- **حصر التسجيل بنطاق بريد:** لا نطاق معتمد في `dev`، والبريد لا يُتحقق منه بلا خدمة بريد.

## Consequences

- لا يدخل المنصة إلا من أنشأ له المسؤول حساباً، فيعود الاستهلاك محصوراً بمستخدمين معروفين.
- الحسابات التي سجّلت نفسها أثناء ADR-0020 تبقى؛ مراجعتها أو حذفها قرار مالك (#245).
- **الرجوع:** `ALLOW_REGISTRATION=true` في الملفين ثم `railway config apply`، بقرار مالك جديد.
- **الخروج:** Entra ID OIDC في M6 (FR-001 AC-3).

## Verification

- `Tested (cloud session)`: `compose_checks.py` و`railway_checks.py` وN12/N14 تتوقع القيمة المغلقة؛ T13/T14 وR16/R17 وM06 تتوقع `registrationEnabled: false` و403.
- `Verified (target environment)`: على Railway `dev` بعد `config apply`، `/api/config` يعيد `registrationEnabled: false` ومسار التسجيل 403 (السجل في #15).
