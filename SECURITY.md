# السياسة الأمنية (Security Policy)

## الإبلاغ عن ثغرة

- **لا تنشر تفاصيل الثغرة في Issue أو PR أو تعليق.**
- أبلغ مالك المشروع مباشرة (@faenazi) عبر قناة خاصة، أو استخدم
  [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  إن كانت مفعّلة للمستودع.
- قناة الإبلاغ الأمني الرسمية لصندوق البيئة وجهات التصعيد: **TBD**.
- ثغرات LibreChat نفسه تُبلَّغ upstream وفق سياسة LibreChat الأمنية.

## القواعد الإلزامية

1. **لا أسرار في Git** — مفاتيح API، كلمات مرور، شهادات، tokens. القوالب `*.example` بقيم وهمية فقط.
   `gitleaks` يفحص تاريخ Git كاملاً وشجرة العمل عبر `scripts/validate/run-all.sh`: في التطوير عند التغييرات التي قد تمس الأسرار،
   وإلزامياً في بوابات الإنتاج ([ADR-0011](docs/architecture/adr/0011-production-only-quality-gates.md))؛ GitHub Actions غير مستخدم
   (`security.yml` للاستخدام الاختياري).
2. **بيانات اصطناعية فقط** في التطوير والعرض. لا بيانات موظفين حقيقية ولا مستندات سرية لصندوق البيئة على أي خادم أو
   بيئة غير معتمدة أو واجهات نماذج خارجية.
3. **لا منافذ مكشوفة** لـ MongoDB أو البحث أو RAG أو قواعد المتجهات أو لوحات الإدارة؛ HTTPS إلزامي للوصول الخارجي.
4. **أقل امتياز** للأسرار وصلاحيات GitHub Actions والأدوات وخوادم MCP.
5. **إصدارات مثبتة** للصور والـ Actions والأدوات (tag + digest / SHA / hash).
6. **لا ادعاء امتثال** لأي إطار تنظيمي أو أمني دون تحقق واعتماد رسمي.

## إذا تسرب سر

1. ألغِ/دوّر السر فوراً لدى المزوّد — حذفه من Git لا يكفي.
2. أبلغ مالك المشروع.
3. اتبع [docs/operations/runbook.md](docs/operations/runbook.md#5-الاستجابة-للحوادث--requirement).

## مراجع

- سجل الضوابط وحالتها: [docs/security/security-baseline.md](docs/security/security-baseline.md)
- تصنيف البيانات والتعامل معها: [docs/security/data-handling.md](docs/security/data-handling.md)
