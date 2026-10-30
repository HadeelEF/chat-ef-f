# المساهمة (Contributing)

ينطبق هذا الدليل على البشر ووكلاء الذكاء الاصطناعي. السياسة التفصيلية للوكلاء في [AGENTS.md](AGENTS.md).

**خارطة الطريق المعتمدة:** [ROADMAP](project/ROADMAP.md) (الإصدارات R0.x وبوابات خروجها، المراحل M0–M8، ترتيب التنفيذ).
أي وكيل يبدأ من [START_HERE](project/START_HERE.md) ثم يتحقق من الـ Issues و`main` الحية.
`R0.x` نتائج منتج وليست Git tags؛ `M0–M8` مراحل هندسية محفوظة.

## 1. مبادئ

- المستودع هو المصدر الوحيد للحقيقة؛ GitHub Issues هي سجل الأعمال الوحيد.
- تغيير صغير ومركّز لكل PR، قابل للمراجعة من الهاتف.
- بيانات اصطناعية فقط؛ لا أسرار في أي commit أو Issue أو لقطة شاشة.

## 2. دورة العمل

1. **Issue:** اختر Issue موجودة ذات حالة Ready أو أنشئ واحدة دون تكرار؛ اذكر Product Release وEngineering M، الأولوية، FR/NFR، الاعتماديات والبوابات ومعايير القبول.
2. **فرع:** `feature/<scope>` · `fix/<scope>` · `docs/<scope>` · `chore/<scope>` من `main`.
3. **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat:` `fix:` `docs:` `ci:` `chore:` `refactor:` `test:`.
4. **تحقق مناسب للمهمة** (في بيئة السحابة) — نشاط هندسي وليس بوابة إلزامية
   ([ADR-0011](docs/architecture/adr/0011-production-only-quality-gates.md)، [DoD](docs/quality/definition-of-done.md)):
   التوثيق: مراجعة المحتوى والروابط؛ الوظائف: بناء/اختبار السلوك المتأثر؛ البنية التحتية أو الحساس أمنياً: أثر النشر والأمن والفحوصات ذات الصلة.

   ```bash
   python3 -m venv .venv && . .venv/bin/activate
   python -m pip install --require-hashes -r scripts/validate/requirements.txt
   python3 scripts/validate/repo_checks.py links adr   # quick docs check
   scripts/validate/run-all.sh                         # optional full suite (CI + Security workflow equivalent)
   ```

5. **Pull Request (مسودة):** املأ القالب باختصار: ما تغيّر، ما فُحص فعلاً، المخاطر، والتراجع. اربط الـ Issue (`Closes #N`).
6. **مراجعة:** مراجعة الفرق والآثار الأمنية (الوكيل يستخدم مهارة `review-changes`)؛ لا يُوسم فحص لم يُشغَّل بأنه ناجح.
7. **دمج (squash):** يدمج الوكيل PRs التطوير بتفويض [ADR-0009](docs/architecture/adr/0009-development-phase-agent-delegation.md)
   كما عدّله ADR-0011، ثم يحدّث الـ Issue و`CURRENT_STATE.md`. تغيير مدخلات صور Docker المراقَبة على `main` يعيد نشر Railway `dev`
   تلقائياً ([ADR-0010](docs/architecture/adr/0010-railway-dev-autodeploy-from-main.md)). الإنتاج والبيانات الحقيقية لهما بوابات
   واعتمادات منفصلة ([DoD §2](docs/quality/definition-of-done.md#2-الإنتاج--بوابات-الجودة-الرسمية-planned-قبل-أي-go-live)).

## 3. أين أضع المعلومة؟

| النوع | الموقع |
|---|---|
| مخرجات الإصدار وتسلسل التنفيذ والاعتماديات | `project/ROADMAP.md` (§2–§3، §6) |
| مهمة، خطأ، قرار مطلوب | GitHub Issue |
| متطلب جديد | `docs/product/functional-requirements.md` أو `non-functional-requirements.md` (معرّف جديد) |
| قرار معماري | ADR جديد في `docs/architecture/adr/` |
| حالة متحقق منها | `project/CURRENT_STATE.md` |
| تغيير ملحوظ | `CHANGELOG.md` (قسم Unreleased) |
| إجراء تشغيلي | `docs/operations/` |
| تعريف وكيل/مهارة للمنصّة | `ai/` |
| إجراء تطوير متكرر لوكلاء البرمجة | `.claude/skills/<name>/SKILL.md` |

## 4. لغة التوثيق

العربية للوثائق الموجهة للبشر حيث يفيد، مع الإبقاء على المصطلحات والمعرّفات التقنية بالإنجليزية. ملفات الوكلاء
(`AGENTS.md`, `CLAUDE.md`, المهارات) بالإنجليزية لتقليل الالتباس واستهلاك السياق.

## 5. إضافة مهارة تطوير

- مجلد `.claude/skills/<name>/` يحتوي `SKILL.md` بواجهة YAML محمولة: `name` (يطابق اسم المجلد، أحرف صغيرة وشرطات)
  و`description` (≤ 1024 حرفاً). مفاتيح أخرى مسموحة: `license`, `compatibility`, `metadata`, `allowed-tools`.
- يُكتشف تلقائياً في Codex عبر الرابط الرمزي `.agents/skills`.
- `repo_checks.py skills` يتحقق من الصيغة.
