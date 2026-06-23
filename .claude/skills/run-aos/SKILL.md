---
name: run-aos
description: >-
  Build, run, and smoke-test the AOS (Academic Operating System) project.
  Use this skill when asked to "run AOS", "start AOS", "test AOS",
  "verify AOS", "smoke test AOS", or "check if AOS works".
---

# Run AOS

AOS is a CLI knowledge-management system: Python scripts that validate and
orchestrate a Markdown/YAML knowledge base. There is no server, no GUI.

**Driver:** `.claude/skills/run-aos/driver.py` (shortcut: `scripts/smoke.py`)

All paths below are relative to the repo root.

## Prerequisites

```bash
python3 -m venv venv
source venv/bin/activate
pip install pyyaml
```

The driver auto-creates venv if missing.

## Run (agent path)

```bash
# Direct
source venv/bin/activate
python .claude/skills/run-aos/driver.py

# Shortcut (same thing)
python scripts/smoke.py
```

12 checks:

| # | Check | What it verifies |
|---|-------|-----------------|
| 1 | `scan.py` | Main entry point runs |
| 2 | `scan.py --json` | JSON output parses correctly |
| 3 | `scan.py --log` | Logs to `maintenance-log.md` |
| 4 | `check_invariants.py` | Hard guard runs |
| 5 | `check_invariants.py --json` | Structured JSON output |
| 6 | `check_status.py` | Health panel runs |
| 7 | `aggregate.py` | Usage on no-args |
| 8 | `render.py` | Usage on no-args |
| 9 | `smoke.py` | Shortcut exists + executable |
| 10 | no hardcoded paths | Scripts contain no `/home/` (excl. detection regex) |
| 11 | pre-commit hook | `.git/hooks/pre-commit` exists |
| 12 | venv + PyYAML | Environment ready |

Quick mode (9 checks):

```bash
python .claude/skills/run-aos/driver.py --quick
python scripts/smoke.py --quick
```

## Run (human path)

```bash
source venv/bin/activate
python scripts/scan.py --log
```

## Direct invocation (import internals)

The Python scripts are callable modules for targeted testing:

```bash
source venv/bin/activate
python -c "
from scripts.check_invariants import check_atom_front_matter, load_vocab
vocab = load_vocab()
violations = check_atom_front_matter(vocab)
print(f'Atom violations: {len(violations)}')
"
```

## Tests

AOS has no test suite yet. The driver is the smoke test.

## Install pre-commit hook

```bash
bash scripts/install-hooks.sh
```

## Gotchas

- **PyYAML required.** All scripts need it. The driver auto-installs if missing.
- **Pre-commit hook is local.** `.git/hooks/pre-commit` is not committed to the
  repo — each clone must run `install-hooks.sh`.
- **`aggregate.py` exits non-zero with no args.** This is correct behavior
  (prints usage). The driver checks stdout, not exit code.
- **`scan.py --log` appends to `maintenance-log.md`.** Running it twice on the
  same day won't duplicate entries.
- **qian-skill references live under `.claude/skills/qian-skill/references/`.**
  They are documentation, not executable skills. The skill's main file is
  `SKILL.md`.
- **`render.py` requires `markdown` package for best results.** Without it,
  falls back to built-in simple converter.
- **`smoke.py` is a thin wrapper** around `.claude/skills/run-aos/driver.py`.
  Running the driver directly also works.
- **The invariant checker's "no hardcoded paths" rule uses regex patterns
  containing `/home/` to detect violations.** These are detection rules, not
  violations themselves.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: yaml` | `pip install pyyaml` |
| `venv/bin/python3: No such file` | `python3 -m venv venv` |
| pre-commit check fails | `bash scripts/install-hooks.sh` |
| `scan.py` exit code 2 | SOFT warnings only; check output for details |
| `scan.py` exit code 1 | HARD violations exist; fix then re-run |
