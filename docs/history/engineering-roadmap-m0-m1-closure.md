# السجل الهندسي: إغلاق M0/M1/M1.1 ومواءمة الميثاق الأصلي

> **سجل تاريخي (أُرشف 2026-10-20، [#75](https://github.com/faenazi/ef-ai-workspace/issues/75)); ليس حالة حالية ولا خطة.**
> المصدر: قوائم القبول في `project/ROADMAP.md` كما كانت عند `main@8f40476`. الخطة الحية: [project/ROADMAP.md](../../project/ROADMAP.md)؛
> الحالة الحية: [project/CURRENT_STATE.md](../../project/CURRENT_STATE.md).

## مواءمة مع الميثاق الأصلي

ميثاق `CLAUDE.md` الأصلي (commit `11e80e2`) استخدم ترقيماً مختصراً (M1–M5). موجّه M0 اللاحق اعتمد الترقيم M0–M8
ويحل محله. المحتوى محفوظ:

| الميثاق الأصلي | الترقيم المعتمد الحالي |
|---|---|
| M1 foundation (Compose، ADRs، CI، .env.example) | M0 (الحوكمة، ADRs، CI) + M1 (Compose، .env.example) + M1.1 (استضافة متعددة البيئات) |
| M2 branding & bilingual | M2 |
| M3 LLM integrations, Agents, Skills, RAG, Artifacts | M3 + M4 + M5 |
| M4 security hardening, SSO, governance | M6 |
| M5 RFP assistant & integrations | M7 |
| — | M8 Pilot & production readiness (جديد) |

## معايير القبول كما أُغلقت

### M0 — Repository Foundation & Governance — ✅ مكتملة (PR [#9](https://github.com/faenazi/ef-ai-workspace/pull/9)، دُمج 2026-10-17، `0eab526`)

- [x] مراجعة المحتوى الحالي وتحليل الفجوات ([تقرير M0](reports/M0-delivery-report.md))
- [x] نقاط دخول: README، AGENTS.md، CLAUDE.md (يستورد AGENTS.md)، CONTRIBUTING، SECURITY، CHANGELOG
- [x] توثيق المنتج والمعمارية وADRs والتصميم والأمن والتشغيل والجودة
- [x] ROADMAP و CURRENT_STATE و RELEASE_PLAN
- [x] قوالب GitHub، CODEOWNERS، Dependabot، CI وفحص الأسرار
- [x] مهارات تطوير مُتحقق منها، منفصلة عن مهارات المنصّة
- [x] فحوصات CI ناجحة على الـ PR — لمرحلة M0 فقط يُقبل بديلاً عنها دليل جلسة السحابة وفق الاستثناء المعتمد
      [CI-EX-01](ci-exceptions-2026-10.md#ci-ex-01--github-actions-غير-متاح-لمرحلة-m0)
      (لا يُعتبر تحققاً مستقلاً؛ لا ينطبق على مراحل لاحقة دون اعتماد جديد)
- [x] Pull Request مفتوح للمراجعة، وموافقة مالك المشروع ودمجه
- [x] الأعمال المؤجلة والاعتماديات موثقة (Issues)

### M1 — LibreChat Platform Foundation — ✅ مكتملة (PR [#12](https://github.com/faenazi/ef-ai-workspace/pull/12)، دُمج 2026-10-18، `0db80d9`؛ Issue [#2](https://github.com/faenazi/ef-ai-workspace/issues/2))

> الاسم الأصلي «LibreChat & Coolify Foundation». هدف Coolify **مُستبدل** بـ ADR-0008؛ المسارات `infrastructure/coolify/` أدناه نُقلت
> إلى `infrastructure/common/` و`infrastructure/compose/` (معايير القبول تبقى كما تحققت).

**النطاق:** `infrastructure/coolify/` (compose + `.env.example` + `librechat.yaml`)، LibreChat + MongoDB فقط
(Meilisearch مؤجل إلى M3 بقرار OD-02 #4؛ RAG إلى M4)، تحقق آلي للإعداد، smoke test في السحابة، توثيق نشر Coolify،
ADR-0007 لتثبيت الإصدار.

**خارج النطاق:** نشر فعلي على VPS دون موافقة وتوفر D-01/D-02، ربط مزوّد نماذج (M3)، SSO (M6)، الهوية (M2).

**معايير القبول** (الأدلة: [تقرير M1](reports/M1-delivery-report.md)):

- [x] الصور مثبتة بـ tag + digest مُتحقق منها من السجل الرسمي (2026-10-18) — ADR-0007 **Accepted** (بيانات اصطناعية/عرض فقط، #11)
- [x] `docker compose config` ينجح بملف بيئة كامل، و**يرفض** `.env.example` غير المعبأ (حماية مقصودة بدل قيم وهمية قابلة للنشر)
- [x] فحص آلي يفشل إذا نشرت أي خدمة منفذاً في `compose.yaml` (`compose_checks.py`)
- [x] MongoDB بمصادقة ومستخدم أقل امتياز؛ لا كلمات مرور افتراضية؛ الأسرار عبر `${VAR:?}`
- [x] Healthchecks لكل خدمة؛ `GET /health` ينجح في smoke test داخل السحابة
- [x] volumes مسماة موثقة؛ نسخ احتياطي واستعادة مُختبران (فقدان كامل للـ volumes)
- [x] `ALLOW_REGISTRATION=false` افتراضياً مع إجراء مُختبر لإنشاء أول مسؤول
- [x] توثيق ربط نموذج عبر `${ENV_VAR}` دون كشف بيانات الاعتماد
- [x] Dependabot `docker-compose` مُعدّ (تشغيله على GitHub غير متحقق)
- [x] تعليمات تراجع، وتحديث CURRENT_STATE بالأدلة
- [x] GitHub CI أخضر **أو** اعتماد المالك لاستثناء CI-EX-02 (#10) — CI-EX-02 **Approved** لـ PR #12 فقط
      ([#11](https://github.com/faenazi/ef-ai-workspace/issues/11))؛ الأدلة `Tested (cloud session)` وليست CI مستقلاً
- [x] مراجعة المالك ودمج PR M1 — PR #12، 2026-10-18 (`0db80d9`)
- [ ] ~~M1.1 — أول نشر على Coolify ([#13](https://github.com/faenazi/ef-ai-workspace/issues/13))~~ — **مُستبدل** بـ M1.1 أدناه (#13 و#6 أُغلقا)

> **تدقيق حالة المراحل (2026-10-19):**
> [Foundation Closure Audit](reports/2026-10-19-foundation-closure-audit.md).
> M0/M1 مكتملتان حسب نطاقهما واختبارات cloud-session السابقة؛ M1.1 Phase A مكتملة
> وPhase B **لم تغلق**، وR0.1 الأساس منشور لكن بوابة الإغلاق مفتوحة حتى استيفاء أدلة #15/#17.

### M1.1 — Multi-Environment Hosting & First Controlled Railway Deployment — المرحلة أ مدموجة، المرحلة ب بدأت على Railway مع بقاء اختبارات غير منفذة ([#15](https://github.com/faenazi/ef-ai-workspace/issues/15))

**النطاق:** [ADR-0008](../architecture/adr/0008-multi-environment-hosting-railway-windows-ubuntu.md) — إعداد مشترك (`infrastructure/common/`)،
Compose لـ Windows وUbuntu (Caddy HTTPS)، Railway IaC (`.railway/railway.ts`) وصور مشتقة صغيرة، سكربتات الإعداد والأسرار، فحوصات
`compose_checks.py`/`railway_checks.py`، smoke tests للبيئات الثلاث، فحص صور report-only، إزالة Coolify من المعمارية النشطة.
**خارج النطاق:** M2/M3، بيانات حقيقية، DNS/نطاقات مخصصة، إنتاج.

**المرحلة أ — الإعداد والتحقق (PR [#18](https://github.com/faenazi/ef-ai-workspace/pull/18)) — Merged 2026-10-18 (`bccd408`):**

- [x] ADR-0008؛ ADR-0004 → Superseded؛ #13 و#6 مُغلقان بإحالة؛ Issues جديدة #15 #16 #17
- [x] Railway IaC بالمسار المدعوم (`railway.ts`، SDK مثبت)، لا Config as Code (deprecated)
- [x] MongoDB خاص (لا TCP proxy/نطاق)، مستخدم أقل امتياز، volume واحد لكل خدمة، تخطيط تخزين مُختبر، LibreChat كـ non-root
- [x] Windows: Compose loopback + مساعد PowerShell (init/up/down/restart/backup/restore/reset)؛ ترخيص Docker Desktop موثّق (D4).
      *(المساعد ومسار Docker Desktop أُزيلا بقرار المالك في 2026-10-20، #75.)*
- [x] Ubuntu: Compose + Caddy HTTPS (CA مؤسسية/internal/ACME)، تقوية، نسخ، ترقية، تراجع، نقاط مراقبة
- [x] تحقق `Tested (cloud session)`: run-all، compose local 37/37، on-prem 43/43، محاكاة Railway 30/30 (+2 SKIP: IPv6)، مساعد Windows 10/10
- [x] قرارات المالك D1–D4 وسياسة SC-18 (D5) معتمدة ومُنفّذة في المستودع ([#16](https://github.com/faenazi/ef-ai-workspace/issues/16)) — اعتماد سياسات، ليس تفويض نشر
- [x] D2 المعدّل: لا GitHub Actions — بوابة جودة يدوية على SHA النهائي (DoD)؛ نشر Railway يدوي فقط (لا مصدر GitHub، `railway-deploy.sh`)؛ اختبارات سلبية آلية. *(لاحقاً: النشر التلقائي ADR-0010، وبوابة الجودة لكل PR استُبدلت بتحقق مناسب للمهمة ADR-0011 — 2026-10-19)*
- [x] دمج PR #18 بقرار المالك (@faenazi) في 2026-10-18T21:37Z — squash `bccd408`، شجرته مطابقة لرأس الـ PR `cfecb5b`

**المرحلة ب — التحقق في البيئات المستهدفة (بدأت على Railway `dev` في 2026-10-19):**

> **تحديث حالة لا يمحو التاريخ:** التحقق من أول `config apply` ونشر LibreChat/MongoDB والرابط العام
> وautodeploy من `main` مسجل في [سجل الحالة المؤرشف](2026-10-20-current-state-ledger.md) و[#15](https://github.com/faenazi/ef-ai-workspace/issues/15).
> قرار النشر اليدوي السابق استبدله [ADR-0010](../architecture/adr/0010-railway-dev-autodeploy-from-main.md).
> **المتبقي:** بعض RW checks والنسخ وحد الإنفاق، وWindows/Ubuntu الحقيقي في #17.

- [x] أول `railway config apply` ونشر عملي وautodeploy من `main` في Railway `dev` ببيانات اصطناعية موثقة (#15 وADR-0010).
- [ ] استكمال اختبارات RW المتبقية، نسخ volume، حد الإنفاق ولوحة الضبط في Railway؛ حالة كل بند موثقة في CURRENT_STATE و#15.
- [ ] تشغيل قبول على Windows 11 حقيقي وخادم Ubuntu ([#17](https://github.com/faenazi/ef-ai-workspace/issues/17))

### M2–M8 — المواءمة مع خارطة الإصدارات الجديدة

تتوزع **نتائج المستخدم** على R0.2 (M3 قبل اكتمال M2)، R0.3 (M2)، R0.4 (Pilot من M8 مع ضوابط M6)، R0.5 (M4/M5)، R0.6 (M7)،
R1.0 (M6/M8). لا يؤجل الأمن إلى الإصدار الأخير؛ راجع [خارطة المنتج المعتمدة](planning-2026-10-19/PRODUCT_ROADMAP.md).
معايير القبول التفصيلية تُكتب في Issue كل مرحلة عند بدئها، مستندة إلى FR/NFR المرتبطة في
[functional-requirements.md](../product/functional-requirements.md) و[non-functional-requirements.md](../product/non-functional-requirements.md).
