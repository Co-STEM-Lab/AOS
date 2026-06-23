#!/usr/bin/env python3
"""
聚合管线：按项目提取关联原子，注入论文模板生成初稿。

用法：
    python scripts/aggregate.py <project-id> [--template templates/paper-template.md]

依赖：
    - PyYAML (pip install pyyaml)
    - knowledge/atoms/ 下的原子文件（含 YAML front-matter）
    - projects/ 下的项目卡片（含 YAML front-matter）
"""

import sys
import os
import glob
import re
import yaml
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = ROOT / "knowledge" / "atoms"
PROJECTS_DIR = ROOT / "projects"


def parse_front_matter(filepath: str) -> dict | None:
    """从 Markdown 文件中提取 YAML front-matter。"""
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
    """提取 Markdown 文件的正文（去掉 front-matter）。"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    if match:
        return content[match.end() :].strip()
    return content.strip()


def find_atoms_by_project(project_id: str) -> list[dict]:
    """查找所有属于指定项目的原子。"""
    atoms = []
    for atom_file in ATOMS_DIR.glob("*.md"):
        if atom_file.name.startswith("example-"):
            continue  # 跳过示例文件
        fm = parse_front_matter(str(atom_file))
        if fm and fm.get("project") == project_id:
            body = parse_body(str(atom_file))
            atoms.append({"front_matter": fm, "body": body, "file": atom_file.name})
    return atoms


def group_atoms_by_tag(atoms: list[dict]) -> dict[str, list[dict]]:
    """按结构标签分组原子。"""
    groups = {
        "#引言缺口": [],
        "#方法组件": [],
        "#结果讨论": [],
        "other": [],
    }
    for atom in atoms:
        tags = atom["front_matter"].get("tags", [])
        placed = False
        for tag in tags:
            if tag in groups:
                groups[tag].append(atom)
                placed = True
                break
        if not placed:
            groups["other"].append(atom)
    return groups


def find_project_card(project_id: str) -> Path | None:
    """在各个项目子目录中查找项目卡片。"""
    for subdir in ["active", "completed", "ideas"]:
        project_dir = PROJECTS_DIR / subdir / project_id
        if project_dir.is_dir():
            index_file = project_dir / "index.md"
            if index_file.exists():
                return index_file
    return None


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/aggregate.py <project-id>")
        print("示例: python scripts/aggregate.py proj-dynamic-X")
        sys.exit(1)

    project_id = sys.argv[1]

    # 1. 查找项目卡片
    card_path = find_project_card(project_id)
    if not card_path:
        print(f"❌ 未找到项目: {project_id}")
        print(f"   请在 projects/active/, projects/completed/, 或 projects/ideas/ 下创建项目目录")
        sys.exit(1)

    card_fm = parse_front_matter(str(card_path))
    project_title = card_fm.get("title", project_id) if card_fm else project_id

    # 2. 查找关联原子
    atoms = find_atoms_by_project(project_id)
    if not atoms:
        print(f"⚠️  项目 {project_title} 暂无关联原子")
        print(f"   请在 knowledge/atoms/ 下创建原子，并将 project 字段设为 {project_id}")
        sys.exit(0)

    grouped = group_atoms_by_tag(atoms)

    # 3. 输出聚合结果
    print(f"# {project_title}")
    print(f"\n> 自动聚合生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"> 项目 ID: {project_id}")
    print(f"> 关联原子数: {len(atoms)}")
    print()

    # Introduction 段：缺口原子
    if grouped["#引言缺口"]:
        print("## Introduction（缺口 → 动机）\n")
        for atom in grouped["#引言缺口"]:
            print(f"### {atom['front_matter']['title']}")
            print(atom["body"])
            print()
    else:
        print("## Introduction\n\n<!-- 无缺口原子，请先创建 type=gap 的原子 -->\n")

    # Method 段：方法原子
    if grouped["#方法组件"]:
        print("## Method（方法组件）\n")
        for atom in grouped["#方法组件"]:
            print(f"### {atom['front_matter']['title']}")
            print(atom["body"])
            print()

    # Results & Discussion 段：结果原子 + 洞察原子
    if grouped["#结果讨论"]:
        print("## Results & Discussion\n")
        for atom in grouped["#结果讨论"]:
            print(f"### {atom['front_matter']['title']}")
            print(atom["body"])
            print()

    # 其他原子
    if grouped["other"]:
        print("## 其他原子\n")
        for atom in grouped["other"]:
            print(f"### {atom['front_matter']['title']}")
            print(atom["body"])
            print()

    # 汇总
    print("---")
    print(f"## 原子索引")
    for group_name, group_atoms in grouped.items():
        if group_atoms:
            print(f"\n### {group_name}")
            for a in group_atoms:
                print(f"- [{a['front_matter']['id']}] {a['front_matter']['title']}")


if __name__ == "__main__":
    main()
