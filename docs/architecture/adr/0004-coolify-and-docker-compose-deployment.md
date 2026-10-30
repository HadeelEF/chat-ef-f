# ADR-0004 — النشر عبر Coolify و Docker Compose

> **Superseded.** القرار الساري: [ADR-0008](0008-multi-environment-hosting-railway-windows-ubuntu.md) — Railway (عرض سحابي) وWindows المحلي وUbuntu في الموقع.
> مسار `infrastructure/coolify/` المذكور أدناه نُقل إلى `infrastructure/common/` و`infrastructure/compose/` (التاريخ في Git).

| Field | Value |
|---|---|
| Status | **Superseded by [ADR-0008](0008-multi-environment-hosting-railway-windows-ubuntu.md)** (2026-10-18) — كان Accepted 2026-10-17. لم يُنشر Coolify قط؛ النص أدناه محفوظ كسجل تاريخي |
| Date | 2026-10-17 |
| Deciders | مالك المشروع |
| Related | ADR-0005, NFR-PORT-01, docs/operations/deployment.md |

## Context

بيئة التطوير والعرض: Coolify ذاتي الإدارة على Ubuntu VPS. الـ VPS والنطاق والأسرار **غير مؤكدة الوجود بعد**.
متحقق منه من توثيق Coolify الرسمي (`coollabsio/coolify-docs`، 2026-10-17):

- Compose build pack من مستودع Git (يدعم webhooks) أو "Docker Compose Empty" للصق الملف.
- متغيرات سحرية: `SERVICE_URL_*`, `SERVICE_FQDN_*`, `SERVICE_PASSWORD_*`, `SERVICE_HEX_32_*`/`_64_`، و`${VAR:?}` لإلزام القيمة.
- التوصية: عدم نشر المنافذ (`ports:`)؛ وكيل Coolify يوجّه للنطاق والمنفذ الداخلي.
- فحوصات الصحة يجب تعريفها في ملف Compose.
- يوجد قالب LibreChat رسمي في Coolify، لكنه يستخدم صورة **dev** مثبتة على commit، و`ALLOW_REGISTRATION` مفعّل افتراضياً،
  و`POSTGRES_HOST_AUTH_METHOD=trust` — **لا يُستخدم كما هو**.

## Decision

1. ملف Compose خاص بالمشروع في `infrastructure/coolify/` (M1) يُنشر عبر Coolify Compose build pack من GitHub.
2. ملف Compose يبقى Compose قياسياً قابلاً للتشغيل خارج Coolify؛ المتغيرات السحرية لـ Coolify تُستخدم فقط عبر
   طبقة متغيرات موثقة يمكن استبدالها (ADR-0005).
3. لا منافذ منشورة لأي خدمة داخلية؛ فقط LibreChat يُكشف عبر وكيل Coolify مع HTTPS.

## Rationale

Coolify يوفر HTTPS ووكيلاً ونشراً من Git بتكلفة تشغيل منخفضة مناسبة لبيئة العرض، دون فقدان قابلية النقل.

## Alternatives considered

| البديل | سبب عدم الاختيار |
|---|---|
| Kubernetes | تعقيد غير مبرر للمرحلة الحالية؛ قد يُعاد تقييمه للإنتاج (OD-05) |
| قالب LibreChat الجاهز في Coolify | صورة dev، إعدادات افتراضية غير آمنة |
| Docker Compose يدوي على VPS | يفقد HTTPS المُدار والنشر من Git |

## Consequences

- النسخ الاحتياطي المجدول في Coolify لقواعد البيانات موثق لـ **Services**؛ لم نجد توثيقاً له في Compose **Applications** من Git →
  يلزم مسار `mongodump` مستقل يُختبر في M1/M6.
- أي ميزة Coolify خاصة تُوثق مع بديلها خارج Coolify.

## Verification

M1: `docker compose config` ناجح في CI، تشغيل محلي في بيئة السحابة مع healthchecks، ثم نشر تجريبي على Coolify **بعد** توفر D-01/D-02 وموافقة مالك المشروع.
