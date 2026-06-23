#!/usr/bin/env python3
"""
聚合管线：按项目提取关联原子，注入论文模板生成初稿。

用法：
    python scripts/aggregate.py <project-id>                  # 纯文本聚合
    python scripts/aggregate.py <project-id> --execute         # 执行计算原子并嵌入输出
    python scripts/aggregate.py <project-id> --execute --input data/custom.csv  # 指定输入数据

依赖：
    - PyYAML (pip install pyyaml)
    - knowledge/atoms/ 下的原子文件（含 YAML front-matter）
    - projects/ 下的项目卡片（含 YAML front-matter）
    - --execute 模式下需要计算原子声明的 script_deps 已安装
"""

import sys
import os
import subprocess
import json
import shlex
import re
import yaml
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = ROOT / "knowledge" / "atoms"
SCRIPTS_DIR = ATOMS_DIR / "scripts"
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


def execute_compute_atom(atom: dict, input_override: str = None) -> str:
    """执行计算原子的脚本并返回格式化输出。"""
    fm = atom["front_matter"]
    script_name = fm.get("script", "")
    if not script_name:
        return "\n<!-- ⚠️ 计算原子缺少 script 字段 -->\n"

    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return f"\n<!-- ⚠️ 脚本未找到: {script_path} -->\n"

    # 构建命令
    cmd = [sys.executable, str(script_path)]
    data_input = input_override or fm.get("script_input", "")
    if data_input:
        # 如果是相对路径，转为绝对路径
        data_path = ROOT / data_input
        if data_path.exists():
            data_input = str(data_path)
        cmd.extend(["--input", data_input])

    # 附加原子声明的额外参数
    extra_args = fm.get("script_args", "")
    if extra_args:
        cmd.extend(shlex.split(extra_args))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(ROOT))
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            return f"\n<!-- ❌ 脚本执行失败 (exit {result.returncode}) -->\n```\n{stderr or output}\n```\n"

        # 尝试格式化 JSON 输出
        try:
            parsed = json.loads(output)
            if "error" in parsed:
                return f"\n<!-- ❌ 脚本返回错误 -->\n```json\n{json.dumps(parsed, indent=2, ensure_ascii=False)}\n```\n"

            # 生成可读的 Markdown 表格
            lines = ["\n**📊 脚本输出：**\n"]

            # 基本信息
            if "test" in parsed:
                lines.append(f"检验方法: {parsed['test']}  ")

            # 分组统计
            for key in ["group_a", "group_b"]:
                if key in parsed:
                    g = parsed[key]
                    label = g.get("label", key)
                    lines.append(f"{label}: n={g.get('n','?')}, mean={g.get('mean','?')}, std={g.get('std','?')}  ")

            # 检验结果
            for k, v in parsed.items():
                if k in ("group_a", "group_b", "test", "input_file"):
                    continue
                if isinstance(v, bool):
                    lines.append(f"{k}: {'✅ 是' if v else '❌ 否'}  ")
                elif isinstance(v, float) and v < 0.001 and k == "p_value":
                    lines.append(f"{k}: {v} (< 0.001, 显著)  ")
                else:
                    lines.append(f"{k}: {v}  ")

            lines.append(f"\n<details>\n<summary>原始 JSON</summary>\n\n```json\n{json.dumps(parsed, indent=2, ensure_ascii=False)}\n```\n</details>\n")
            return "".join(lines)

        except json.JSONDecodeError:
            # 非 JSON 输出，原样呈现
            return f"\n**📊 脚本输出：**\n\n```\n{output}\n```\n"

    except subprocess.TimeoutExpired:
        return "\n<!-- ⚠️ 脚本执行超时 (30s) -->\n"
    except Exception as e:
        return f"\n<!-- ⚠️ 脚本执行异常: {e} -->\n"


def render_atom(atom: dict, execute: bool = False, input_override: str = None) -> str:
    """渲染单个原子为 Markdown 段。"""
    fm = atom["front_matter"]
    lines = [f"### {fm['title']}", "", atom["body"]]

    if execute and fm.get("type") == "compute":
        lines.append(execute_compute_atom(atom, input_override))

    return "\n".join(lines)


def main():
    execute = False
    input_override = None
    project_id = None

    # 参数解析
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--execute":
            execute = True
        elif args[i] == "--input" and i + 1 < len(args):
            input_override = args[i + 1]
            i += 1
        elif not args[i].startswith("--") and project_id is None:
            project_id = args[i]
        i += 1

    if not project_id:
        print("用法: python scripts/aggregate.py <project-id> [--execute] [--input data.csv]")
        print("示例: python scripts/aggregate.py proj-dynamic-X")
        print("      python scripts/aggregate.py proj-dynamic-X --execute")
        print("      python scripts/aggregate.py proj-dynamic-X --execute --input data/custom.csv")
        sys.exit(1)

    if execute:
        # 检查依赖
        deps_ok, missing = check_script_deps(project_id)
        if not deps_ok:
            print(f"⚠️  缺少依赖: {', '.join(missing)}", file=sys.stderr)
            print(f"   安装: pip install {' '.join(missing)}", file=sys.stderr)
            print(f"   或跳过执行: python scripts/aggregate.py {project_id}", file=sys.stderr)

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
    compute_count = sum(1 for a in atoms if a["front_matter"].get("type") == "compute")

    # 3. 输出聚合结果
    print(f"# {project_title}")
    print(f"\n> 自动聚合生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"> 项目 ID: {project_id}")
    print(f"> 关联原子数: {len(atoms)}")
    if execute and compute_count > 0:
        print(f"> 计算原子: {compute_count}（已执行 ✅）")
    elif compute_count > 0:
        print(f"> 计算原子: {compute_count}（未执行，加 --execute 运行）")
    print()

    # Introduction 段：缺口原子
    if grouped["#引言缺口"]:
        print("## Introduction（缺口 → 动机）\n")
        for atom in grouped["#引言缺口"]:
            print(render_atom(atom, execute, input_override))
            print()
    else:
        print("## Introduction\n\n<!-- 无缺口原子，请先创建 type=gap 的原子 -->\n")

    # Method 段：方法原子（含 compute 类型）
    if grouped["#方法组件"]:
        print("## Method（方法组件）\n")
        for atom in grouped["#方法组件"]:
            print(render_atom(atom, execute, input_override))
            print()

    # Results & Discussion 段：结果原子 + 洞察原子
    if grouped["#结果讨论"]:
        print("## Results & Discussion\n")
        for atom in grouped["#结果讨论"]:
            print(render_atom(atom, execute, input_override))
            print()

    # 其他原子
    if grouped["other"]:
        print("## 其他原子\n")
        for atom in grouped["other"]:
            print(render_atom(atom, execute, input_override))
            print()

    # 汇总
    print("---")
    print(f"## 原子索引")
    for group_name, group_atoms in grouped.items():
        if group_atoms:
            print(f"\n### {group_name}")
            for a in group_atoms:
                compute_mark = " ⚡" if a["front_matter"].get("type") == "compute" else ""
                print(f"- [{a['front_matter']['id']}]{compute_mark} {a['front_matter']['title']}")


def check_script_deps(project_id: str) -> tuple[bool, list[str]]:
    """检查项目所有计算原子的依赖是否已安装。"""
    missing = set()
    for atom_file in ATOMS_DIR.glob("*.md"):
        fm = parse_front_matter(str(atom_file))
        if not fm or fm.get("project") != project_id or fm.get("type") != "compute":
            continue
        for dep in fm.get("script_deps", []):
            try:
                __import__(dep.replace("-", "_"))
            except ImportError:
                missing.add(dep)
    return len(missing) == 0, sorted(missing)


if __name__ == "__main__":
    main()
