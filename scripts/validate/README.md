# Validation scripts

| File | Purpose |
|---|---|
| `run-all.sh` | Runs every check defined in `.github/workflows/ci.yml` and `security.yml`; reads actionlint/gitleaks versions and SHA-256 sums from the workflows and verifies the downloaded binaries |
| `repo_checks.py` | Offline governance checks: required files, doc size budgets (`budgets`), forbidden tracked files, Markdown links + anchors and line length (`prose`, ≤ 400 characters outside code; history and ADRs exempt), skill frontmatter (also `ai/skills/`), agent-file limits, `.claude/settings.json` secret-read rules, requirement-ID uniqueness, ADR structure/index, JSON/YAML syntax |
| `requirements.in` | Top-level pinned validation tools |
| `requirements.txt` | Hash-locked lock file (generated — do not edit by hand) |

## Run locally (cloud session)

```bash
python3 -m venv .venv && . .venv/bin/activate      # a venv avoids PEP 668 "externally managed" errors
python -m pip install --require-hashes -r scripts/validate/requirements.txt
scripts/validate/run-all.sh                        # full CI + Security equivalent (+ negative policy tests, deploy path)
python scripts/validate/repo_checks.py links adr   # quick subset (see --list)
```

`run-all.sh` caches binaries in `${VALIDATE_CACHE:-~/.cache/ef-ai-workspace-validate}`. CI uses Python 3.12; use the same
version for evidence that should match CI (e.g. `uv venv -p 3.12`).

GitHub Actions is not used (owner decision, #16). These scripts are optional, task-chosen developer verification tools in
development and building blocks of the production quality gates (ADR-0011); results are cloud-session evidence, not
independent CI verification (`docs/quality/definition-of-done.md`).

## Updating pinned tools

```bash
# edit requirements.in, then:
uv pip compile scripts/validate/requirements.in --python-version 3.12 --generate-hashes \
  --no-header --universal -o scripts/validate/requirements.txt
```

Dependabot (`pip` ecosystem) proposes updates monthly. When bumping actionlint or gitleaks, update both the version and
the SHA-256 from the official release checksums file in the workflow `env:` block.
