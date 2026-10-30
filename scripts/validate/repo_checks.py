#!/usr/bin/env python3
"""Repository governance checks for EF AI Workspace.

Runs offline, needs only the Python standard library plus PyYAML.
Exit code 0 = all checks passed, 1 = at least one failure.

Usage:
    python3 scripts/validate/repo_checks.py            # run all checks
    python3 scripts/validate/repo_checks.py --list     # list check names
    python3 scripts/validate/repo_checks.py links adr  # run selected checks
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[2]

# Files that must exist for the repository to satisfy its own entry-point contract.
REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".github/CODEOWNERS",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/dependabot.yml",
    ".claude/settings.json",
    "docs/README.md",
    "docs/product/vision.md",
    "docs/product/scope.md",
    "docs/product/BRD.md",
    "docs/product/functional-requirements.md",
    "docs/product/non-functional-requirements.md",
    "docs/architecture/overview.md",
    "docs/architecture/HLD.md",
    "docs/architecture/data-flow.md",
    "docs/architecture/adr/README.md",
    "docs/quality/definition-of-done.md",
    "project/START_HERE.md",
    "project/CURRENT_STATE.md",
    "project/ROADMAP.md",
    "docs/history/README.md",
    "ai/README.md",
    "infrastructure/common/librechat.yaml",
    "infrastructure/common/librechat.env",
    "infrastructure/compose/compose.yaml",
    "infrastructure/compose/compose.local.yaml",
    "infrastructure/compose/compose.onprem.yaml",
    "infrastructure/compose/.env.example",
    "infrastructure/railway/librechat.Dockerfile",
    "infrastructure/railway/mongodb.Dockerfile",
    ".railway/railway.ts",
    ".railway/package.json",
    ".railway/package-lock.json",
    "scripts/validate/compose_checks.py",
    "scripts/validate/railway_checks.py",
    "tests/lib.sh",
    "tests/smoke/compose-stack.sh",
    "tests/smoke/railway-emulation.sh",
    "tests/smoke/railway-manual-deploy.sh",
    "tests/policy/negative-checks.sh",
    "tests/integration/mock_chat.py",
    "scripts/setup/railway-deploy.sh",
]

# Size budgets (max bytes, max lines) for the documents every agent session reads before any task.
# History belongs in Issues, CHANGELOG.md and docs/history/, not in these files.
DOC_BUDGETS = {
    "project/CURRENT_STATE.md": (10 * 1024, 80),
    "project/START_HERE.md": (6 * 1024, 60),
}

# Markdown stays readable on a phone: no line over PROSE_MAX characters outside fenced code.
# Archived history and ADRs are kept verbatim and therefore exempt.
PROSE_MAX = 400
PROSE_EXEMPT = ("docs/history/", "docs/architecture/adr/")

# Tracked paths that must never be committed (secrets / runtime data).
FORBIDDEN_TRACKED = [
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)\.env\.(?!example$)[^/]+$"),
    re.compile(r"\.(pem|key|p12|pfx|jks)$"),
    re.compile(r"(^|/)CLAUDE\.local\.md$"),
    re.compile(r"(^|/)\.claude/settings\.local\.json$"),
    re.compile(r"\.(dump|bson|archive)$"),
    re.compile(r"(^|/)secrets/(?!README\.md$)[^/]+"),
]

# Agent Skills portable frontmatter profile (shared by Claude Code and Codex).
SKILL_ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Inline links and images; reference-style links and raw HTML are not checked.
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
INLINE_CODE_RE = re.compile(r"`[^`]*`")

failures: list[str] = []


def fail(check: str, msg: str) -> None:
    failures.append(f"[{check}] {msg}")


def tracked_files() -> list[str]:
    """Files tracked by git plus untracked-but-not-ignored files (pre-commit view)."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return sorted({p for p in out.splitlines() if p and (ROOT / p).exists()})


def markdown_files() -> list[Path]:
    return [ROOT / p for p in tracked_files() if p.endswith(".md")]


def strip_code(lines: list[str], inline: bool = True) -> list[str]:
    """Blank out fenced code blocks (and inline code if requested) so links inside code are ignored."""
    result: list[str] = []
    fence = ""  # opening marker of the current fenced block; a block closes only on the same character
    for line in lines:
        m = FENCE_RE.match(line)
        if m and (not fence or (m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence))):
            fence = "" if fence else m.group(1)
            result.append("")
            continue
        if fence:
            result.append("")
        else:
            result.append(INLINE_CODE_RE.sub("", line) if inline else line)
    return result


def github_slug(text: str) -> str:
    """Approximate GitHub's heading anchor algorithm (works for Arabic headings)."""
    text = re.sub(r"<[^>]+>", "", text).replace("`", "")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # keep link text only
    text = text.strip().lower()
    kept = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch in "-_ " or cat[0] in ("L", "N") or cat in ("Mn", "Mc"):
            kept.append(ch)
    return "".join(kept).replace(" ", "-")


def anchors_for(path: Path, cache: dict[Path, set[str]]) -> set[str]:
    if path not in cache:
        seen: dict[str, int] = {}
        anchors: set[str] = set()
        # GitHub keeps inline-code text in heading anchors, so only fenced blocks are skipped here.
        for line in strip_code(path.read_text(encoding="utf-8").splitlines(), inline=False):
            m = HEADING_RE.match(line)
            if not m:
                continue
            slug = github_slug(m.group(2))
            n = seen.get(slug, 0)
            anchors.add(slug if n == 0 else f"{slug}-{n}")
            seen[slug] = n + 1
        cache[path] = anchors
    return cache[path]


# ----------------------------------------------------------------- checks


def check_required() -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail("required", f"missing required file: {rel}")


def check_budgets() -> None:
    for rel, (max_bytes, max_lines) in DOC_BUDGETS.items():
        path = ROOT / rel
        if not path.is_file():
            continue  # reported by the 'required' check
        size = path.stat().st_size
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if size > max_bytes:
            fail("budgets", f"{rel} is {size} bytes (budget {max_bytes}); move history to docs/history/ or the Issue")
        if lines > max_lines:
            fail("budgets", f"{rel} has {lines} lines (budget {max_lines}); move history to docs/history/ or the Issue")


def check_forbidden() -> None:
    for rel in tracked_files():
        if rel.endswith(".example"):
            continue
        for pattern in FORBIDDEN_TRACKED:
            if pattern.search(rel):
                fail("forbidden", f"file must not be committed: {rel}")


def check_links() -> None:
    cache: dict[Path, set[str]] = {}
    for md in markdown_files():
        lines = strip_code(md.read_text(encoding="utf-8").splitlines())
        for lineno, line in enumerate(lines, 1):
            for target in LINK_RE.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                    continue  # external (http, https, mailto, ...) — not checked offline
                path_part, _, anchor = target.partition("#")
                path_part = urllib.parse.unquote(path_part)
                dest = md if not path_part else (md.parent / path_part).resolve()
                where = f"{md.relative_to(ROOT)}:{lineno}"
                if path_part and not dest.exists():
                    fail("links", f"{where} broken link -> {target}")
                    continue
                if anchor and dest.is_file() and dest.suffix == ".md":
                    if anchor not in anchors_for(dest, cache):
                        fail("links", f"{where} missing anchor -> {target}")


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    data = yaml.safe_load(text[4:end])
    return data if isinstance(data, dict) else None


def check_skills() -> None:
    skills_dir = ROOT / ".claude" / "skills"
    if not skills_dir.is_dir():
        fail("skills", ".claude/skills directory is missing")
        return
    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    if not skill_dirs:
        fail("skills", "no skills found in .claude/skills")
    for d in skill_dirs:
        skill_md = d / "SKILL.md"
        rel = skill_md.relative_to(ROOT)
        if not skill_md.is_file():
            fail("skills", f"{d.relative_to(ROOT)} has no SKILL.md")
            continue
        fm = parse_frontmatter(skill_md)
        if fm is None:
            fail("skills", f"{rel}: missing or invalid YAML frontmatter")
            continue
        extra = set(fm) - SKILL_ALLOWED_KEYS
        if extra:
            fail("skills", f"{rel}: non-portable frontmatter keys {sorted(extra)}")
        name = fm.get("name")
        if name != d.name:
            fail("skills", f"{rel}: name '{name}' must equal directory name '{d.name}'")
        if not isinstance(name, str) or len(name) > 64 or not SKILL_NAME_RE.match(name or ""):
            fail("skills", f"{rel}: name must be lowercase a-z0-9 and single hyphens, <=64 chars")
        desc = fm.get("description")
        if not isinstance(desc, str) or not desc.strip():
            fail("skills", f"{rel}: description is required")
        elif len(desc) > 1024:
            fail("skills", f"{rel}: description exceeds 1024 characters")
        body_lines = skill_md.read_text(encoding="utf-8").count("\n")
        if body_lines > 500:
            fail("skills", f"{rel}: SKILL.md exceeds 500 lines ({body_lines})")
    # Codex discovers repo skills under .agents/skills; we share them via a symlink.
    link = ROOT / ".agents" / "skills"
    if not link.is_symlink() or os.readlink(link) != "../.claude/skills":
        fail("skills", ".agents/skills must be a symlink to ../.claude/skills (Codex discovery)")


# Platform Skills (ai/skills/, ADR-0017) as LibreChat v0.8.8 loads them from DEPLOYMENT_SKILLS_DIR at startup: an
# invalid SKILL.md stops the server from starting (packages/api/src/skills/deployment.ts), so it is caught here.
PLATFORM_SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PLATFORM_SKILL_RESERVED = {"help", "clear", "compact", "model", "exit", "quit", "settings", "anthropic", "claude"}
PLATFORM_SKILL_BOOLEANS = {"always-apply", "alwaysapply", "user-invocable", "disable-model-invocation"}


def check_platform_skills() -> None:
    root = ROOT / "ai" / "skills"
    if not root.is_dir():
        return
    for entry in sorted(root.iterdir()):
        rel = entry.relative_to(ROOT)
        if not entry.is_dir():
            fail("platform-skills", f"{rel}: only skill folders belong in ai/skills (it is mounted as /app/skill)")
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            fail("platform-skills", f"{rel} has no SKILL.md")
            continue
        try:
            fm = parse_frontmatter(skill_md)
        except yaml.YAMLError as exc:
            fm = None
            fail("platform-skills", f"{skill_md.relative_to(ROOT)}: {str(exc).splitlines()[0]} (quote values with ':')")
            continue
        if fm is None:
            fail("platform-skills", f"{skill_md.relative_to(ROOT)}: missing or invalid YAML frontmatter")
            continue
        keys = {str(k).lower(): v for k, v in fm.items()}
        name = keys.get("name")
        if (not isinstance(name, str) or name != entry.name or len(name) > 64 or not PLATFORM_SKILL_NAME_RE.match(name)
                or name in PLATFORM_SKILL_RESERVED or name.startswith(("anthropic-", "claude-"))):
            fail("platform-skills", f"{rel}: name must equal the folder, match [a-z0-9][a-z0-9-]*, <=64 chars, "
                 "and not be reserved or start with anthropic-/claude-")
        desc = keys.get("description")
        if not isinstance(desc, str) or not 20 <= len(desc.strip()) <= 250:
            fail("platform-skills", f"{rel}: description must be 20-250 characters (LibreChat trims the model catalog "
                 "at 250)")
        for key in PLATFORM_SKILL_BOOLEANS & set(keys):
            if not isinstance(keys[key], bool):
                fail("platform-skills", f"{rel}: {key} must be true or false")
        text = skill_md.read_text(encoding="utf-8")
        body = text[text.find("\n---", 4) + 4:].strip()
        if not body or len(body) > 100_000:
            fail("platform-skills", f"{rel}: the instruction body must be non-empty and <= 100,000 characters")
        files = [f for f in entry.rglob("*") if f.is_file()]
        if len(files) > 500 or any(f.stat().st_size > 10 * 1024 * 1024 for f in files):
            fail("platform-skills", f"{rel}: at most 500 files of 10 MB each")


def check_agent_files() -> None:
    agents = ROOT / "AGENTS.md"
    claude = ROOT / "CLAUDE.md"
    if agents.is_file() and agents.stat().st_size > 32 * 1024:
        fail("agents", "AGENTS.md exceeds Codex project_doc_max_bytes default (32 KiB)")
    if claude.is_file():
        lines = claude.read_text(encoding="utf-8").splitlines()
        if not any(line.strip() == "@AGENTS.md" for line in lines):
            fail("agents", "CLAUDE.md must import shared policy with a standalone '@AGENTS.md' line")
        if len(lines) > 200:
            fail("agents", f"CLAUDE.md exceeds 200 lines ({len(lines)})")
    if agents.is_file() and len(agents.read_text(encoding="utf-8").splitlines()) > 250:
        fail("agents", "AGENTS.md exceeds 250 lines; move detail into docs/ or skills")


def check_requirements() -> None:
    fr = ROOT / "docs/product/functional-requirements.md"
    if fr.is_file():
        text = fr.read_text(encoding="utf-8")
        headings = re.findall(r"^### (FR-\d{3})\b", text, re.M)
        index = re.findall(r"^\| (FR-\d{3}) \|", text, re.M)
        for rid in {h for h in headings if headings.count(h) > 1}:
            fail("requirements", f"duplicate requirement heading {rid}")
        if sorted(set(headings)) != sorted(set(index)):
            fail("requirements", f"FR index/heading mismatch: index={sorted(set(index) ^ set(headings))}")
    nfr = ROOT / "docs/product/non-functional-requirements.md"
    if nfr.is_file():
        ids = re.findall(r"^\| (NFR-[A-Z0-9]+-\d{2}) \|", nfr.read_text(encoding="utf-8"), re.M)
        for rid in {i for i in ids if ids.count(i) > 1}:
            fail("requirements", f"duplicate NFR id {rid}")


def check_adr() -> None:
    adr_dir = ROOT / "docs/architecture/adr"
    index = adr_dir / "README.md"
    if not index.is_file():
        return
    index_text = index.read_text(encoding="utf-8")
    numbers: list[str] = []
    for adr in sorted(adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")):
        numbers.append(adr.name[:4])
        text = adr.read_text(encoding="utf-8")
        for field in ("Status", "Date"):
            if not re.search(rf"^\|\s*{field}\s*\|", text, re.M):
                fail("adr", f"{adr.name}: missing '{field}' metadata row")
        for section in ("Context", "Decision", "Rationale", "Alternatives considered", "Consequences"):
            if not re.search(rf"^## {section}\b", text, re.M):
                fail("adr", f"{adr.name}: missing section '## {section}'")
        if f"({adr.name})" not in index_text:
            fail("adr", f"{adr.name} is not listed in adr/README.md")
    for n in {x for x in numbers if numbers.count(x) > 1}:
        fail("adr", f"duplicate ADR number {n}")


def check_structured_files() -> None:
    for rel in tracked_files():
        path = ROOT / rel
        try:
            if rel.endswith(".json"):
                json.loads(path.read_text(encoding="utf-8"))
            elif rel.endswith((".yml", ".yaml")):
                list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        except (ValueError, yaml.YAMLError) as exc:
            fail("syntax", f"{rel}: {exc.__class__.__name__}: {str(exc).splitlines()[0]}")


def check_prose() -> None:
    for md in markdown_files():
        rel = md.relative_to(ROOT).as_posix()
        if rel.startswith(PROSE_EXEMPT):
            continue
        lines = strip_code(md.read_text(encoding="utf-8").splitlines(), inline=False)
        for lineno, line in enumerate(lines, 1):
            if len(line) > PROSE_MAX:
                fail("prose", f"{rel}:{lineno} is {len(line)} characters (max {PROSE_MAX}); split it or use a list")


def check_claude_settings() -> None:
    """Secret files must be read-denied while safe templates (.env.example) stay readable.

    Mirrors Claude Code's documented gitignore semantics for deny rules: a later `!` rule in the
    same deny list carves paths out of earlier rules. Behaviour was confirmed with Claude Code
    2.1.302 in a cloud session (see docs/history/reports/M0-delivery-report.md).
    """
    path = ROOT / ".claude/settings.json"
    if not path.is_file():
        return
    try:
        deny = json.loads(path.read_text(encoding="utf-8"))["permissions"]["deny"]
    except (ValueError, KeyError, TypeError):
        fail("settings", ".claude/settings.json has no permissions.deny list")
        return
    patterns = [r[5:-1] for r in deny if isinstance(r, str) and r.startswith("Read(") and r.endswith(")")]

    def denied(name: str) -> bool:
        result = False
        for pat in patterns:
            negate = pat.startswith("!")
            pat = pat[1:] if negate else pat
            pat = pat.removeprefix("./").removeprefix("**/")
            if fnmatch.fnmatchcase(name, pat):
                result = not negate
        return result

    for name in (".env", ".env.local", ".env.production"):
        if not denied(name):
            fail("settings", f"secret file '{name}' is not read-denied in .claude/settings.json")
    if denied(".env.example"):
        fail("settings", "'.env.example' is read-denied; add Read(!.env.example) after the .env.* rule")


CHECKS: dict[str, Callable[[], None]] = {
    "required": check_required,
    "budgets": check_budgets,
    "forbidden": check_forbidden,
    "links": check_links,
    "skills": check_skills,
    "platform-skills": check_platform_skills,
    "agents": check_agent_files,
    "settings": check_claude_settings,
    "requirements": check_requirements,
    "adr": check_adr,
    "syntax": check_structured_files,
    "prose": check_prose,
}


def main(argv: list[str]) -> int:
    if "--list" in argv:
        print("\n".join(CHECKS))
        return 0
    selected = argv or list(CHECKS)
    unknown = [c for c in selected if c not in CHECKS]
    if unknown:
        print(f"unknown check(s): {unknown}; use --list", file=sys.stderr)
        return 2
    for name in selected:
        before = len(failures)
        CHECKS[name]()
        status = "PASS" if len(failures) == before else "FAIL"
        print(f"{status:4}  {name}")
    if failures:
        print("\nFailures:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nAll repository checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
