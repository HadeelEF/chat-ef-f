# ADR-0003 — هندسة بمساعدة Claude Code Cloud مع سياسة AGENTS.md مشتركة

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-17 |
| Deciders | مالك المشروع (Claude Code Cloud معتمد؛ توافق Codex مطلوب مستقبلاً) |
| Related | ADR-0002 |

## Context

- التطوير الأولي عبر Claude Code Cloud؛ التوافق مع OpenAI Codex مطلوب مستقبلاً.
- متحقق منه (توثيق Claude Code الرسمي، 2026-10-17): Claude Code يقرأ `AGENTS.md` أصلياً **فقط إذا لم يوجد `CLAUDE.md`**؛
  الطريقة الموصى بها للمشاركة هي سطر `@AGENTS.md` داخل `CLAUDE.md` (حد أقصى 4 مستويات استيراد، هدف < 200 سطر).
- متحقق منه (مصدر Codex `codex-rs`، commit `8d9f646`): Codex يقرأ `AGENTS.md` من جذر المشروع حتى المجلد الحالي
  بحد افتراضي 32 KiB (`project_doc_max_bytes`) ولا يقرأ `CLAUDE.md`؛ يكتشف المهارات في `.agents/skills/` ويتبع
  الروابط الرمزية للمجلدات في نطاق المستودع، ولا يفحص `.claude/skills/`.

## Decision

1. `AGENTS.md` = سياسة الهندسة المشتركة الوحيدة (موجزة، < 250 سطراً، < 32 KiB).
2. `CLAUDE.md` = سطر `@AGENTS.md` + تعليمات خاصة بـ Claude فقط.
3. مهارات التطوير في `.claude/skills/<name>/SKILL.md` بصيغة Agent Skills المحمولة (`name`, `description` فقط إضافة
   للحقول المحمولة)، و`.agents/skills` رابط رمزي إلى `../.claude/skills` لاكتشاف Codex — نسخة واحدة دون تكرار.
4. التفاصيل الإجرائية في `docs/` والمهارات (progressive disclosure)، لا في ملفات الجذر.

## Rationale

مصدر واحد للسياسة يمنع التعارض؛ الاستيراد والرابط الرمزي آليات موثقة رسمياً؛ الإيجاز يقلل استهلاك السياق.

## Alternatives considered

| البديل | سبب عدم الاختيار |
|---|---|
| نسختان منفصلتان (CLAUDE.md و AGENTS.md كاملتان) | تكرار وتعارض محتمل |
| رابط رمزي `CLAUDE.md → AGENTS.md` | لا يسمح بتعليمات خاصة بـ Claude؛ التوثيق يفضّل الاستيراد |
| حذف `CLAUDE.md` | يفقد محتوى الميثاق المحفوظ وتعليمات Claude الخاصة |

## Consequences

- يتحقق `scripts/validate/repo_checks.py` من وجود `@AGENTS.md`، حدود الحجم، صحة بيانات المهارات، والرابط الرمزي.
- **لم يُختبر** تشغيل Codex فعلياً على المستودع (لا تتوفر بيئة Codex) — الحالة: Configured, not runtime-tested.

## Verification

جلسة Claude Code جديدة تحمّل `AGENTS.md` عبر الاستيراد؛ جلسة Codex الأولى تؤكد الاكتشاف وتُحدّث هذا القسم.
