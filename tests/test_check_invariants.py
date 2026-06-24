"""
check_invariants.py 的单元测试。

覆盖：front-matter 校验 / 矩阵耦合 / 技能证据 / 脚本自包含 /
      原子独立性 / 证据锚定 / 文档一致性 / 自动修复。

运行：python scripts/test_check_invariants.py
"""

import sys
import os
import tempfile
import json
import unittest
from pathlib import Path

# 确保能从 scripts/ 目录导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_invariants as ci
from aos_utils import parse_front_matter


# ─── 测试基础设施：通过 monkey-patch 全局路径指向临时目录 ─────

def make_vocab(overrides=None):
    """构造最小可用词汇表。"""
    vocab = {
        "atom_types": ["gap", "method", "result", "insight", "compute"],
        "atom_statuses": ["draft", "final"],
        "structure_tags": ["#引言缺口", "#方法组件", "#结果讨论"],
        "id_prefix_map": {
            "gap": "gap", "method": "method", "result": "result",
            "insight": "insight", "compute": "compute",
        },
        "project_buckets": ["active", "completed", "ideas"],
        "project_statuses": ["idea", "active", "writing", "submitted", "published"],
        "skill_categories": ["测试分类"],
        "skill_levels": ["L1", "L2", "L3", "L4"],
    }
    if overrides:
        vocab.update(overrides)
    return vocab


def make_atom_file(dir_path, filename, front_matter_lines, body_text="# 核心断言\n\n测试正文。"):
    """在指定目录创建原子文件。"""
    path = Path(dir_path) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = "\n".join(front_matter_lines)
    content = f"---\n{fm}\n---\n\n{body_text}"
    path.write_text(content, encoding="utf-8")
    return path


class FixtureSandbox:
    """在临时目录中搭建 AOS 文件结构，并替换 ci 模块的全局路径。"""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def setup_dirs(self):
        """创建知识库和项目目录。"""
        (self.root / "knowledge" / "atoms").mkdir(parents=True, exist_ok=True)
        (self.root / "knowledge" / "atoms" / "scripts").mkdir(parents=True, exist_ok=True)
        (self.root / "projects" / "active").mkdir(parents=True, exist_ok=True)
        (self.root / "projects" / "completed").mkdir(parents=True, exist_ok=True)
        (self.root / "projects" / "ideas").mkdir(parents=True, exist_ok=True)

    def bind(self):
        """将 ci 模块的路径常量重定向到临时目录。"""
        self._orig = {}
        # 保存原始 ROOT，所有相对路径计算以此为基准
        orig_root = ci.ROOT
        for attr in ("ROOT", "ATOMS_DIR", "SCRIPTS_DIR", "PROJECTS_DIR",
                      "VOCAB_PATH", "MATRIX_PATH", "SKILL_TREE_PATH",
                      "README_PATH", "CLAUDE_PATH"):
            orig_val = getattr(ci, attr)
            self._orig[attr] = orig_val
            if attr == "ROOT":
                setattr(ci, attr, self.root)
            else:
                setattr(ci, attr, self.root / Path(orig_val).relative_to(orig_root))

    def unbind(self):
        """恢复原始路径。"""
        for attr, val in self._orig.items():
            setattr(ci, attr, val)

    def cleanup(self):
        self.tmp.cleanup()

    def at(self, *parts):
        return self.root.joinpath(*parts)


# ─── 测试类 ──────────────────────────────────────────────────

class TestAtomFrontMatter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = FixtureSandbox()
        cls.sandbox.setup_dirs()
        cls.sandbox.bind()

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.unbind()
        cls.sandbox.cleanup()

    def setUp(self):
        # 每次测试前清空原子目录
        atoms_dir = self.sandbox.at("knowledge", "atoms")
        for f in atoms_dir.rglob("*.md"):
            f.unlink()

    def test_valid_atom_no_violations(self):
        """合法的原子不应产生违规。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "gap-test-gap.md",
            [
                'id: "gap-test-gap"',
                'title: "测试缺口"',
                'type: gap',
                'tags: ["#引言缺口", "#金相分析"]',
                'project: "proj-test"',
                'status: draft',
                'source: "Zhang 2023"',
                'created: "2026-01-01"',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertEqual(len(violations), 0,
                         f"Expected 0 violations, got: {violations}")

    def test_missing_front_matter(self):
        """缺少 front-matter 的原子应报 HARD 违规。"""
        p = self.sandbox.at("knowledge", "atoms", "bad.md")
        p.write_text("# 没有 front-matter", encoding="utf-8")
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertTrue(any(v["level"] == "HARD" and "无法解析" in v["message"]
                            for v in violations))

    def test_id_prefix_mismatch(self):
        """id 前缀与 type 不一致应报 HARD。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "result-bad-prefix.md",
            [
                'id: "result-bad-prefix"',
                'title: "结果"',
                'type: gap',
                'tags: ["#引言缺口", "#金相分析"]',
                'project: "proj-test"',
                'status: draft',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertTrue(any("前缀" in v.get("message", "") for v in violations))

    def test_unknown_type(self):
        """不在词汇表中的 type 应报 HARD。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "bad-type.md",
            [
                'id: "bad-type"',
                'title: "坏类型"',
                'type: unknown_type',
                'tags: ["#引言缺口"]',
                'project: "proj-test"',
                'status: draft',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertTrue(any("不在受控词汇表" in v.get("message", "") for v in violations))

    def test_compute_atom_missing_script(self):
        """compute 类型原子缺少 script 字段应报 HARD。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "compute-no-script.md",
            [
                'id: "compute-no-script"',
                'title: "无脚本"',
                'type: compute',
                'tags: ["#方法组件"]',
                'project: "proj-test"',
                'status: draft',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertTrue(any("缺少 script 字段" in v.get("message", "") for v in violations))

    def test_compute_atom_nonexistent_script(self):
        """compute 原子引用的脚本不存在应报 HARD。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "compute-no-file.md",
            [
                'id: "compute-no-file"',
                'title: "脚本不存在"',
                'type: compute',
                'tags: ["#方法组件"]',
                'project: "proj-test"',
                'status: draft',
                'script: "nonexistent.py"',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertTrue(any("脚本文件不存在" in v.get("message", "") for v in violations))

    def test_no_tags_warning(self):
        """缺少标签应报 SOFT 警告。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "gap-no-tags.md",
            [
                'id: "gap-no-tags"',
                'title: "无标签"',
                'type: gap',
                'tags: []',
                'project: "proj-test"',
                'status: draft',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertTrue(any("tags 为空" in v.get("message", "") for v in violations))

    def test_no_project_warning(self):
        """缺少 project 字段应报 SOFT 警告。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "gap-no-project.md",
            [
                'id: "gap-no-project"',
                'title: "无项目"',
                'type: gap',
                'tags: ["#引言缺口"]',
                'status: draft',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        self.assertTrue(any("project 字段为空" in v.get("message", "") for v in violations))


class TestMatrixProjectCoupling(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = FixtureSandbox()
        cls.sandbox.setup_dirs()
        cls.sandbox.bind()

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.unbind()
        cls.sandbox.cleanup()

    def setUp(self):
        # 清空项目和矩阵文件
        for d in self.sandbox.at("projects").rglob("*.md"):
            d.unlink()
        matrix = self.sandbox.at("matrix.md")
        if matrix.exists():
            matrix.unlink()

    def _make_project(self, pid, bucket="active"):
        """创建简单的项目卡片。"""
        proj_dir = self.sandbox.at("projects", bucket, pid)
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "index.md").write_text(f"""---
id: "{pid}"
title: "Test Project"
domain: "金相分析"
problem: "可解释性"
status: active
---
# Test
""", encoding="utf-8")

    def test_project_not_in_matrix(self):
        """项目存在于磁盘但矩阵中未引用 → SOFT 警告。"""
        self._make_project("proj-test-001")
        self.sandbox.at("matrix.md").write_text(
            "## 矩阵总表\n\n| 研究领域 \\ 核心问题 | 可解释性 |\n"
            "|---------------------|----------|\n"
            "| 金相分析 | — |\n",
            encoding="utf-8",
        )
        vocab = make_vocab()
        violations = ci.check_matrix_project_coupling(vocab)
        self.assertTrue(any("未出现在矩阵中" in v.get("message", "")
                            for v in violations),
                        f"Expected soft warning, got: {violations}")

    def test_matrix_ref_to_nonexistent_project(self):
        """矩阵引用了不存在的项目 → HARD 违规。"""
        self.sandbox.at("matrix.md").write_text(
            "## 矩阵总表\n\n| 研究领域 \\ 核心问题 | 可解释性 |\n"
            "|---------------------|----------|\n"
            "| 金相分析 | [proj-ghost](projects/active/proj-ghost/) 💡 |\n",
            encoding="utf-8",
        )
        vocab = make_vocab()
        violations = ci.check_matrix_project_coupling(vocab)
        self.assertTrue(any("引用了不存在的项目" in v.get("message", "")
                            for v in violations))


class TestSkillEvidence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = FixtureSandbox()
        cls.sandbox.setup_dirs()
        cls.sandbox.bind()

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.unbind()
        cls.sandbox.cleanup()

    def setUp(self):
        skill_file = self.sandbox.at("competencies", "skill-tree.md")
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        if skill_file.exists():
            skill_file.unlink()

    def test_l3_skill_no_evidence(self):
        """L3 技能缺少证据应报 SOFT 警告。"""
        self.sandbox.at("competencies", "skill-tree.md").write_text(
            "| 技能 | 评级 | 证据（项目/产出） |\n"
            "|------|------|-------------------|\n"
            "| 文献批判性阅读 | L3 |  |\n",
            encoding="utf-8",
        )
        vocab = make_vocab()
        violations = ci.check_skill_evidence(vocab)
        self.assertTrue(len(violations) > 0,
                        f"Expected soft warning for L3 skill with no evidence")
        self.assertTrue(any("缺少证据" in v.get("message", "") for v in violations))

    def test_l4_skill_no_evidence(self):
        """L4 技能缺少证据应报 SOFT 警告。"""
        self.sandbox.at("competencies", "skill-tree.md").write_text(
            "| 技能 | 评级 | 证据（项目/产出） |\n"
            "|------|------|-------------------|\n"
            "| 学术论文写作 | L4 |  |\n",
            encoding="utf-8",
        )
        vocab = make_vocab()
        violations = ci.check_skill_evidence(vocab)
        self.assertTrue(any("缺少证据" in v.get("message", "") for v in violations),
                        f"Got: {violations}")

    def test_l2_skill_no_evidence_ok(self):
        """L2 技能无需检查证据（只有 L3/L4 要求证据）。"""
        self.sandbox.at("competencies", "skill-tree.md").write_text(
            "| 技能 | 评级 | 证据（项目/产出） |\n"
            "|------|------|-------------------|\n"
            "| 统计分析 | L2 |  |\n",
            encoding="utf-8",
        )
        vocab = make_vocab()
        violations = ci.check_skill_evidence(vocab)
        self.assertEqual(len(violations), 0,
                         f"L2 should not trigger evidence check, got: {violations}")


class TestScriptSelfContainment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = FixtureSandbox()
        cls.sandbox.setup_dirs()
        cls.sandbox.bind()

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.unbind()
        cls.sandbox.cleanup()

    def setUp(self):
        scripts_dir = self.sandbox.at("knowledge", "atoms", "scripts")
        for f in scripts_dir.glob("*.py"):
            f.unlink()

    def test_hardcoded_path(self):
        """脚本包含硬编码绝对路径应报 SOFT 警告。"""
        (self.sandbox.at("knowledge", "atoms", "scripts") / "test.py").write_text(
            'data = open("/home/user/data.csv")\n', encoding="utf-8")
        vocab = make_vocab()
        violations = ci.check_script_self_containment(vocab)
        self.assertTrue(any("硬编码绝对路径" in v.get("message", "") for v in violations))

    def test_undeclared_dep(self):
        """脚本 import 了未在 script_deps 中声明的外部库。"""
        scripts_dir = self.sandbox.at("knowledge", "atoms", "scripts")
        (scripts_dir / "compute-0001.py").write_text(
            "import numpy as np\nprint(np.array([1,2,3]))\n", encoding="utf-8")
        atoms_dir = self.sandbox.at("knowledge", "atoms")
        make_atom_file(
            atoms_dir,
            "compute-0001.md",
            [
                'id: "compute-0001"',
                'title: "测试计算"',
                'type: compute',
                'tags: ["#方法组件"]',
                'project: "proj-test"',
                'status: draft',
                'script: "compute-0001.py"',
                'script_deps: []',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_script_self_containment(vocab)
        self.assertTrue(any("未在 atom front-matter script_deps 中声明" in v.get("message", "")
                            for v in violations))


class TestAtomIndependence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = FixtureSandbox()
        cls.sandbox.setup_dirs()
        cls.sandbox.bind()

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.unbind()
        cls.sandbox.cleanup()

    def setUp(self):
        atoms_dir = self.sandbox.at("knowledge", "atoms")
        for f in atoms_dir.rglob("*.md"):
            f.unlink()

    def test_hardcoded_project_path_in_body(self):
        """原子正文包含硬编码项目路径 → SOFT 警告。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "gap-with-path.md",
            [
                'id: "gap-with-path"',
                'title: "含路径"',
                'type: gap',
                'tags: ["#引言缺口"]',
                'project: "proj-test"',
                'status: draft',
            ],
            body_text="# 核心断言\n参见 ../../projects/active/proj-other 的细节。",
        )
        vocab = make_vocab()
        violations = ci.check_atom_independence(vocab)
        self.assertTrue(any("硬编码项目路径" in v.get("message", "") for v in violations))


class TestEvidenceAnchoring(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = FixtureSandbox()
        cls.sandbox.setup_dirs()
        cls.sandbox.bind()

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.unbind()
        cls.sandbox.cleanup()

    def setUp(self):
        atoms_dir = self.sandbox.at("knowledge", "atoms")
        for f in atoms_dir.rglob("*.md"):
            f.unlink()

    def test_result_atom_without_source(self):
        """result 类型原子缺少 source → HARD 违规。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "result-no-source.md",
            [
                'id: "result-no-source"',
                'title: "无源结果"',
                'type: result',
                'tags: ["#结果讨论"]',
                'project: "proj-test"',
                'status: draft',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_evidence_anchoring(vocab)
        self.assertTrue(any("source 为空" in v.get("message", "")
                            for v in violations),
                        f"Got: {violations}")

    def test_insight_without_related_atoms(self):
        """insight 原子在 body 中无关联引用 → SOFT 警告。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "insight-orphan.md",
            [
                'id: "insight-orphan"',
                'title: "孤立洞察"',
                'type: insight',
                'tags: ["#结果讨论"]',
                'project: "proj-test"',
                'status: draft',
            ],
            body_text="# 核心断言\n这一段没有引用任何 method 或 result 原子。",
        )
        vocab = make_vocab()
        violations = ci.check_evidence_anchoring(vocab)
        self.assertTrue(any("缺乏推导链" in v.get("message", "")
                            for v in violations),
                        f"Got: {violations}")


class TestAutoFix(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sandbox = FixtureSandbox()
        cls.sandbox.setup_dirs()
        cls.sandbox.bind()

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.unbind()
        cls.sandbox.cleanup()

    def setUp(self):
        atoms_dir = self.sandbox.at("knowledge", "atoms")
        for f in atoms_dir.rglob("*.md"):
            f.unlink()

    def test_fix_blank_project(self):
        """空 project 字段 → 自动修复为 'uncategorized'。"""
        make_atom_file(
            self.sandbox.at("knowledge", "atoms"),
            "gap-blank-project.md",
            [
                'id: "gap-blank-project"',
                'title: "空项目"',
                'type: gap',
                'tags: ["#引言缺口"]',
                'project: ""',
                'status: draft',
            ],
        )
        vocab = make_vocab()
        violations = ci.check_atom_front_matter(vocab)
        project_violations = [v for v in violations if v.get("field") == "project"]
        self.assertTrue(len(project_violations) > 0)

        fixed = ci.auto_fix(violations)
        self.assertTrue(fixed > 0)

        # 重新读取确认修复生效
        content = self.sandbox.at("knowledge", "atoms", "gap-blank-project.md").read_text()
        self.assertIn('project: "uncategorized"', content)


class TestAosUtils(unittest.TestCase):
    """验证共享工具模块的基础功能。"""

    def test_parse_valid_front_matter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nid: test\n---\n\nBody\n")
            f.flush()
            fm = parse_front_matter(f.name)
            self.assertEqual(fm, {"id": "test"})
            os.unlink(f.name)

    def test_parse_no_front_matter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Just body text\n")
            f.flush()
            fm = parse_front_matter(f.name)
            self.assertIsNone(fm)
            os.unlink(f.name)

    def test_parse_body_with_front_matter(self):
        from aos_utils import parse_body
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nid: test\n---\n\nBody text\n")
            f.flush()
            body = parse_body(f.name)
            self.assertEqual(body, "Body text")
            os.unlink(f.name)

    def test_parse_body_no_front_matter(self):
        from aos_utils import parse_body
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Plain text\n")
            f.flush()
            body = parse_body(f.name)
            self.assertEqual(body, "Plain text")
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
