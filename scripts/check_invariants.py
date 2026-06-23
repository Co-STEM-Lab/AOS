#!/usr/bin/env python3
"""
AOS 不变式校验引擎 —— Guardian 的核心判断中枢。

用法：
    python scripts/check_invariants.py              # 人类可读报告
    python scripts/check_invariants.py --json       # 机器可读 JSON (CI / pre-commit)
    python scripts/check_invariants.py --json --fix # 尝试自动修复软违规

退出码：
    0 — 全部通过
    1 — 存在 HARD 违规（pre-commit 应拒绝）
    2 — 仅有 SOFT 警告
    3 — 引擎自身错误

依赖：PyYAML
"""

import sys
import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = ROOT / "knowledge" / "atoms"
SCRIPTS_DIR = ATOMS_DIR / "scripts"
PROJECTS_DIR = ROOT / "projects"
VOCAB_PATH = ROOT / "knowledge" / "controlled-vocabulary.yml"
MATRIX_PATH = ROOT / "matrix.md"
SKILL_TREE_PATH = ROOT / "skills" / "skill-tree.md"


# ─── 工具函数 ───────────────────────────────────────────────

def load_vocab() -> dict:
    """加载受控词汇表。"""
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_front_matter(filepath) -> dict | None:
    """从 Markdown 文件提取 YAML front-matter。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def parse_body(filepath) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    return content[match.end():].strip() if match else content.strip()


def file_mtime(filepath: Path) -> str:
    """文件最后修改时间。"""
    ts = filepath.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def today_str() -> str:
    return date.today().isoformat()


# ─── 不变式检查器 ────────────────────────────────────────────

def check_atom_front_matter(vocab: dict) -> list[dict]:
    """不变式④ 标签一致 + 原子格式校验。"""
    violations = []
    allowed_types = vocab["atom_types"]
    allowed_statuses = vocab["atom_statuses"]
    allowed_tags = vocab["structure_tags"]
    id_map = {v: k for k, v in vocab["id_prefix_map"].items()}

    for f in sorted(ATOMS_DIR.glob("*.md")):
        if f.name.startswith("example-"):
            continue

        fm = parse_front_matter(str(f))
        if not fm:
            violations.append({
                "level": "HARD",
                "invariant": "标签一致",
                "file": str(f.relative_to(ROOT)),
                "message": "无法解析 front-matter",
                "fix": "检查 YAML 语法（--- 块是否正确闭合）",
            })
            continue

        atom_id = fm.get("id", "")
        atom_type = fm.get("type", "")
        tags = fm.get("tags", [])
        pid = fm.get("project", "")
        status = fm.get("status", "draft")

        # 检查 id 格式
        if not re.match(r"^(gap|method|result|insight|compute)-\d{4}$", atom_id):
            expected_prefix = id_map.get(atom_type, "type")
            violations.append({
                "level": "HARD",
                "invariant": "标签一致",
                "file": str(f.relative_to(ROOT)),
                "field": "id",
                "value": atom_id,
                "message": f"id 格式错误，应为 {expected_prefix}-NNNN (4 位数字)",
                "fix": f"将 id 改为 {expected_prefix}-XXXX",
            })

        # 检查 id 前缀与 type 一致
        if atom_type and atom_id:
            prefix = atom_id.split("-")[0] if "-" in atom_id else ""
            expected = vocab["id_prefix_map"].get(atom_type, "")
            if expected and prefix != expected:
                violations.append({
                    "level": "HARD",
                    "invariant": "标签一致",
                    "file": str(f.relative_to(ROOT)),
                    "field": "id",
                    "value": atom_id,
                    "message": f"id 前缀 '{prefix}' 与 type '{atom_type}' 不一致（预期前缀 '{expected}'）",
                    "fix": f"将 type 改为 {prefix}，或将 id 前缀改为 {expected}",
                })

        # 检查 type
        if atom_type not in allowed_types:
            violations.append({
                "level": "HARD",
                "invariant": "标签一致",
                "file": str(f.relative_to(ROOT)),
                "field": "type",
                "value": atom_type,
                "message": f"type 不在受控词汇表: {allowed_types}",
                "fix": f"从 {allowed_types} 中选择正确的 type",
            })

        # 检查 status
        if status not in allowed_statuses:
            violations.append({
                "level": "HARD",
                "invariant": "标签一致",
                "file": str(f.relative_to(ROOT)),
                "field": "status",
                "value": status,
                "message": f"status 不在受控词汇表: {allowed_statuses}",
                "fix": f"改为 draft 或 final",
            })

        # 检查标签
        has_structure_tag = False
        if tags:
            for tag in tags:
                if tag in allowed_tags:
                    has_structure_tag = True
                elif tag.startswith("#"):
                    # 可能是领域标签，也可能是结构标签的拼写错误
                    # 模糊匹配：如果与任一结构标签编辑距离很近，视为疑似拼写错误
                    suggestions = [t for t in allowed_tags if tag[:3] == t[:3] or tag[-2:] == t[-2:]]
                    if suggestions:
                        violations.append({
                            "level": "HARD",
                            "invariant": "标签一致",
                            "file": str(f.relative_to(ROOT)),
                            "field": "tags",
                            "value": tag,
                            "message": f"标签 '{tag}' 疑似结构标签拼写错误，近似匹配: {suggestions}",
                            "fix": f"改为 {suggestions[0]}（或确认此为领域标签后忽略此警告）",
                        })
                    # 否则视为领域标签，允许通过
        else:
            violations.append({
                "level": "SOFT",
                "invariant": "标签一致",
                "file": str(f.relative_to(ROOT)),
                "field": "tags",
                "message": "tags 为空，缺少结构标签和领域标签",
                "fix": "至少添加 1 个结构标签 + 1 个领域标签",
            })

        # 缺少结构标签
        if tags and not has_structure_tag:
            violations.append({
                "level": "SOFT",
                "invariant": "标签一致",
                "file": str(f.relative_to(ROOT)),
                "field": "tags",
                "value": tags,
                "message": f"缺少结构标签（需至少包含 {allowed_tags} 之一）",
                "fix": f"添加一个结构标签，如 {allowed_tags[0]}",
            })

        # 检查 project 字段
        if not pid:
            violations.append({
                "level": "SOFT",
                "invariant": "标签一致",
                "file": str(f.relative_to(ROOT)),
                "field": "project",
                "value": "",
                "message": "project 字段为空或缺失",
                "fix": "填入关联项目 id，或填 'uncategorized'",
            })

        # 计算原子专项检查
        if atom_type == "compute":
            script = fm.get("script", "")
            if not script:
                violations.append({
                    "level": "HARD",
                    "invariant": "脚本自包含",
                    "file": str(f.relative_to(ROOT)),
                    "field": "script",
                    "message": "compute 类型原子缺少 script 字段",
                    "fix": "填入 scripts/ 下的脚本文件名",
                })
            else:
                script_path = SCRIPTS_DIR / script
                if not script_path.exists():
                    violations.append({
                        "level": "HARD",
                        "invariant": "脚本自包含",
                        "file": str(f.relative_to(ROOT)),
                        "field": "script",
                        "value": script,
                        "message": f"脚本文件不存在: {script_path.relative_to(ROOT)}",
                        "fix": "创建脚本文件或修正文件名",
                    })

    return violations


def check_matrix_project_coupling(vocab: dict) -> list[dict]:
    """不变式③ 矩阵封闭 — 每个项目必须在矩阵中，矩阵中的引用必须有效。"""
    violations = []

    # 1. 从 matrix.md 提取所有项目引用（跳过示例区域）
    if not MATRIX_PATH.exists():
        return [{"level": "SOFT", "invariant": "矩阵封闭",
                 "file": "matrix.md", "message": "matrix.md 不存在"}]

    matrix_content = MATRIX_PATH.read_text(encoding="utf-8")
    # 去掉"使用示例"区域（该区域引用仅为格式示范）
    example_start = matrix_content.find("## 使用示例")
    if example_start > 0:
        # 找到示例区域后的下一个 ##
        next_section = matrix_content.find("\n## ", example_start + 1)
        if next_section > 0:
            matrix_content = matrix_content[:example_start] + matrix_content[next_section:]
        else:
            matrix_content = matrix_content[:example_start]

    # 匹配 [proj-xxx](...) 形式的链接
    matrix_projects = set(re.findall(r'\[(proj-\w+)\]\(', matrix_content))

    # 2. 扫描所有项目
    all_projects = set()
    project_map = {}  # id -> (bucket, relative_path)
    for bucket in vocab["project_buckets"]:
        bucket_dir = PROJECTS_DIR / bucket
        if not bucket_dir.is_dir():
            continue
        for proj_dir in bucket_dir.iterdir():
            if not proj_dir.is_dir():
                continue
            idx = proj_dir / "index.md"
            if not idx.exists():
                continue
            fm = parse_front_matter(str(idx))
            pid = fm.get("id", proj_dir.name) if fm else proj_dir.name
            all_projects.add(pid)
            project_map[pid] = (bucket, str(idx.relative_to(ROOT)))

    # 3. 矩阵中的引用是否有效？
    for ref in matrix_projects:
        if ref not in all_projects:
            violations.append({
                "level": "HARD",
                "invariant": "矩阵封闭",
                "file": "matrix.md",
                "field": "矩阵引用",
                "value": ref,
                "message": f"矩阵引用了不存在的项目: {ref}",
                "fix": f"移除无效引用，或创建 projects/ 下对应项目",
            })

    # 4. 是否有项目未被矩阵引用？（软警告，可能是新项目未更新矩阵）
    unreferenced = all_projects - matrix_projects
    for pid in sorted(unreferenced):
        bucket, path = project_map.get(pid, ("?", "?"))
        violations.append({
            "level": "SOFT",
            "invariant": "矩阵封闭",
            "file": "matrix.md",
            "field": "缺失引用",
            "value": pid,
            "message": f"项目 {pid} 未出现在矩阵中 ({path})",
            "fix": f"在 matrix.md 对应格子中添加 [{pid}]({path})",
        })

    return violations


def check_skill_evidence(vocab: dict) -> list[dict]:
    """不变式② 证据前置 — L3/L4 技能必须有证据。"""
    violations = []
    if not SKILL_TREE_PATH.exists():
        return [{"level": "SOFT", "invariant": "证据前置",
                 "file": "skills/skill-tree.md", "message": "skill-tree.md 不存在"}]

    content = SKILL_TREE_PATH.read_text(encoding="utf-8")
    # 匹配表格行：| 技能名 | L2 或以上 | 证据内容 |
    # 表格格式: | 文献批判性阅读 | L3 | 证据... |
    table_rows = re.findall(r'^\|\s*([^|]+?)\s*\|\s*(L[234])\s*\|\s*([^|]*?)\s*\|', content, re.MULTILINE)

    # 也匹配 -- 的情况
    no_evidence_rows = re.findall(
        r'^\|\s*([^|]+?)\s*\|\s*(--|L[234])\s*\|\s*(\s*)\|', content, re.MULTILINE
    )

    # 更精确：匹配评级的技能
    skill_pattern = re.compile(
        r'^\|\s*([^|]+?)\s*\|\s*(L[234])\s*\|\s*([^|]*?)\s*\|', re.MULTILINE
    )
    for match in skill_pattern.finditer(content):
        skill_name = match.group(1).strip()
        level = match.group(2)
        evidence = match.group(3).strip()

        # 排除表头行
        if skill_name in ("技能", "------", ""):
            continue

        if level in ("L3", "L4") and (not evidence or evidence == "--"):
            violations.append({
                "level": "SOFT",
                "invariant": "证据前置",
                "file": "skills/skill-tree.md",
                "field": skill_name,
                "value": level,
                "message": f"技能 '{skill_name}' 评级为 {level} 但缺少证据",
                "fix": f"填入支撑 {level} 评级的项目或产出证据",
            })

    return violations


def check_script_self_containment(vocab: dict) -> list[dict]:
    """不变式⑥ 脚本自包含 — 检查硬编码路径、未声明依赖。"""
    violations = []
    if not SCRIPTS_DIR.is_dir():
        return violations

    for script_file in sorted(SCRIPTS_DIR.glob("*.py")):
        content = script_file.read_text(encoding="utf-8")

        rel = str(script_file.relative_to(ROOT))

        # 检查硬编码绝对路径（启发式）
        abs_paths = re.findall(r'["\'](/home/|/Users/|/tmp/|/var/)\S*["\']', content)
        if abs_paths:
            violations.append({
                "level": "SOFT",
                "invariant": "脚本自包含",
                "file": rel,
                "value": abs_paths[0][:60],
                "message": f"脚本包含硬编码绝对路径 (共 {len(abs_paths)} 处)",
                "fix": "改用相对路径或通过 --input 参数传入",
            })

        # 检查 import 是否有对应的 script_deps
        imports = set(re.findall(r'^\s*(?:import|from)\s+(\w+)', content, re.MULTILINE))
        stdlib = {"sys", "os", "re", "json", "csv", "math", "argparse", "subprocess",
                  "pathlib", "datetime", "collections", "shlex", "glob", "typing",
                  "io", "textwrap", "itertools", "functools", "hashlib", "random",
                  "shutil", "tempfile", "logging", "unittest", "pdb", "traceback",
                  "copy", "enum", "dataclasses", "contextlib", "abc", "ast", "inspect",
                  "types", "warnings", "weakref", "pprint", "string", "struct"}
        external = imports - stdlib
        # 不对未声明的 import 报 HARD（可能是标准库的边界情况），报 SOFT
        # 更实际的检查：找对应原子文件，看 script_deps 是否覆盖
        # 这里做简单版本：不匹配原子，只标记有外部依赖的脚本
        if external:
            # 尝试找对应的 compute atom
            script_name = script_file.stem  # e.g. compute-0001
            atom_file = ATOMS_DIR / f"{script_name}.md"
            if atom_file.exists():
                atom_fm = parse_front_matter(str(atom_file))
                if atom_fm:
                    declared = set(atom_fm.get("script_deps", []))
                    undeclared = external - declared
                    if undeclared:
                        violations.append({
                            "level": "SOFT",
                            "invariant": "脚本自包含",
                            "file": rel,
                            "value": ", ".join(sorted(undeclared)),
                            "message": f"外部库未在 atom front-matter script_deps 中声明: {', '.join(sorted(undeclared))}",
                            "fix": f"在对应 compute atom 的 script_deps 中添加: {sorted(undeclared)}",
                        })

    return violations


def check_atom_independence(vocab: dict) -> list[dict]:
    """不变式① 原子独立可引用 — 检查原子是否包含对特定项目的硬依赖。"""
    violations = []
    for f in sorted(ATOMS_DIR.glob("*.md")):
        if f.name.startswith("example-"):
            continue
        body = parse_body(str(f))
        rel = str(f.relative_to(ROOT))

        # 检测：正文中硬编码了具体项目路径
        # 如 "../../projects/active/proj-xxx" 
        project_paths = re.findall(r'(?:\.\./)*projects/(?:active|completed|ideas)/\S+', body)
        if project_paths:
            violations.append({
                "level": "SOFT",
                "invariant": "原子独立可引用",
                "file": rel,
                "value": project_paths[0][:80],
                "message": "原子正文包含硬编码项目路径，可能损害独立性",
                "fix": "改用项目 id 引用而非文件路径",
            })

    return violations


# ─── 自动修复 ──────────────────────────────────────────────────

def auto_fix(violations: list[dict]) -> int:
    """尝试自动修复 SOFT 违规。返回修复数量。"""
    fixed = 0
    for v in violations:
        if v["level"] != "SOFT":
            continue
        # 当前仅支持几种可自动修复的模式
        if v.get("field") == "project" and v.get("value") == "":
            fpath = ROOT / v["file"]
            content = fpath.read_text(encoding="utf-8")
            new_content = re.sub(
                r'(project:\s*)""',
                r'\1"uncategorized"',
                content,
                count=1
            )
            if new_content != content:
                fpath.write_text(new_content, encoding="utf-8")
                fixed += 1
    return fixed


# ─── 主入口 ───────────────────────────────────────────────────

def main():
    json_mode = "--json" in sys.argv
    fix_mode = "--fix" in sys.argv

    if not VOCAB_PATH.exists():
        msg = {"error": f"词汇表不存在: {VOCAB_PATH}"}
        print(json.dumps(msg, ensure_ascii=False) if json_mode else msg["error"])
        sys.exit(3)

    try:
        vocab = load_vocab()
    except Exception as e:
        msg = {"error": f"词汇表解析失败: {e}"}
        print(json.dumps(msg, ensure_ascii=False) if json_mode else msg["error"])
        sys.exit(3)

    # 收集所有违规
    all_violations = []
    all_violations.extend(check_atom_front_matter(vocab))
    all_violations.extend(check_matrix_project_coupling(vocab))
    all_violations.extend(check_skill_evidence(vocab))
    all_violations.extend(check_script_self_containment(vocab))
    all_violations.extend(check_atom_independence(vocab))

    hard = [v for v in all_violations if v["level"] == "HARD"]
    soft = [v for v in all_violations if v["level"] == "SOFT"]

    # 自动修复
    if fix_mode and soft:
        fixed = auto_fix(soft)
        if fixed > 0:
            # 重新检查（简化：只重跑 atom front-matter 检查）
            all_violations = check_atom_front_matter(vocab)
            all_violations.extend(check_matrix_project_coupling(vocab))
            all_violations.extend(check_skill_evidence(vocab))
            all_violations.extend(check_script_self_containment(vocab))
            all_violations.extend(check_atom_independence(vocab))
            hard = [v for v in all_violations if v["level"] == "HARD"]
            soft = [v for v in all_violations if v["level"] == "SOFT"]

    if json_mode:
        report = {
            "timestamp": today_str(),
            "summary": {
                "total_violations": len(all_violations),
                "hard": len(hard),
                "soft": len(soft),
                "pass": len(all_violations) == 0,
            },
            "hard_violations": hard,
            "soft_violations": soft,
            "exit_code": 1 if hard else (2 if soft else 0),
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        # 人类可读输出
        print("=" * 60)
        print("  AOS 不变式校验")
        print("=" * 60)
        print(f"  时间: {today_str()}")
        print(f"  HARD 违规: {len(hard)} | SOFT 警告: {len(soft)}")
        print()

        if not all_violations:
            print("✅ 全部不变式通过。")
        else:
            for level_label, vlist in [("🔴 HARD 违规 (阻断提交)", hard), ("🟡 SOFT 警告", soft)]:
                if not vlist:
                    continue
                print(f"## {level_label}\n")
                for v in vlist:
                    print(f"  📄 {v['file']}")
                    print(f"     不变式: {v['invariant']}")
                    print(f"     {v['message']}")
                    if v.get("fix"):
                        print(f"     → 修复: {v['fix']}")
                    print()
            print("---")
            if hard:
                print("❌ 存在 HARD 违规。请修复后重新提交。")
            if soft:
                print("🟡 存在 SOFT 警告。建议在下次维护中处理。")

    # 退出码
    if hard:
        sys.exit(1)
    elif soft:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
