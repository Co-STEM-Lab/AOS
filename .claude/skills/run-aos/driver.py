#!/usr/bin/env python3
"""
AOS smoke driver — install, verify, run every CLI entry point.

Usage:
    python .claude/skills/run-aos/driver.py           # full smoke test
    python .claude/skills/run-aos/driver.py --quick   # fast check only
"""

import sys
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS = ROOT / "scripts"
VENV = ROOT / "venv"
PYTHON = VENV / "bin" / "python3"

PASS = 0
SKIP = 0
FAIL = 0


def report(name: str, ok: bool, detail: str = ""):
    global PASS, SKIP, FAIL
    if ok is None:
        SKIP += 1
        print(f"  ⬜ SKIP  {name}")
    elif ok:
        PASS += 1
        print(f"  ✅ PASS  {name}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL  {name}")
        if detail:
            for line in detail.strip().split("\n")[:5]:
                print(f"          {line}")


def run(cmd: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(PYTHON)] + cmd,
        capture_output=True, text=True, timeout=timeout, cwd=str(ROOT)
    )


def setup():
    """Ensure venv + PyYAML."""
    if not VENV.exists():
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(VENV)],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        if result.returncode != 0:
            report("venv create", False, result.stderr)
            return False

    result = subprocess.run(
        [str(PYTHON), "-m", "pip", "install", "-q", "pyyaml"],
        capture_output=True, text=True, timeout=60, cwd=str(ROOT)
    )
    report("venv + PyYAML", result.returncode == 0, result.stderr)
    return result.returncode == 0


def test_scan():
    """scan.py — the main entry point."""
    r = run(["scripts/scan.py"])
    ok = r.returncode in (0, 1, 2) and "AOS" in r.stdout
    report("scan.py", ok,
           f"exit={r.returncode}" if not ok else "")


def test_scan_json():
    """scan.py --json — machine-readable output."""
    r = run(["scripts/scan.py", "--json"])
    ok = r.returncode in (0, 1, 2)
    import json
    try:
        d = json.loads(r.stdout.strip())
        ok = ok and "timestamp" in d and "invariants" in d
    except json.JSONDecodeError:
        ok = False
    report("scan.py --json", ok,
           f"JSON parse failed: {r.stdout[:100]}" if not ok else "")


def test_scan_log():
    """scan.py --log — scan + write maintenance log."""
    r = run(["scripts/scan.py", "--log"])
    ok = r.returncode in (0, 1, 2) and "已追加" in r.stdout
    report("scan.py --log", ok,
           f"exit={r.returncode} stdout={r.stdout[-100:]}" if not ok else "")


def test_invariants():
    """check_invariants.py — hard guard."""
    r = run(["scripts/check_invariants.py"])
    ok = r.returncode in (0, 1, 2) and "不变式" in r.stdout
    report("check_invariants.py", ok,
           f"exit={r.returncode}" if not ok else "")


def test_invariants_json():
    """check_invariants.py --json — structured output."""
    r = run(["scripts/check_invariants.py", "--json"])
    ok = r.returncode in (0, 1, 2)
    import json
    try:
        d = json.loads(r.stdout.strip())
        ok = ok and "summary" in d and "hard_violations" in d
    except json.JSONDecodeError:
        ok = False
    report("check_invariants.py --json", ok)


def test_status():
    """check_status.py — health panel."""
    r = run(["scripts/check_status.py"])
    ok = r.returncode == 0 and "健康" in r.stdout
    report("check_status.py", ok)


def test_aggregate_help():
    """aggregate.py — help output."""
    r = run(["scripts/aggregate.py"])
    ok = r.returncode != 0 and "用法" in r.stdout
    report("aggregate.py --help", ok)


def test_render_help():
    """render.py — help output."""
    r = run(["scripts/render.py"])
    ok = r.returncode != 0 and "用法" in r.stdout
    report("render.py --help", ok)


def test_smoke_self():
    """smoke.py — wrapper script exists and is executable."""
    ok = (ROOT / "scripts" / "smoke.py").exists() and \
         (ROOT / "scripts" / "smoke.py").stat().st_mode & 0o111
    report("smoke.py (exists + executable)", ok,
           "file missing or not executable" if not ok else "")


def test_env_isolation():
    """Verify scripts run from clean env (no hardcoded paths)."""
    g = subprocess.run(
        ["grep", "-rn", "/home/", str(SCRIPTS)],
        capture_output=True, text=True, timeout=10, cwd=str(ROOT)
    )
    # Exclude lines that are regex patterns used to DETECT hardcoded paths
    hardcoded = [
        line for line in g.stdout.strip().split("\n") if line
        and 'findall' not in line and 're.' not in line
    ]
    ok = len(hardcoded) == 0
    report("no hardcoded paths in scripts/", ok,
           "\n".join(hardcoded[:3]) if not ok else "")


def test_git_hook_exists():
    """pre-commit hook installed."""
    hook = ROOT / ".git" / "hooks" / "pre-commit"
    ok = hook.exists()
    report("pre-commit hook", ok,
           "run: bash scripts/install-hooks.sh" if not ok else "")


def main():
    quick = "--quick" in sys.argv

    print("=" * 56)
    print("  AOS Smoke Driver")
    print("=" * 56)
    print(f"  ROOT: {ROOT}")
    print()

    print("🔧 Setup")
    if not setup():
        print("❌ Setup failed — cannot continue")
        sys.exit(2)
    print()

    print("🧪 Tests")
    test_scan()
    test_scan_json()
    test_scan_log()
    test_invariants()
    test_invariants_json()
    test_status()
    test_aggregate_help()
    test_render_help()
    test_smoke_self()

    if not quick:
        test_env_isolation()
        test_git_hook_exists()

    print()
    print("=" * 56)
    total = PASS + FAIL + SKIP
    print(f"  Results: {PASS} passed, {FAIL} failed, {SKIP} skipped ({total} total)")
    print("=" * 56)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
