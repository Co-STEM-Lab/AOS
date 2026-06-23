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
SKILL_TREE_PATH = ROOT / "competencies" / "skill-tree.md"
README_PATH = ROOT / "README.md"
CLAUDE_PATH = ROOT / "CLAUDE.md"


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
    matrix_projects = set(re.findall(r'\[(proj-[\w-]+)\]\(', matrix_content))

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
                 "file": "competencies/skill-tree.md", "message": "skill-tree.md 不存在"}]

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
                "file": "competencies/skill-tree.md",
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


def check_documentation_consistency(vocab: dict) -> list[dict]:
    """不变式⑦ 文档同步 — README/CLAUDE.md 与实际项目结构一致。"""
    violations = []

    # ── 实际文件系统 ──
    actual_dirs = set()
    actual_scripts = set()
    actual_skills = set()
    for d in ROOT.rglob("*"):
        if d.is_dir() and d.name not in ("venv", "__pycache__", ".git", "node_modules"):
            parts = d.relative_to(ROOT).parts
            # 允许 .claude 目录，排除其他隐藏目录
            if parts[0].startswith(".") and parts[0] != ".claude":
                continue
            actual_dirs.add(str(d.relative_to(ROOT)))
    for f in (ROOT / "scripts").glob("*.py"):
        actual_scripts.add(f.name)
    # 只取顶层 skill 文件（排除 qian-skill/references/ 等子目录参考文件）
    skills_root = ROOT / ".claude" / "skills"
    if skills_root.is_dir():
        for f in skills_root.glob("*.md"):
            actual_skills.add(f.name)
        # 也收录 skill 子目录的 SKILL.md（如 qian-skill/SKILL.md）
        for skill_dir in skills_root.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                actual_skills.add(f"{skill_dir.name}/SKILL.md")

    # ── README.md 中的目录树 vs 实际 ──
    if README_PATH.exists():
        readme = README_PATH.read_text(encoding="utf-8")
        # 提取 README 中声明的目录
        readme_dirs = set(re.findall(r'├──\s+(\S+/)\s+#', readme))
        readme_dirs.update(re.findall(r'└──\s+(\S+/)\s+#', readme))

        # README 声称存在但实际不存在
        for d in sorted(readme_dirs):
            d_clean = d.rstrip("/")
            if d_clean and d_clean not in actual_dirs and d_clean not in ("knowledge/", "outputs/", "projects/", "templates/", "competencies/", ".claude/", "data/"):
                pass  # 父级目录可能包含子目录
            # 检查特定目录
        for check_dir in ["knowledge/atoms/scripts", "knowledge/atoms", "competencies", ".claude/skills", ".claude/rules"]:
            if check_dir not in actual_dirs:
                violations.append({
                    "level": "HARD",
                    "invariant": "文档同步",
                    "file": "README.md",
                    "field": "目录结构",
                    "value": check_dir,
                    "message": f"README 声明了目录 '{check_dir}' 但实际不存在",
                    "fix": f"创建目录或从 README 中移除引用",
                })

        # 实际存在但 README 未声明的重要目录/文件（用简单子串匹配，避免树形 regex 误报）
        for check_name in ["knowledge/atoms/scripts", "knowledge/controlled-vocabulary.yml",
                          "knowledge/maintenance-log.md", "CLAUDE.md", "data"]:
            if (ROOT / check_name).exists():
                # 取最后一级路径组件匹配
                basename = Path(check_name).name
                if basename not in readme and check_name not in readme:
                    violations.append({
                        "level": "SOFT",
                        "invariant": "文档同步",
                        "file": "README.md",
                        "field": "目录结构",
                        "value": check_name,
                        "message": f"'{check_name}' 实际存在但 README 未提及",
                        "fix": "在 README 目录树中添加此项",
                    })

    # ── CLAUDE.md 脚本列表 vs 实际 ──
    if CLAUDE_PATH.exists():
        claude = CLAUDE_PATH.read_text(encoding="utf-8")
        claude_scripts = set(re.findall(r'scripts/(\S+\.py)', claude))
        for s in sorted(actual_scripts):
            if s not in claude_scripts:
                violations.append({
                    "level": "SOFT",
                    "invariant": "文档同步",
                    "file": "CLAUDE.md",
                    "field": "脚本列表",
                    "value": s,
                    "message": f"脚本 scripts/{s} 实际存在但 CLAUDE.md 未列出",
                    "fix": f"在 CLAUDE.md 核心脚本节添加 scripts/{s}",
                })
        for s in sorted(claude_scripts):
            if s not in actual_scripts:
                violations.append({
                    "level": "HARD",
                    "invariant": "文档同步",
                    "file": "CLAUDE.md",
                    "field": "脚本列表",
                    "value": s,
                    "message": f"CLAUDE.md 引用了不存在的脚本 scripts/{s}",
                    "fix": f"移除或修正 CLAUDE.md 中的引用",
                })

    # ── CLAUDE.md 技能列表 vs 实际 ──
    if CLAUDE_PATH.exists():
        claude_text = CLAUDE_PATH.read_text(encoding="utf-8")
        # 从表格中提取所有文件路径引用（第二列或任意位置）
        claude_skill_files = set(re.findall(r'\.claude/skills/\S+\.md', claude_text))
        claude_skill_names = set(re.findall(r'`(\S+)`\s*\|', claude_text))
        for s in sorted(actual_skills):
            # 匹配文件名或逻辑名
            file_ref = f".claude/skills/{s}" if not s.startswith("qian-skill") else f".claude/skills/{s}"
            if s not in claude_skill_names and not any(s in ref or ref.endswith(s) for ref in claude_skill_files):
                violations.append({
                    "level": "SOFT",
                    "invariant": "文档同步",
                    "file": "CLAUDE.md",
                    "field": "Skills 列表",
                    "value": s,
                    "message": f"Skill '{s}' 实际存在但 CLAUDE.md 未列出",
                    "fix": "在 CLAUDE.md Skills 表格中添加此项",
                })

    # ── README 与 Rules 的不变式关键词一致性 ──
    if README_PATH.exists():
        rules_path = ROOT / ".claude" / "rules" / "aos-guardian.md"
        if rules_path.exists():
            readme_text = README_PATH.read_text(encoding="utf-8")
            rules_text = rules_path.read_text(encoding="utf-8")
            # 检查 Rules 中的每条不变式关键词是否在 README 中出现
            rule_invariants = re.findall(r'\*\*([^*]+)\*\*', rules_text)
            for inv in rule_invariants:
                if len(inv) > 4 and inv not in readme_text:
                    violations.append({
                        "level": "SOFT",
                        "invariant": "文档同步",
                        "file": "README.md",
                        "field": "不变式",
                        "value": inv,
                        "message": f"Rules 中的不变式 '{inv}' 未在 README 中找到",
                        "fix": "在 README 不变式列表中添加此项",
                    })

    return violations


# ─── 文档同步生成器 ────────────────────────────────────────────

# 目录 → 注释映射（README 树用的中文说明）
DIR_COMMENTS = {
    "CLAUDE.md": "🤖 AI 入口（每次对话自动加载）",
    "README.md": "本文件",
    "matrix.md": "🎯 研究领域 × 核心问题矩阵",
    ".claude/": "AI 配置",
    ".claude/rules/": "硬约束",
    ".claude/skills/": "协作技能",
    "knowledge/": "🧠 知识库",
    "knowledge/atoms/": "产出原子（最小可重组知识单元）",
    "knowledge/atoms/scripts/": "计算原子配套的可复用脚本",
    "knowledge/literature/": "文献笔记",
    "knowledge/datasets/": "数据集描述",
    "knowledge/controlled-vocabulary.yml": "受控标签词汇表",
    "knowledge/maintenance-log.md": "系统维护日志",
    "competencies/": "💪 人的学术能力库",
    "competencies/skill-tree.md": "技能树（自评 + 证据 + 成长路径）",
    "projects/": "🔄 项目管线",
    "projects/active/": "进行中",
    "projects/completed/": "已完成",
    "projects/ideas/": "想法池",
    "outputs/": "📄 聚合产物",
    "outputs/papers/": "论文草稿",
    "outputs/proposals/": "基金本子",
    "outputs/talks/": "演讲 slides",
    "templates/": "📋 标准化模板",
    "templates/atom-template.md": "原子模板",
    "templates/project-template.md": "项目卡片模板",
    "templates/skill-template.md": "技能项模板",
    "templates/paper-template.md": "论文草稿模板",
    "scripts/": "🔧 辅助工具",
    "scripts/scan.py": "统一扫描入口",
    "scripts/check_invariants.py": "不变式校验引擎",
    "scripts/check_status.py": "系统健康度 + 新鲜度",
    "scripts/aggregate.py": "聚合原子生成初稿",
    "scripts/install-hooks.sh": "安装 pre-commit hook",
    "scripts/smoke.py": "全量烟雾测试（= run-aos driver）",
    "data/": "📊 示例/测试数据",
}


def build_tree_entries(root: Path, prefix: str = "") -> list[str]:
    """递归扫描目录，生成 README 树条目。"""
    entries = []
    items = sorted(
        [p for p in root.iterdir()
         if p.name not in ("venv", "__pycache__", ".git", ".gitignore",
                           ".claude", "__init__.py") and not p.name.endswith(".pyc")],
        key=lambda x: (x.is_file(), x.name.lower())
    )

    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        connector = "└── " if is_last else "├── "
        indent_next = "    " if is_last else "│   "

        rel = str(item.relative_to(ROOT))
        name = item.name + ("/" if item.is_dir() else "")
        key = rel + ("/" if item.is_dir() else "")

        comment = DIR_COMMENTS.get(rel, DIR_COMMENTS.get(key, ""))
        line = f"{prefix}{connector}{name}"
        if comment:
            line += f"{' ' * max(1, 30 - len(name))}# {comment}"
        entries.append(line)

        if item.is_dir():
            entries.extend(build_tree_entries(item, prefix + indent_next))

    return entries


def build_readme_tree() -> str:
    """从实际文件系统生成完整的 README 目录树。"""
    top = [
        f"├── CLAUDE.md{' ' * 21}# 🤖 AI 入口（每次对话自动加载）",
        f"├── README.md{' ' * 22}# 本文件",
        f"├── matrix.md{' ' * 21}# 🎯 研究领域 × 核心问题矩阵",
        "│",
    ]
    # .claude/ 单独处理
    if (ROOT / ".claude").is_dir():
        top.append(".claude/".rjust(4) + "├── .claude/" + " " * 22 + "# AI 配置")
        if (ROOT / ".claude" / "rules").is_dir():
            top.append(".claude/rules/".rjust(4) + "│   ├── rules/" + " " * 27 + "# 硬约束")
        if (ROOT / ".claude" / "skills").is_dir():
            top.append(".claude/skills/".rjust(4) + "│   └── skills/" + " " * 26 + "# 协作技能")
        top.append("│")

    # 其余顶级目录
    rest_dirs = ["knowledge", "competencies", "projects", "outputs", "templates", "scripts", "data"]
    for d in rest_dirs:
        dpath = ROOT / d
        if not dpath.exists():
            continue
        entries = build_tree_entries(dpath, "│   " if d != "data" else "    ")
        rel = d + "/"
        comment = DIR_COMMENTS.get(rel, "")
        prefix = "├── " if d != "data" else "└── "
        line = f"{prefix}{d}/"
        if comment:
            line += f"{' ' * max(1, 30 - len(d))}# {comment}"
        top.append(line)
        for entry in entries:
            top.append(entry)
        if d != "data":
            top.append("│")
        else:
            break

    return "academic-operating-system/\n" + "\n".join(top)


def sync_readme_tree(readme_content: str) -> str:
    """用实际文件系统重建 README 中的目录树块。"""
    tree = build_readme_tree()
    # 找到 ``` 包围的树块并替换
    pattern = r'(academic-operating-system/\n)(.*?)(\n```)'
    return re.sub(pattern, tree + r'\3', readme_content, count=1, flags=re.DOTALL)


def sync_claude_scripts(claude_content: str) -> str:
    """同步 CLAUDE.md 中的脚本列表与 scripts/ 实际文件。"""
    scripts = sorted(
        [f.name for f in (ROOT / "scripts").glob("*") if f.suffix in (".py", ".sh")]
    )
    lines = []
    for s in scripts:
        comments = DIR_COMMENTS.get(f"scripts/{s}", "")
        comment = f"  # {comments}" if comments else ""
        lines.append(f"python scripts/{s}{comment}")

    new_block = "```bash\n" + "\n".join(lines) + "\n```"

    # 替换 "## 核心脚本" 后的第一个 ```bash 块
    pattern = r'(## 核心脚本\n\n)```bash\n.*?\n```'
    return re.sub(pattern, r'\1' + new_block, claude_content, count=1, flags=re.DOTALL)


def sync_claude_skills(claude_content: str) -> str:
    """同步 CLAUDE.md 中的 Skills 表格与 .claude/skills/ 实际文件。"""
    skills_root = ROOT / ".claude" / "skills"
    if not skills_root.is_dir():
        return claude_content

    rows = ["| Skill | 文件 | 用途 | 触发词 |",
            "|-------|------|------|--------|"]

    skill_info = {
        "qian-skill": (".claude/skills/qian-skill/SKILL.md",
                       "钱学森系统科学方法论——复杂工程诊断 + 总体设计 + 涌现检查",
                       "多模块/跨服务/重构/性能排查时自动启用"),
        "aos-guardian": (".claude/skills/aos-guardian.md",
                         "系统守护——不变式巡检 + 新鲜度漂移 + 修复提案",
                         '"检查 AOS" / "守护" / "维护"'),
        "aos-operations": (".claude/skills/aos-operations.md",
                           "操作引导——建原子/建项目/改词汇表/出初稿时自动检查",
                           "任何 AOS 文件修改操作时自动启用"),
        "run-aos": (".claude/skills/run-aos/SKILL.md",
                    "构建、运行、烟雾测试 AOS 全部 CLI 入口",
                    '"run AOS" / "test AOS" / "verify AOS"'),
    }

    for skill_dir in sorted(skills_root.iterdir()):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            name = skill_dir.name
            if name not in skill_info:
                skill_info[name] = (f".claude/skills/{name}/SKILL.md", "", "")
        elif skill_dir.is_file() and skill_dir.suffix == ".md":
            name = skill_dir.stem
            if name not in skill_info:
                skill_info[name] = (f".claude/skills/{skill_dir.name}", "", "")

    for name, (path, purpose, trigger) in sorted(skill_info.items()):
        if not (skills_root / name).exists() and not (skills_root / (name + ".md")).exists():
            # Try alternate names
            found = False
            for f in skills_root.glob(f"{name}*"):
                found = True
                break
            if not found and name not in ("qian-skill", "aos-guardian", "aos-operations", "run-aos"):
                continue
        rows.append(f"| `{name}` | `{path}` | {purpose} | {trigger} |")

    new_table = "\n".join(rows)
    pattern = r'(\| Skill \| 文件 \| 用途 \| 触发词 \|\n\|-------\|------\|------\|--------\|\n)(.*?)(\n\n##)'
    return re.sub(pattern, r'\1' + "\n".join(rows[2:]) + r'\3', claude_content, count=1, flags=re.DOTALL)


def sync_matrix_entries(matrix_content: str) -> str:
    """根据所有项目的 domain/problem 自动填充矩阵。"""
    lines = matrix_content.split("\n")
    table_start = sep_line = table_end = -1

    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("| 研究领域") or s.startswith("| Research Domain"):
            table_start = i
        elif table_start >= 0 and s.startswith("|") and "---" in s:
            sep_line = i
        elif sep_line >= 0 and table_start >= 0 and not s.startswith("|"):
            table_end = i
            break

    if table_start < 0 or sep_line < 0:
        return matrix_content
    if table_end < 0:
        table_end = len(lines)

    # 提取列名（跳过 HTML 注释占位）
    header_cells = [c.strip() for c in lines[table_start].split("|")[1:-1]]
    problems = []
    for h in header_cells[1:]:
        if h.startswith("<!--"):
            continue  # 跳过注释占位列
        problems.append(h)

    # 提取现有行: domain → [cell, cell, ...]
    existing_rows: dict[str, list[str]] = {}
    for i in range(sep_line + 1, table_end):
        line = lines[i]
        if not line.strip().startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 2 and not cells[0].startswith("<!--"):
            existing_rows[cells[0]] = cells[1:]

    # 扫描所有项目
    status_icons = {
        "idea": "💡", "active": "🔬", "writing": "✍️",
        "submitted": "📤", "published": "✅"
    }
    project_cells: dict[tuple[str, str], str] = {}

    for bucket in ["active", "completed", "ideas"]:
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
            if not fm:
                continue
            pid = fm.get("id", proj_dir.name)
            domain = fm.get("domain", "")
            problem = fm.get("problem", "")
            status = fm.get("status", "idea")
            if not domain or not problem:
                continue
            icon = status_icons.get(status, "❓")
            rel = str(idx.relative_to(ROOT).parent)
            project_cells[(domain, problem)] = f"[{pid}]({rel}/) {icon}"

    # 收集所有 domain/problem
    all_domains = list(existing_rows.keys())
    all_problems = list(problems)
    for d, p in project_cells:
        if d not in all_domains:
            all_domains.append(d)
        if p not in all_problems:
            all_problems.append(p)

    # 补全新 domain 的空行
    for d in all_domains:
        if d not in existing_rows:
            existing_rows[d] = ["—"] * len(all_problems)

    # 扩展列
    old_pc = len(problems)
    if len(all_problems) > old_pc:
        for d in existing_rows:
            existing_rows[d].extend(["—"] * (len(all_problems) - old_pc))

    # 清除旧的项目引用（项目已不存在 → 恢复为 "—"）
    all_project_ids = {pid for (d, p), cell in project_cells.items()
                       for pid in [cell.split("]")[0].lstrip("[")] if "proj-" in pid}
    for d in existing_rows:
        for ci in range(len(existing_rows[d])):
            cell = existing_rows[d][ci]
            if cell != "—" and "proj-" in cell:
                ref_id = cell.split("]")[0].lstrip("[")
                if ref_id not in all_project_ids:
                    existing_rows[d][ci] = "—"

    # 填入项目
    for (d, p), cell in project_cells.items():
        if d in existing_rows and p in all_problems:
            pi = all_problems.index(p)
            while len(existing_rows[d]) <= pi:
                existing_rows[d].append("—")
            existing_rows[d][pi] = cell

    # 重建表
    header = "| 研究领域 \\ 核心问题 |" + "|".join(f" {p} " for p in all_problems) + "|"
    sep = "|" + "|".join("---------------------" for _ in range(len(all_problems) + 1)) + "|"
    new_rows = []
    for d in all_domains:
        cells = existing_rows.get(d, ["—"] * len(all_problems))
        new_rows.append("| " + " | ".join([d] + cells) + " |")

    result = lines[:table_start] + [header, sep] + new_rows + lines[table_end:]
    return "\n".join(result)


# ─── 自动修复 ──────────────────────────────────────────────────

def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def _write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def auto_fix(violations: list[dict]) -> int:
    """自动修复可安全处理的违规。返回修复数量。"""
    fixed = 0

    for v in violations:
        fpath = ROOT / v["file"] if "file" in v else None
        if not fpath or not fpath.exists():
            continue

        content = _read_file(fpath)
        new_content = content

        # ① 空白 project → "uncategorized"
        if v.get("field") == "project" and v.get("value", "") == "":
            new_content = re.sub(
                r'(project:\s*)""',
                r'\1"uncategorized"',
                new_content,
                count=1
            )

        # ② 空白 created → 当天日期
        elif v.get("field") == "created" and v.get("value", "") == "":
            new_content = re.sub(
                r'(created:\s*)""',
                f'\\1"{today_str()}"',
                new_content,
                count=1
            )

        # ③ id 前缀与 type 不一致 → 修正 id 前缀匹配 type
        elif v.get("field") == "id" and "前缀" in v.get("message", ""):
            # 从 fix 建议中提取"id 前缀改为 XXX"的正确前缀
            fix_msg = v.get("fix", "")
            prefix_match = re.search(r"id 前缀改为\s+(\w+)", fix_msg)
            if not prefix_match:
                # fallback: 从 atom 的 type 查 id_prefix_map
                prefix_match = re.search(r"type 改为\s+(\w+)", fix_msg)
            if prefix_match:
                correct_prefix = prefix_match.group(1)
            else:
                # 最终 fallback: 直接读 atom 文件取 type，查表
                correct_prefix = None
                for atom_f in ATOMS_DIR.glob("*.md"):
                    if str(atom_f.relative_to(ROOT)) == v["file"]:
                        fm = parse_front_matter(str(atom_f))
                        if fm:
                            atom_type = fm.get("type", "")
                            correct_prefix = load_vocab()["id_prefix_map"].get(atom_type)
                        break
                if not correct_prefix:
                    continue
            new_content = re.sub(
                r'(id:\s*")\w+(-\d{4}")',
                f'\\1{correct_prefix}\\2',
                new_content,
                count=1
            )

        # ④ 空白 script_deps 但脚本有外部 import → 自动推断
        elif v.get("field") == "script" and "script_deps" in v.get("message", ""):
            # 这需要读取脚本内容——在 violation 的 message 中已有 undeclared 列表
            # 更简单：直接找对应的 compute atom，读脚本 import
            dep_match = re.search(r"未声明:\s*(.+)", v.get("message", ""))
            if dep_match:
                deps_str = dep_match.group(1)
                deps = [d.strip() for d in deps_str.split(",")]
                # 在 front-matter 中添加 script_deps
                new_content = re.sub(
                    r'(script_deps:\s*)\[\]',
                    f'\\1{deps}',
                    new_content,
                    count=1
                )

        if new_content != content:
            _write_file(fpath, new_content)
            fixed += 1

    # ── 文档同步修复（有任一漂移 → 全量重建，保证一致）──
    doc_violations = [v for v in violations if v.get("invariant") == "文档同步"]
    if doc_violations:
        # README 目录树：全量重建
        if README_PATH.exists():
            old = _read_file(README_PATH)
            new = sync_readme_tree(old)
            if new != old:
                _write_file(README_PATH, new)
                fixed += 1

        # CLAUDE.md：脚本列表 + Skills 表格 全量重建
        if CLAUDE_PATH.exists():
            old = _read_file(CLAUDE_PATH)
            new = sync_claude_scripts(old)
            new = sync_claude_skills(new)
            if new != old:
                _write_file(CLAUDE_PATH, new)
                fixed += 1

    # ── 矩阵同步修复（项目变更 → 矩阵自动填）──
    matrix_violations = [v for v in violations if v.get("invariant") == "矩阵封闭"]
    if matrix_violations and MATRIX_PATH.exists():
        old = _read_file(MATRIX_PATH)
        new = sync_matrix_entries(old)
        if new != old:
            _write_file(MATRIX_PATH, new)
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
    all_violations.extend(check_documentation_consistency(vocab))

    hard = [v for v in all_violations if v["level"] == "HARD"]
    soft = [v for v in all_violations if v["level"] == "SOFT"]

    # 自动修复（处理全部违规，不区分 HARD/SOFT）
    if fix_mode and all_violations:
        fixed = auto_fix(all_violations)
        if fixed > 0:
            # 重新检查
            all_violations = check_atom_front_matter(vocab)
            all_violations.extend(check_matrix_project_coupling(vocab))
            all_violations.extend(check_skill_evidence(vocab))
            all_violations.extend(check_script_self_containment(vocab))
            all_violations.extend(check_atom_independence(vocab))
            all_violations.extend(check_documentation_consistency(vocab))
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
