# ترقية LibreChat (LibreChat Upgrade)

| الحقل | القيمة |
|---|---|
| النطاق | ترقية LibreChat في واجهة Railway المبنية من المصدر ([ADR-0013](../architecture/adr/0013-arabic-web-client-build.md)) وصورة Compose |
| الأداة | [`scripts/upgrade/librechat-upgrade-check.sh`](../../scripts/upgrade/librechat-upgrade-check.sh) (قراءة فقط، لا تغيّر المستودع) |
| ذات صلة | [دليل التشغيل §3 و§4](runbook.md#3-الترقية-upgrade)، [ADR-0012](../architecture/adr/0012-temporary-security-patch-layer.md)، ترقية MongoDB في [#62](https://github.com/faenazi/ef-ai-workspace/issues/62) |

## 1. ما الذي يجعل الترقية عملاً

LibreChat نفسه لا يتغير داخل الصورة إلا بثلاثة أشياء في `infrastructure/common/client/`، والأداة تفحصها كلها:

- **التعديلات البرمجية** (`patches/*.patch`): تُطبَّق بالترتيب على مصدر الإصدار المثبّت؛ أي تعديل لا ينطبق يُفشل البناء.
- **الترجمة** (`ar.json`): البناء يرفض مفتاحاً لم يعد في الإنجليزية، أو متغيرات `{{…}}` تغيّرت، أو تغطية أقل من 100%.
- **الهوية** (`brand/`): `build.sh` يستبدل ملفات upstream بالاسم نفسه ويُفشل البناء إن اختفى أحدها.

وخارجها: طبقة الترقيع الأمني (ADR-0012) التي يُفشل حارسُها البناء عند أول صورة أحدث، و`version` في `librechat.yaml`.

## 2. الخطوات

1. **الفحص:** `scripts/upgrade/librechat-upgrade-check.sh v0.8.9 report.md` (tag أو فرع أو commit).
   - التقرير يذكر digest الصورة، ونتيجة كل تعديل (ينطبق كما هو / دمج ثلاثي نظيف / تعارض في ملفات مسمّاة).
   - ويذكر مفاتيح الترجمة المحذوفة والجديدة والمتغيرة، وأسماء الأصول، ونسخة Node للبناء، ونسخة الإعداد، وحاجة طبقة ADR-0012.
   - المدة: ثوانٍ إلى دقيقة. يُرفق التقرير بـ Issue الترقية.
2. **تثبيت الإصدار** في PR واحد:
   - `infrastructure/railway/librechat.Dockerfile`: `commit=` في مرحلة `source`، و`FROM ghcr.io/librechat-ai/librechat:<tag>@<digest>` (من التقرير)، وصورة Node في مرحلة `client` إن غيّرها upstream.
   - `infrastructure/compose/compose.yaml`: الصورة نفسها بالـ digest نفسه (`railway_checks.py` يفشل إن اختلفا).
3. **التعديلات:** في نسخة عمل من المصدر الجديد تُطبَّق التعديلات بالترتيب.
   - ما ينطبق كما هو يبقى.
   - ما يندمج دمجاً ثلاثياً نظيفاً يُعاد توليده من `git diff` بالترويسة نفسها.
   - ما يتعارض يُعاد تنفيذه على الكود الجديد، أو يُحذف إن أصلحه upstream (التقرير يقول «already in upstream»).
4. **الترجمة:** تُحذف من `ar.json` المفاتيح التي لم تعد موجودة، وتُصحَّح القيم التي تغيّرت متغيراتها. وتُترجم المفاتيح الجديدة التي لا يغطيها عربي upstream، وفق [المسرد](../design/arabic-glossary.md).
5. **ADR-0012:** يُحذف من الطبقة كل بند يقول التقرير إن upstream أصلحه، وتُحذف الطبقة كلها حين لا يبقى بند، ويُحدَّث [سجل الثغرات](../security/vulnerability-register.md).
6. **الاختبار** في جلسة سحابية:
   - بناء الصورة الكاملة (نسخة الاختبار بشهادة الوكيل).
   - `tests/integration/mock_chat.py`، و`tests/smoke/railway-emulation.sh`، وفحص Trivy (`scripts/validate/image-scan.sh`، إلزامي عند تغيّر الـ digest).
   - فحوص Playwright للواجهة بالعربية والإنجليزية، على الجوال والكمبيوتر.
   - `tests/ui/pwa_install.cjs`: الـ manifest الجديد وأيقوناته وحكم Chromium في قابلية التثبيت على الجوال ([§14](../quality/concept1-interface-test-cases.md#14-تثبيت-التطبيق-على-الجوال-pwa-232)).
   - `tests/ui/mobile_app.cjs`: حواف iPhone وأهداف اللمس وزر التثبيت وشريط النسخة الجديدة ([§16](../quality/concept1-interface-test-cases.md#16-إحساس-تطبيق-الجوال-238)).
7. **النشر والتراجع:**
   - نسخة احتياطية لـ volumes Railway قبل الدمج؛ الدمج ينشر `dev` تلقائياً (ADR-0010)، ثم التحقق من سجل البناء (تطبيق كل التعديلات، وتغطية 100%) وسجل التشغيل.
   - التراجع: revert للـ PR (يعود الـ digest السابق والواجهة السابقة)، و[دليل التشغيل §4](runbook.md#4-التراجع-rollback) إن غيّرت الترقية البيانات.

## 3. نتيجة آخر فحص

نتائج تشغيل الأداة على الإصدارات القادمة تُسجَّل في Issue الترقية، لا هنا (آخرها: [#118](https://github.com/faenazi/ef-ai-workspace/issues/118)).
