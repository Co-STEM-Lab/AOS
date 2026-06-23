#!/usr/bin/env python3
"""
状态检查：一键查看 AOS 健康度（矩阵覆盖率、原子库存、项目阻塞）。

用法：
    python scripts/check_status.py

依赖：PyYAML
"""

import sys
import os
import re
import yaml
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = ROOT / "knowledge" / "atoms"
PROJECTS_DIR = ROOT / "projects"


def parse_front_matter(filepath: str) -> dict | None:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def count_atoms() -> dict:
    """统计原子库存。"""
    inventory = {"total": 0, "draft": 0, "final": 0, "by_type": defaultdict(int), "uncategorized": 0}
    for f in ATOMS_DIR.glob("*.md"):
        if f.name.startswith("example-"):
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


def main():
    atoms = count_atoms()
    proj_info = scan_projects()

    print("=" * 50)
    print("  AOS 状态检查")
    print("=" * 50)

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

    # 项目详情
    if proj_info["projects"]:
        print("\n   项目列表:")
        for p in proj_info["projects"]:
            icon = {"idea": "💡", "active": "🔬", "writing": "✍️", "submitted": "📤", "published": "✅"}.get(p["status"], "❓")
            print(f"   {icon} [{p['bucket']}] {p['title']}")

    # 指标 3：阻塞检测
    print("\n🚧 阻塞检测:")
    blocked = [p for p in proj_info["projects"] if p["status"] in ("active", "writing")]
    if blocked:
        print(f"   进行中项目: {len(blocked)} 个")
        for p in blocked:
            print(f"   → {p['title']} (状态: {p['status']})")
    else:
        print("   ✅ 无进行中项目阻塞")

    # 最后更新
    print("\n---")
    print("建议: 每周运行一次以跟踪系统健康度。")


if __name__ == "__main__":
    main()
