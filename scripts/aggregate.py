#!/usr/bin/env python3
"""
聚合管线：按项目提取关联原子，注入论文模板生成初稿。

用法：
    python scripts/aggregate.py <project-id>                  # 纯文本聚合（Markdown）
    python scripts/aggregate.py <project-id> --html            # 直接输出 A4 HTML
    python scripts/aggregate.py <project-id> --html -o paper.html  # 输出到文件
    python scripts/aggregate.py <project-id> --execute         # 执行计算原子并嵌入输出
    python scripts/aggregate.py <project-id> --execute --input data/custom.csv  # 指定输入数据

依赖：
    - PyYAML (pip install pyyaml)
    - knowledge/atoms/ 下的原子文件（含 YAML front-matter）
    - projects/ 下的项目卡片（含 YAML front-matter）
    - --execute 模式下需要计算原子声明的 script_deps 已安装
    - --html 模式下可选 pip install markdown 获得更好渲染
"""

import sys
import os
import io
import subprocess
import json
import shlex
import re
import yaml
from pathlib import Path
from datetime import datetime
from aos_utils import parse_front_matter, parse_body

ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = ROOT / "knowledge" / "atoms"
SCRIPTS_DIR = ATOMS_DIR / "scripts"
PROJECTS_DIR = ROOT / "projects"
CSS_PATH = ROOT / "templates" / "output.css"
HTML_TEMPLATE = ROOT / "templates" / "paper-html.html"



def find_atoms_by_project(project_id: str) -> list[dict]:
    """查找所有属于指定项目的原子。"""
    atoms = []
    for atom_file in ATOMS_DIR.rglob("*.md"):
        if atom_file.parent.name in ("example", "scripts"):
            continue  # 跳过示例文件和脚本目录
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
    html_mode = False
    output_path = None

    # 参数解析
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--execute":
            execute = True
        elif args[i] == "--html":
            html_mode = True
        elif args[i] == "-o" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 1
        elif args[i] == "--input" and i + 1 < len(args):
            input_override = args[i + 1]
            i += 1
        elif not args[i].startswith("-") and project_id is None:
            project_id = args[i]
        i += 1

    if not project_id:
        print("用法: python scripts/aggregate.py <project-id> [--html] [--execute] [-o output.html]")
        print("示例: python scripts/aggregate.py proj-dynamic-X")
        print("      python scripts/aggregate.py proj-dynamic-X --html")
        print("      python scripts/aggregate.py proj-dynamic-X --html -o paper.html")
        print("      python scripts/aggregate.py proj-dynamic-X --execute --html")
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

    # 3. 构建 MD 输出（存到列表，最后决定输出格式）
    out: list[str] = []
    a = out.append  # shorthand

    a(f"# {project_title}")
    a(f"\n> 自动聚合生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    a(f"> 项目 ID: {project_id}")
    a(f"> 关联原子数: {len(atoms)}")
    if execute and compute_count > 0:
        a(f"> 计算原子: {compute_count}（已执行 ✅）")
    elif compute_count > 0:
        a(f"> 计算原子: {compute_count}（未执行，加 --execute 运行）")
    a("")

    # Introduction 段
    if grouped["#引言缺口"]:
        a("## Introduction（缺口 → 动机）\n")
        for atom in grouped["#引言缺口"]:
            a(render_atom(atom, execute, input_override))
            a("")
    else:
        a("## Introduction\n\n<!-- 无缺口原子，请先创建 type=gap 的原子 -->\n")

    # Method 段
    if grouped["#方法组件"]:
        a("## Method（方法组件）\n")
        for atom in grouped["#方法组件"]:
            a(render_atom(atom, execute, input_override))
            a("")

    # Results & Discussion 段
    if grouped["#结果讨论"]:
        a("## Results & Discussion\n")
        for atom in grouped["#结果讨论"]:
            a(render_atom(atom, execute, input_override))
            a("")

    # 其他原子
    if grouped["other"]:
        a("## 其他原子\n")
        for atom in grouped["other"]:
            a(render_atom(atom, execute, input_override))
            a("")

    # 汇总
    a("---")
    a("## 原子索引")
    for group_name, group_atoms in grouped.items():
        if group_atoms:
            a(f"\n### {group_name}")
            for atom in group_atoms:
                compute_mark = " ⚡" if atom["front_matter"].get("type") == "compute" else ""
                a(f"- [{atom['front_matter']['id']}]{compute_mark} {atom['front_matter']['title']}")

    md_text = "\n".join(out)

    # 4. 输出
    if html_mode:
        body_html = md_to_html(md_text)
        html = wrap_html(project_title, body_html)
        if output_path:
            Path(output_path).write_text(html, encoding="utf-8")
            print(f"✅ 已输出 A4 HTML: {output_path}")
        else:
            print(html)
    else:
        print(md_text)


def check_script_deps(project_id: str) -> tuple[bool, list[str]]:
    """检查项目所有计算原子的依赖是否已安装。"""
    missing = set()
    for atom_file in ATOMS_DIR.rglob("*.md"):
        if atom_file.parent.name in ("example", "scripts"):
            continue
        fm = parse_front_matter(str(atom_file))
        if not fm or fm.get("project") != project_id or fm.get("type") != "compute":
            continue
        for dep in fm.get("script_deps", []):
            try:
                __import__(dep.replace("-", "_"))
            except ImportError:
                missing.add(dep)
    return len(missing) == 0, sorted(missing)


# ─── HTML 输出 ──────────────────────────────────────────────

def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline_md(text: str) -> str:
    text = _escape_html(text)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img alt="\1" src="\2">', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def md_to_html(md: str) -> str:
    """Markdown→HTML。优先 markdown 库，fallback 简易转换。"""
    try:
        import markdown as mdlib
        return mdlib.markdown(md, extensions=["tables", "fenced_code"])
    except ImportError:
        pass

    lines = md.split("\n")
    out = []
    in_list = in_ol = in_code = False
    code_buf = []

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                out.append(f'<pre><code>{_escape_html(chr(10).join(code_buf))}</code></pre>')
                code_buf = []; in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line); continue

        if not line.strip():
            if in_list: out.append("</ul>"); in_list = False
            if in_ol: out.append("</ol>"); in_ol = False
            continue

        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            if in_ol: out.append("</ol>"); in_ol = False
            out.append(f"<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>")
            continue

        m = re.match(r"^[-*+]\s+(.+)$", line)
        if m:
            if not in_list: out.append("<ul>"); in_list = True
            out.append(f"<li>{_inline_md(m.group(1))}</li>"); continue

        m = re.match(r"^\d+\.\s+(.+)$", line)
        if m:
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{_inline_md(m.group(1))}</li>"); continue

        m = re.match(r"^>\s?(.*)$", line)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            if in_ol: out.append("</ol>"); in_ol = False
            out.append(f"<blockquote><p>{_inline_md(m.group(1))}</p></blockquote>"); continue

        if in_list: out.append("</ul>"); in_list = False
        if in_ol: out.append("</ol>"); in_ol = False
        out.append(f"<p>{_inline_md(line)}</p>")

    if in_list: out.append("</ul>")
    if in_ol: out.append("</ol>")
    return "\n".join(out)


def wrap_html(title: str, body_html: str) -> str:
    """将正文 HTML 注入 A4 模板，CSS 内联。"""
    css = ""
    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{_escape_html(title)}</title>
<style>
{css}
</style>
</head>
<body>
<div class="page">
<h1>{_escape_html(title)}</h1>
<div class="authors"></div>
<div class="affiliation"></div>
<div class="abstract"><p><strong>摘要：</strong></p></div>
<div class="keywords"><strong>关键词：</strong></div>
{body_html}
</div>
</body>
</html>"""


if __name__ == "__main__":
    main()
