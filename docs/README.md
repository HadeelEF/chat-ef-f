# فهرس التوثيق (Documentation Index)

كل وثيقة لها غرض واحد ومالك واحد للمعلومة. إذا وجدت المعلومة نفسها في مكانين، فالمكان المذكور هنا هو المرجع.

## خريطة ملكية المعلومات

| النوع | الوثيقة المرجعية |
|---|---|
| الرؤية والمبادئ | [product/vision.md](product/vision.md) |
| **خارطة الطريق: الإصدارات R0.1–R1.0 وبوابات خروجها، المراحل M0–M8، ترتيب التنفيذ** | [ROADMAP](../project/ROADMAP.md) |
| **الحالة المتحققة الآن (لقطة بالأدلة)** | [CURRENT_STATE](../project/CURRENT_STATE.md) |
| **الدخول لأي جلسة تطوير** | [START_HERE](../project/START_HERE.md) |
| **السجل التاريخي** (تقارير التسليم، التخطيط الأصلي، سجلات الحالة القديمة؛ ليس حالة ولا سياسة) | [history/](history/README.md) |
| النطاق، الافتراضات، الاعتماديات (D-xx)، القرارات المفتوحة (OD-xx) | [product/scope.md](product/scope.md) |
| متطلبات الأعمال (BR-xx) | [product/BRD.md](product/BRD.md) |
| المتطلبات الوظيفية (FR-xxx) | [product/functional-requirements.md](product/functional-requirements.md) |
| المتطلبات غير الوظيفية (NFR-xxx) | [product/non-functional-requirements.md](product/non-functional-requirements.md) |
| المعمارية وقدرات LibreChat المتحقق منها | [architecture/overview.md](architecture/overview.md) |
| التصميم عالي المستوى | [architecture/HLD.md](architecture/HLD.md) |
| تدفقات البيانات وحدود الثقة | [architecture/data-flow.md](architecture/data-flow.md) |
| إعدادات الذكاء الاصطناعي الآمنة افتراضياً (الصلاحيات، الأدوات، أخطاء المزوّد) | [architecture/ai-safe-defaults.md](architecture/ai-safe-defaults.md) |
| القرارات المعمارية (السجل الوحيد) | [architecture/adr/](architecture/adr/README.md) |
| حوكمة الهوية البصرية | [design/brand-guidelines.md](design/brand-guidelines.md) |
| هيكل نظام التصميم وآليات LibreChat | [design/design-system.md](design/design-system.md) |
| معايير تجربة المستخدم (RTL/LTR، الجوال، الوصول) | [design/ux-standards.md](design/ux-standards.md) |
| واجهة «بصير» بعد الدخول: الفكرة 1 المعتمدة (#181) | [design/concept1-interface.md](design/concept1-interface.md) |
| تدقيقات التصميم: مصفوفة تطبيق الهوية (#42) وتدقيق العربية وRTL والوصول (#44) والاختبار الشامل للواجهة العربية (#127) | [design/audits/brand-implementation-matrix.md](design/audits/brand-implementation-matrix.md) · [design/audits/arabic-rtl-audit.md](design/audits/arabic-rtl-audit.md) · [design/audits/arabic-rtl-full-test.md](design/audits/arabic-rtl-full-test.md) |
| مسرد المصطلحات والترجمات العربية المقترحة (#44) | [design/arabic-glossary.md](design/arabic-glossary.md) |
| سجل الضوابط الأمنية وحالتها | [security/security-baseline.md](security/security-baseline.md) |
| سجل الثغرات وخطة معالجة الحرجة قبل 2026-11-18 | [security/vulnerability-register.md](security/vulnerability-register.md) · [security/cve-remediation-plan.md](security/cve-remediation-plan.md) |
| تصنيف البيانات والتعامل معها | [security/data-handling.md](security/data-handling.md) |
| البيئات والنشر | [operations/deployment.md](operations/deployment.md) |
| التشغيل (نسخ، ترقية، تراجع، حوادث) | [operations/runbook.md](operations/runbook.md) |
| ترقية LibreChat (أداة الفحص والخطوات) | [operations/librechat-upgrade.md](operations/librechat-upgrade.md) |
| تعريف الإنجاز والجاهزية، المسؤوليات، بوابات الإصدار والإنتاج | [quality/definition-of-done.md](quality/definition-of-done.md) |
| الاختبار وتقييم الذكاء الاصطناعي | [quality/testing-strategy.md](quality/testing-strategy.md) |
| معيار الأوضاع الثلاثة (الجودة والزمن والتكلفة والبحث، #211) | [quality/model-benchmark.md](quality/model-benchmark.md) |
| حالات اختبار صفحة الدردشة ونتائج تنفيذها (#133) | [quality/chat-page-test-cases.md](quality/chat-page-test-cases.md) |
| حالات اختبار رحلة الموظف في المحادثة على الكمبيوتر والجوال (#175) | [quality/chat-journey-test-cases.md](quality/chat-journey-test-cases.md) |
| حالات اختبار واجهة الفكرة 1 ونتائج تنفيذها (#181) | [quality/concept1-interface-test-cases.md](quality/concept1-interface-test-cases.md) |

**تقرير تدقيق إغلاق M0/M1/M1.1/R0.1:** [Foundation Closure Audit](history/reports/2026-10-19-foundation-closure-audit.md).

خارج `docs/`: الحالة والخطة في [project/](../project/ROADMAP.md) · سياسة الوكلاء [AGENTS.md](../AGENTS.md) ·
أصول الذكاء الاصطناعي للمنصّة [ai/](../ai/README.md) · الأمن [SECURITY.md](../SECURITY.md).

## مفردات الحالة الموحّدة

| السياق | القيم |
|---|---|
| التنفيذ | `Planned` → `Implemented` → `Configured` → `Tested` → `Verified` → `Approved`؛ `Blocked` |
| مهمة التسليم (Issue) | `Backlog` · `Ready` · `In Progress` · `In Review` · `Blocked` · `Done` — `Done` في GitHub ≠ `Verified (target environment)` |
| المتطلبات | `Draft` · `Approved` · `Deferred` · `Withdrawn` |
| القرارات (ADR) | `Proposed` · `Accepted` · `Superseded` · `Deprecated` |
| تحليل الفجوات | `EXISTING` · `COMPLETE` · `PARTIAL` · `MISSING` · `PLANNED` · `BLOCKED` |

## هيكل المستودع المستهدف (تدريجي)

المجلدات التالية **تُنشأ عند الحاجة الفعلية** (لا مجلدات فارغة):

| المسار | يُنشأ في | الغرض |
|---|---|---|
| `infrastructure/common/`, `infrastructure/compose/`, `infrastructure/railway/`, `.railway/` | M1/M1.1 (موجودة) | الإعداد المشترك، Compose (Windows/Ubuntu)، Railway IaC — [infrastructure/README.md](../infrastructure/README.md)، ADR-0008 |
| `scripts/setup/` | M1.1 (موجودة) | توليد ملفات البيئة والأسرار |
| `tests/smoke/`, `tests/integration/`, `tests/security/` | M1+ | اختبارات تشغيلية |
| `scripts/operations/` | M1/M6 | نسخ احتياطي واستعادة |
| `scripts/upgrade/` | M2 (موجودة) | فحص جاهزية ترقية LibreChat ([librechat-upgrade.md](operations/librechat-upgrade.md)) |
| `config/branding/`, `assets/brand/` | M2 | رموز وأصول الهوية المعتمدة |
| `ai/agents/`, `ai/skills/`, `ai/prompts/`, `ai/knowledge/`, `ai/evals/` | M5+ | أصول المنصّة |
| `integrations/mcp/`, `integrations/openapi/` | M5/M7 | عقود التكامل |
| `.claude/rules/` | عند الحاجة | قواعد Claude Code مقيّدة بالمسارات (`paths:`) |
| `docs/history/` | 2026-10-20 (موجودة) | وثائق توقفت عن وصف الوضع الحالي، تُنقل بـ `git mv` ولا تُعدَّل — [history/README.md](history/README.md) |
