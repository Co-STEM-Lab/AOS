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

**Driver:** `.claude/skills/run-aos/driver.py` — runs every script entry
point with representative arguments, checks exit codes and output.

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
source venv/bin/activate
python .claude/skills/run-aos/driver.py
```

Runs 10 checks:

| # | Check | What it verifies |
|---|-------|-----------------|
| 1 | `scan.py` | Main entry point runs, output contains "AOS" |
| 2 | `scan.py --json` | Machine-readable JSON output parses correctly |
| 3 | `scan.py --log` | Logs to `knowledge/maintenance-log.md` |
| 4 | `check_invariants.py` | Hard guard runs, output contains "不变式" |
| 5 | `check_invariants.py --json` | Structured JSON with `summary` and `violations` |
| 6 | `check_status.py` | Health panel runs, output contains "健康" |
| 7 | `aggregate.py` | Prints usage on no-args (exit ≠ 0 is expected) |
| 8 | no hardcoded paths | Scripts contain no `/home/` paths (excl. detection regex) |
| 9 | pre-commit hook | `.git/hooks/pre-commit` exists |
| 10 | venv + PyYAML | Environment is ready |

Quick mode (skips env isolation and hook check):

```bash
python .claude/skills/run-aos/driver.py --quick
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
- **The invariant checker's "no hardcoded paths" rule uses regex patterns
  containing `/home/` to detect violations.** These are detection rules, not
  violations themselves. The driver excludes them.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: yaml` | `pip install pyyaml` |
| `venv/bin/python3: No such file` | `python3 -m venv venv` |
| pre-commit check fails | `bash scripts/install-hooks.sh` |
| `scan.py` exit code 2 | SOFT warnings only; check output for details |
| `scan.py` exit code 1 | HARD violations exist; fix then re-run |
