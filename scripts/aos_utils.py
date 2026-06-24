"""
AOS 共享工具函数 —— 消除跨脚本的重复实现。

提供：
    - parse_front_matter()  解析 YAML front-matter
    - parse_body()          提取 front-matter 之后的正文
"""

import re
import yaml
from pathlib import Path


# ─── Front-matter 解析 ───────────────────────────────────────

_FM_PATTERN = re.compile(
    r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)",
    re.DOTALL,
)


def parse_front_matter(filepath: str | Path) -> dict | None:
    """从 Markdown 文件提取 YAML front-matter。

    返回解析后的 dict，或 None（文件不存在 / 无 front-matter / YAML 语法错误）。
    """
    content = _read_file(filepath)
    if content is None:
        return None

    m = _FM_PATTERN.match(content)
    if not m:
        return None

    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None


def parse_body(filepath: str | Path) -> str:
    """提取 front-matter 之后的正文。"""
    content = _read_file(filepath)
    if content is None:
        return ""

    m = _FM_PATTERN.match(content)
    if m:
        return content[m.end():].strip()
    return content.strip()


def _read_file(filepath: str | Path) -> str | None:
    """读取文件内容，文件不存在时返回 None。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None
