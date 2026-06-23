#!/usr/bin/env python3
"""
AOS 统一扫描入口 —— 编排不变式校验 + 健康面板。

用法：
    python scripts/scan.py              # 人类可读统一面板
    python scripts/scan.py --json       # 机器可读 JSON

依赖：check_invariants.py + check_status.py
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent


def run(script: str, args: list[str]) -> dict:
    """运行子脚本并解析 JSON 输出。"""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)] + args,
        capture_output=True, text=True, timeout=30, cwd=str(ROOT)
    )
    try:
        return json.loads(result.stdout.strip())
    except (json.JSONDecodeError, IndexError):
        return {"error": (result.stdout.strip() or result.stderr.strip())[:200]}


def main():
    json_mode = "--json" in sys.argv

    invariants = run("check_invariants.py", ["--json"])
    health = run("check_status.py", ["--json"])

    if json_mode:
        report = {
            "timestamp": date.today().isoformat(),
            "invariants": invariants,
            "health": health,
            "pass": (invariants.get("summary", {}).get("pass", False) and
                     health.get("freshness", {}).get("total_warnings", 0) == 0),
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        ihard = invariants.get("summary", {}).get("hard", "?")
        isoft = invariants.get("summary", {}).get("soft", "?")
        ipass = invariants.get("summary", {}).get("pass", False)

        fw = health.get("freshness", {}).get("total_warnings", "?")
        fb = health.get("freshness", {}).get("by_type", {})

        print("=" * 60)
        print("  AOS 系统扫描")
        print("=" * 60)
        print(f"  时间: {date.today().isoformat()}")
        print()
        print(f"  📋 不变式: {'✅ 通过' if ipass else '❌ 违规'}")
        print(f"     HARD: {ihard} | SOFT: {isoft}")
        print(f"  ⏳ 新鲜度: 警告 {fw}")
        if fb:
            print(f"     技能: {fb.get('skill', 0)} | 项目: {fb.get('project', 0)} | 原子: {fb.get('atom', 0)}")
        print()

        if ipass and fw == 0:
            print("  ✅ 全部通过。")
        else:
            print("  → 详情: python scripts/check_invariants.py")
            print("  → 详情: python scripts/check_status.py")
        print()

        # 健康指标
        atoms = health.get("atoms") or {}
        projs = health.get("projects") or {}
        matrix = health.get("matrix_coverage") or {}
        if atoms:
            print(f"  📦 原子: {atoms.get('total', '?')} | draft: {atoms.get('draft', '?')} | final: {atoms.get('final', '?')}")
        if projs:
            print(f"  📁 项目: {projs.get('total', '?')}")
        print()

    iv_pass = invariants.get("summary", {}).get("pass", False)
    fw_total = health.get("freshness", {}).get("total_warnings", -1)
    sys.exit(0 if iv_pass and fw_total == 0 else (1 if not iv_pass else 2))


if __name__ == "__main__":
    main()
