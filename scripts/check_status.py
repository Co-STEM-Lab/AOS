#!/usr/bin/env python3
"""
状态检查：一键查看 AOS 健康度（矩阵覆盖率、原子库存、项目阻塞、新鲜度漂移）。

用法：
    python scripts/check_status.py              # 人类可读面板
    python scripts/check_status.py --json       # 机器可读 JSON
    python scripts/check_status.py --freshness  # 仅新鲜度检查

依赖：PyYAML + knowledge/controlled-vocabulary.yml
"""

import sys
import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = ROOT / "knowledge" / "atoms"
PROJECTS_DIR = ROOT / "projects"
VOCAB_PATH = ROOT / "knowledge" / "controlled-vocabulary.yml"
SKILL_TREE_PATH = ROOT / "competencies" / "skill-tree.md"
MATRIX_PATH = ROOT / "matrix.md"


def parse_front_matter(filepath: str) -> dict | None:
    """解析 YAML front-matter，返回字典。"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def parse_body(filepath: str) -> str:
    """提取 YAML front-matter 之后的正文。"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", content, re.DOTALL)
    if not match:
        return content
    return match.group(1)


def count_atoms() -> dict:
    """统计原子库存。"""
    inventory = {"total": 0, "draft": 0, "final": 0, "by_type": defaultdict(int), "uncategorized": 0}
    for f in ATOMS_DIR.rglob("*.md"):
        if f.parent.name in ("example", "scripts"):
            continue
        fm = parse_front_matter(str(f))
        if not fm:
            continue
        inventory["total"] += 1
        status = fm.get("status", "draft")
        if status == "draft":
            inventory["draft"] += 1
        else:
            inventory["final"] += 1
        inventory["by_type"][fm.get("type", "unknown")] += 1
        if fm.get("project") == "uncategorized" or not fm.get("project"):
            inventory["uncategorized"] += 1
    return inventory


def scan_projects() -> dict:
    """扫描所有项目状态。"""
    projects = []
    for subdir in ["active", "completed", "ideas"]:
        dir_path = PROJECTS_DIR / subdir
        if not dir_path.is_dir():
            continue
        for proj_dir in sorted(dir_path.iterdir()):
            if not proj_dir.is_dir():
                continue
            index_file = proj_dir / "index.md"
            if not index_file.exists():
                continue
            fm = parse_front_matter(str(index_file))
            if not fm:
                continue
            projects.append({
                "id": fm.get("id", proj_dir.name),
                "title": fm.get("title", proj_dir.name),
                "status": fm.get("status", "unknown"),
                "bucket": subdir,
            })
    return {"projects": projects, "total": len(projects)}


def load_freshness_thresholds() -> dict:
    """从词汇表加载新鲜度阈值。"""
    if not VOCAB_PATH.exists():
        return {"skill_stale_days": 180, "project_stale_days": 90, "atom_draft_stale_days": 60}
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        vocab = yaml.safe_load(f)
    return vocab.get("freshness", {"skill_stale_days": 180, "project_stale_days": 90, "atom_draft_stale_days": 60})


def days_since(date_str: str) -> int | None:
    """计算从给定日期到今天的天数。"""
    if not date_str:
        return None
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except ValueError:
        return None


def check_skill_freshness() -> list[dict]:
    """检查技能新鲜度（不变式② 证据前置的扩展）。"""
    warnings = []
    thresholds = load_freshness_thresholds()
    max_days = thresholds["skill_stale_days"]

    if not SKILL_TREE_PATH.exists():
        return warnings

    content = SKILL_TREE_PATH.read_text(encoding="utf-8")
    # 匹配技能行: | 技能名 | L2+ | 证据 |
    pattern = re.compile(r'^\|\s*([^|]+?)\s*\|\s*(L[234])\s*\|\s*([^|]*?)\s*\|', re.MULTILINE)
    for match in pattern.finditer(content):
        skill_name = match.group(1).strip()
        level = match.group(2)
        evidence = match.group(3).strip()
        if skill_name in ("技能", "------", ""):
            continue
        if not evidence or evidence == "--":
            warnings.append({
                "type": "skill_no_evidence",
                "skill": skill_name,
                "level": level,
                "message": f"技能 '{skill_name}' ({level}) 无证据",
                "severity": "high" if level in ("L3", "L4") else "low",
            })

    return warnings


def check_project_staleness() -> list[dict]:
    """检查项目停滞（不变式③ 矩阵封闭的活性扩展）。"""
    warnings = []
    thresholds = load_freshness_thresholds()
    max_days = thresholds["project_stale_days"]

    for bucket in ["active", "ideas"]:
        bucket_dir = PROJECTS_DIR / bucket
        if not bucket_dir.is_dir():
            continue
        for proj_dir in sorted(bucket_dir.iterdir()):
            if not proj_dir.is_dir():
                continue
            idx = proj_dir / "index.md"
            if not idx.exists():
                continue
            fm = parse_front_matter(str(idx))
            if not fm:
                continue
            pid = fm.get("id", proj_dir.name)
            title = fm.get("title", pid)
            status = fm.get("status", "unknown")
            updated = fm.get("updated", "")

            # 检查 active 但无日志
            if bucket == "active":
                body = parse_body(str(idx))
                log_entries = re.findall(r'^\|\s*\d{4}-\d{2}-\d{2}\s*\|', body, re.MULTILINE)
                if not log_entries:
                    warnings.append({
                        "type": "project_no_log",
                        "project_id": pid,
                        "title": title,
                        "status": status,
                        "message": f"项目 '{title}' ({status}) 无进度日志条目",
                        "severity": "medium",
                    })

            # 检查 updated 时间陈旧
            age = days_since(updated)
            if age is not None and age > max_days and bucket == "active":
                warnings.append({
                    "type": "project_stale",
                    "project_id": pid,
                    "title": title,
                    "status": status,
                    "age_days": age,
                    "message": f"项目 '{title}' 已 {age} 天未更新（阈值 {max_days} 天）",
                    "severity": "medium" if age > max_days * 2 else "low",
                })

    return warnings


def check_atom_staleness() -> list[dict]:
    """检查原子草稿陈旧。"""
    warnings = []
    thresholds = load_freshness_thresholds()
    max_days = thresholds["atom_draft_stale_days"]

    for f in sorted(ATOMS_DIR.rglob("*.md")):
        if f.parent.name in ("example", "scripts"):
            continue
        fm = parse_front_matter(str(f))
        if not fm:
            continue
        aid = fm.get("id", f.stem)
        status = fm.get("status", "draft")
        created = fm.get("created", "")

        if status == "draft":
            age = days_since(created)
            if age is not None and age > max_days:
                warnings.append({
                    "type": "atom_draft_stale",
                    "atom_id": aid,
                    "title": fm.get("title", aid),
                    "age_days": age,
                    "message": f"draft 原子 '{fm.get('title', aid)}' 已 {age} 天未定稿（阈值 {max_days} 天）",
                    "severity": "low",
                })

    return warnings


def check_matrix_coverage() -> dict:
    """检查矩阵覆盖率。"""
    if not MATRIX_PATH.exists():
        return {"error": "matrix.md 不存在"}

    content = MATRIX_PATH.read_text(encoding="utf-8")
    # 找到第一个数据表（非示例）
    tables = re.findall(r'^\|[-| ]+\|$.*?(?=\n\n|\n#|\Z)', content, re.MULTILINE | re.DOTALL)

    # 简化：统计矩阵中的项目链接数
    project_refs = re.findall(r'\[(proj-\w+)\]\(', content)
    # 统计空白格（用 '—' 或空）
    empty_cells = len(re.findall(r'\|\s*—\s*\|', content))

    return {
        "project_refs_in_matrix": len(project_refs),
        "empty_cells": empty_cells,
    }


def main():
    json_mode = "--json" in sys.argv
    freshness_only = "--freshness" in sys.argv

    if not freshness_only:
        atoms = count_atoms()
        proj_info = scan_projects()
    skill_warnings = check_skill_freshness()
    project_warnings = check_project_staleness()
    atom_warnings = check_atom_staleness()
    matrix_cov = check_matrix_coverage()

    all_freshness = skill_warnings + project_warnings + atom_warnings

    if json_mode:
        report = {
            "timestamp": date.today().isoformat(),
            "atoms": atoms if not freshness_only else None,
            "projects": proj_info if not freshness_only else None,
            "freshness": {
                "total_warnings": len(all_freshness),
                "by_type": {
                    "skill": len(skill_warnings),
                    "project": len(project_warnings),
                    "atom": len(atom_warnings),
                },
                "warnings": all_freshness,
            },
            "matrix_coverage": matrix_cov,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(0)

    # 人类可读
    print("=" * 60)
    print("  AOS 系统健康检查")
    print("=" * 60)
    print(f"  时间: {date.today().isoformat()}")

    if not freshness_only:
        # 指标 1：原子库存量
        print(f"\n📦 原子库存: {atoms['total']}")
        print(f"   draft: {atoms['draft']} | final: {atoms['final']} | 未归类: {atoms['uncategorized']}")
        if atoms["by_type"]:
            print("   按类型:", dict(atoms["by_type"]))
        if atoms["total"] < 10:
            print("   ⚠️  原子 < 10，初稿生成功能受限")
        elif atoms["total"] >= 50:
            print("   ✅ 原子库存充足，可支撑初稿生成")

        # 指标 2：项目统计
        print(f"\n📁 项目总数: {proj_info['total']}")
        by_bucket = defaultdict(int)
        for p in proj_info["projects"]:
            by_bucket[p["bucket"]] += 1
        print(f"   ideas: {by_bucket.get('ideas', 0)} | active: {by_bucket.get('active', 0)} | completed: {by_bucket.get('completed', 0)}")

        if proj_info["projects"]:
            print("\n   项目列表:")
            for p in proj_info["projects"]:
                icon = {"idea": "💡", "active": "🔬", "writing": "✍️", "submitted": "📤", "published": "✅"}.get(p["status"], "❓")
                print(f"   {icon} [{p['bucket']}] {p['title']}")

        # 指标 3：矩阵
        print(f"\n🗂️  矩阵覆盖率:")
        print(f"   项目引用: {matrix_cov.get('project_refs_in_matrix', '?')} | 空白格: {matrix_cov.get('empty_cells', '?')}")

    # 指标 4：新鲜度漂移
    print(f"\n⏳ 新鲜度漂移检测:")
    if all_freshness:
        print(f"   共 {len(all_freshness)} 项警告")
        # 按严重程度分组
        high = [w for w in all_freshness if w.get("severity") == "high"]
        medium = [w for w in all_freshness if w.get("severity") == "medium"]
        low = [w for w in all_freshness if w.get("severity") == "low"]

        if high:
            print(f"\n   🔴 高优先级 ({len(high)}):")
            for w in high:
                print(f"      {w['message']}")
        if medium:
            print(f"\n   🟡 中优先级 ({len(medium)}):")
            for w in medium:
                print(f"      {w['message']}")
        if low:
            print(f"\n   🟢 低优先级 ({len(low)}):")
            for w in low[:5]:  # 最多显示 5 条低优先级
                print(f"      {w['message']}")
            if len(low) > 5:
                print(f"      ... 及其他 {len(low) - 5} 项")
    else:
        print("   ✅ 无新鲜度漂移警告")

    # 最后更新
    print("\n---")
    print("建议:")
    print("  • 每周: python scripts/check_status.py")
    print("  • 提交前: python scripts/check_invariants.py")
    print("  • AI 巡检: 对 Claude Code 说 '检查 AOS'")


if __name__ == "__main__":
    main()
