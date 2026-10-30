# ADR-0019 — الدخول عبر Google لقائمة مختبرين في Railway `dev`

| Field | Value |
|---|---|
| Status | **Deprecated** — ألغاه المالك 2026-10-25 في جلسة Claude Code Cloud («الغ تفعيل الدخول والتسجيل بقوقل وخله الدخول والتسجيل بالوضع الافتراضي»)، قبل وضع مفتاحي Google ودخول أي مختبر. كان **Accepted** في اليوم نفسه (#202) |
| Date | 2026-10-25 |
| Deciders | مالك المشروع (@faenazi)؛ الإعداد والفحوص هندسية (الوكيل، ADR-0009) |
| Related | [#201](https://github.com/faenazi/ef-ai-workspace/issues/201)؛ FR-001 AC-2/AC-3، FR-014؛ SC-10، SC-17؛ OD-05؛ ADR-0008، ADR-0009، ADR-0010؛ [#16](https://github.com/faenazi/ef-ai-workspace/issues/16) (R-09) |

> **ملغى.** أُرجع الإعداد كاملاً إلى ما قبل #202:
> - التسجيل الذاتي والدخول الاجتماعي مغلقان (SC-10).
> - الحسابات ينشئها المسؤول بـ `create-user`.
>
> لم يُضبط `GOOGLE_CLIENT_ID` ولا `GOOGLE_CLIENT_SECRET` على Railway، ولم ينشأ أي حساب عبر Google. بقي هذا السجل للتاريخ، وأي إعادة تفعيل تحتاج قراراً جديداً.

## Context

- قبل هذا القرار لا يدخل المنصة إلا حساب ينشئه المسؤول بـ `create-user`. التسجيل الذاتي والدخول الاجتماعي مغلقان (SC-10).
- المالك يريد أن يدخل المختبرون بأنفسهم من الجوال، دون أن ينشئ لهم المسؤول حسابات واحداً واحداً.
- ما في LibreChat v0.8.8 (من المصدر عند الوسم):
  - `api/server/routes/config.js`: زر Google يظهر فقط حين `ALLOW_SOCIAL_LOGIN=true`، و`GOOGLE_CLIENT_ID` و`GOOGLE_CLIENT_SECRET` موجودان.
  - `api/strategies/socialLogin.js`: الحساب الجديد يُنشأ فقط مع `ALLOW_SOCIAL_REGISTRATION=true`. ويأخذ دور `USER`.
  - إن طابق بريد Google حساباً محلياً موجوداً، يُرفض الدخول (`AUTH_FAILED`) ولا يُربط الحسابان.
  - `registration.allowedDomains` يُطبَّق على نموذج البريد وعلى Google معاً، وعلى النطاق لا على البريد الواحد.
  - `api/server/services/AuthService.js`: دون خدمة بريد يُعتبر أي بريد يُكتب في نموذج التسجيل مؤكَّداً، فلا يثبت النموذج ملكية البريد.
- تطبيق Google OAuth في حالة *Testing* لا يقبل إلا *Test users* يضيفهم صاحب التطبيق في Google Cloud Console (حتى 100).

## Decision

1. **الدخول والتسجيل الذاتي عبر Google** للمختبرين فقط:
   - في `infrastructure/common/librechat.env`: `ALLOW_SOCIAL_LOGIN=true` و`ALLOW_SOCIAL_REGISTRATION=true` و`GOOGLE_CALLBACK_URL=/oauth/google/callback`.
   - في `librechat.yaml`: `registration.socialLogins: ['google']`.
   - القائمة يملكها المالك: التطبيق يبقى في *Testing*، والمختبر يُضاف أو يُزال من *Test users*. نشر التطبيق (*In production*) يفتح الدخول لأي حساب Google، وهو قرار مالك جديد.
2. **نموذج التسجيل بالبريد يبقى مغلقاً** (`ALLOW_REGISTRATION=false`). الدخول بالبريد وكلمة المرور يبقى للحسابات التي ينشئها المسؤول.
3. **Railway `dev` وحده:**
   - `GOOGLE_CLIENT_ID` و`GOOGLE_CLIENT_SECRET` سرّان بـ `preserve()` في `.railway/railway.ts`، يضعهما المالك من لوحة Railway.
   - Compose (Windows وUbuntu) يتركهما فارغين، فلا يظهر الزر هناك.
4. **لا حدود استهلاك جديدة** (قرار المالك؛ SC-17 يبقى مفتوحاً). حد upstream للتسجيل (5 حسابات في الساعة لكل IP) وحد الدخول (7 كل 5 دقائق) كما هما.

## Rationale

- قائمة *Test users* في Google هي الوسيلة الوحيدة المتاحة الآن لقائمة مختبرين حقيقية:
  - Google يثبت ملكية البريد.
  - المالك يدير القائمة من الجوال دون PR.
- **إعدادات قياسية في upstream بلا تعديل كود** (ADR-0006 المستوى 1)، ويُرجع عنها بمتغيرين.
- الملف المشترك يبقى واحداً لكل البيئات (ADR-0008)، والفرق بين البيئات في الأسرار وحدها.

## Alternatives considered

- **فتح نموذج البريد لأي شخص:** مرفوض. لا تحقق من البريد، والرابط عام، ولا حدود للرسائل، فالتكلفة مفتوحة.
- **حصر النموذج بنطاق (`allowedDomains`):** مرفوض. أي شخص يكتب بريداً من النطاق، والفلتر نفسه يمنع مختبري Gmail من Google.
- **خدمة بريد (SMTP) للتأكيد:** مؤجل. تحتاج مزوّداً وتكلفة، ولا تصنع قائمة مختبرين.
- **Entra ID الآن:** غير ممكن. لا tenant معتمد ولا بيئة داخل المملكة (OD-05، #17). يبقى هدف M6.

## Consequences

- **مخاطر قبلها المالك:**
  - **هويات حقيقية على Railway:** الاسم والبريد وصورة الحساب من Google تُخزَّن في MongoDB على Railway خارج المملكة.
    - المسموح: حسابات Google شخصية أو تجريبية.
    - الممنوع: بريد الصندوق، ودليل الموظفين، وأي محتوى حقيقي (OD-05، القاعدة 2 في `AGENTS.md`).
  - **تعريض أوسع للرابط العام** بينما قرار R-09 (#16) معلّق: أي مختبر مضاف يصل إلى الواجهة كاملة بدور `USER`.
  - **التكلفة:** كل مختبر يستهلك من رصيد Qwen بلا سقف لكل مستخدم.
- **الرجوع:**
  - حذف المتغيرين من Railway يخفي الزر فوراً بعد إعادة التشغيل.
  - أو `ALLOW_SOCIAL_*=false` في الملفين ثم `railway config apply`.
  - الحسابات التي أُنشئت تبقى في MongoDB وتُحذف يدوياً إن لزم.
- **الخروج:** Entra ID OIDC في M6 يحل محل هذا القرار (FR-001 AC-3).
- الفحوص تتوقع الآن: الدخول الاجتماعي مفعّل، والتسجيل بالبريد مغلق، وسرّا Google بـ `preserve()`، والـ callback مساراً نسبياً.

## Verification

- `Tested (cloud session)`:
  - `compose_checks.py` و`railway_checks.py`.
  - `negative-checks.sh`: N34 سر Google نصاً حرفياً، وN35 عنوان callback خارجي.
  - `compose-stack.sh` T13: لا زر Google دون المفتاحين.
  - `railway-emulation.sh`:
    - R16: `googleLoginEnabled` و`socialLogins: ["google"]`.
    - R47: `GET /oauth/google` يعيد 302 إلى `accounts.google.com` مع `redirect_uri` على نطاق Railway، بمفتاحين وهميين.
  - R17 وT14: `POST /api/auth/register` يبقى مرفوضاً.
  - Playwright على صورة Railway المشتقة بمفتاحين وهميين، بالجوال والكمبيوتر وبالعربية والإنجليزية:
    - الزر «تسجيل الدخول بواسطة Google»، ولا رابط «إنشاء حساب».
    - الضغط عليه يصل إلى `accounts.google.com` مع الـ callback الصحيح.
- **عند المالك من الجوال** بعد إضافة المفتاحين:
  - مختبر مضاف يدخل ويُنشأ حسابه بدور `USER`.
  - بريد غير مضاف يرفضه Google.
- الحالة المنشورة تُسجَّل في `project/CURRENT_STATE.md` فقط.
