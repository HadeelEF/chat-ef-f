# ADR-0010 — النشر التلقائي على Railway `dev` من فرع `main`

| Field | Value |
|---|---|
| Status | Accepted — نتيجة «بوابة الجودة قبل الدمج» **معدَّلة بـ [ADR-0011](0011-production-only-quality-gates.md)** (2026-10-19) |
| Date | 2026-10-19 |
| Deciders | مالك المشروع (@faenazi) — تعليمات صريحة في جلسة Claude Code Cloud |
| Related | ADR-0008، ADR-0009، ADR-0011؛ #15، #16 (D2 المعدّل)؛ [railway.md §4](../../operations/railway.md#4-النشر--تلقائي-من-main-adr-0010) |

> **تعديل 2026-10-19 (ADR-0011):** لم تعد بوابة الجودة اليدوية شرطاً لكل دمج. الضابط قبل النشر التلقائي هو فهم الوكيل لأثر النشر
> وتحققه المناسب قبل دمج أي تغيير في watched paths (يُعامل كتغيير بنية تحتية). آلية النشر نفسها دون تغيير.

## Context

- D2 المعدّل في #16 (2026-10-18) جعل نشر Railway **يدوياً فقط**: الخدمتان بلا مصدر GitHub، والنشر بـ `scripts/setup/railway-deploy.sh`،
  لأن GitHub Actions غير مستخدم فلا يوجد CI ينتظره Railway.
- بعد ADR-0009 صار الوكيل يدمج وينشر على `dev` بنفسه، فالنشر اليدوي خطوة إضافية بعد كل دمج.
- قرار المالك (2026-10-19، نصاً): «فعل النشر التلقائي على railway لو صار اي تعديل على main branch».

## Decision

لبيئة Railway **`dev` فقط**:

1. الخدمتان `librechat` و`mongodb` مربوطتان في `.railway/railway.ts` بمصدر GitHub: المستودع `faenazi/ef-ai-workspace`، الفرع `main`،
   و**Wait for CI مُطفأ** (`checkSuites: false`) لعدم وجود GitHub Actions.
2. **Watch paths** لكل خدمة = ملف Dockerfile الخاص بها ومصادر `COPY` فيه فقط. أي push إلى `main` يغيّر ما يدخل في صورة خدمة يعيد
   بناءها ونشرها؛ تغييرات التوثيق والفحوصات وCompose لا تنشر شيئاً.
3. المتغيرات (سياسة `librechat.env` والأسرار) **لا** تُطبّق بالـ push: تبقى عبر `railway config plan/apply` (ADR-0009).
4. `railway_checks.py` يقبل هذا المصدر حرفياً فقط ويفرض تطابق watch paths مع مدخلات الـ Dockerfile؛ الاختبارات السلبية N01–N03 وN17
   ترفض فرعاً آخر أو Wait for CI أو مصدر صورة أو watch path ناقصاً.
5. `railway-deploy.sh` يبقى مسار الطوارئ والرجوع اليدوي.

يبقى بقرار المالك: أي بيئة غير `dev`، أي نطاق، الإنفاق، البيانات الحقيقية، والإنتاج (ADR-0009 كما هو).

## Rationale

الدمج إلى `main` يصبح هو النشر، فتختفي خطوة يدوية متكررة في مرحلة التطوير. وwatch paths تمنع إعادة تشغيل الخدمتين (مع توقف قصير،
لأن لكل خدمة volume) عند تغييرات لا تمس الصور.

## Alternatives considered

| البديل | سبب عدم الاختيار |
|---|---|
| إبقاء النشر اليدوي (D2 المعدّل) | رفضه المالك صراحة |
| نشر عند **أي** تغيير دون watch paths | كل دمج توثيقي يعيد تشغيل MongoDB وLibreChat (توقف قصير مع volumes) دون تغيير في الصورة |
| Wait for CI | يتطلب GitHub Actions، وهو غير مستخدم (D2 المعدّل) |
| تطبيق المتغيرات تلقائياً (workflow `railwayapp/config`) | يتطلب GitHub Actions وtoken في GitHub |

## Consequences

- **لا بوابة قبل النشر سوى بوابة الجودة اليدوية قبل الدمج:** ما يُدمج في `main` ويمس الصور يصل إلى الرابط العام خلال دقائق.
  لذلك تبقى بوابة الجودة على SHA الرأس النهائي (DoD) شرطاً لكل دمج.
- **توقف قصير** (عادةً أقل من دقيقتين) عند كل إعادة نشر لخدمة لها volume (توثيق Railway: Volumes reference).
- **يتطلب وصول Railway إلى المستودع الخاص:** Railway GitHub App مثبّت بصلاحية على `faenazi/ef-ai-workspace`، وحساب عضو في المشروع
  مربوط بـ GitHub بصلاحية contributor (توثيق Railway: Controlling GitHub Autodeploys). هذا إجراء المالك في GitHub/Railway.
- تغيير الـ digest في `compose.yaml` وحده لا يعيد النشر؛ المعتمد هو سطر `FROM` في Dockerfile الخدمة (الفحص يفرض تطابقهما).
- يُلغي قاعدة «لا مصدر GitHub» في AGENTS.md وrailway.md لبيئة `dev`؛ ADR-0008 يبقى Accepted فيما عدا ذلك.

## Verification

- Offline: `railway_checks.py` والاختبارات السلبية (17/17) ضمن `scripts/validate/run-all.sh`.
- Railway `dev`: `config plan` يُظهر المصدر وwatch paths؛ بعد `apply` يظهر المستودع والفرع في Settings → Source؛ أول push يمس صورة
  يُنشئ نشراً تلقائياً `SUCCESS`، وpush توثيقي لا يُنشئ نشراً. يُسجّل على #15.
