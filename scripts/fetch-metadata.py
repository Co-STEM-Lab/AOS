#!/usr/bin/env python3
"""
从 Crossref API 抓取论文元数据（摘要等），更新 papers/*/index.md。

用法:
    python scripts/fetch-metadata.py                    # 更新所有论文
    python scripts/fetch-metadata.py --dry-run           # 试跑，不写文件
    python scripts/fetch-metadata.py --doi 10.1016/...   # 指定单篇
"""

import sys, re, json, os, time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import yaml

ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = ROOT / "papers"

DRY_RUN = False


def fetch_openalex(doi: str) -> dict | None:
    """从 OpenAlex API 获取论文元数据（通常有更好的 abstract 覆盖）。"""
    url = f"https://api.openalex.org/works/doi:{doi}"
    try:
        with urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data
    except HTTPError as e:
        print(f"  ⚠️  HTTP {e.code} for {doi}")
        return None
    except Exception as e:
        print(f"  ⚠️  请求失败 {doi}: {e}")
        return None


def fetch_crossref(doi: str) -> dict | None:
    """从 Crossref API 获取论文元数据。"""
    url = f"https://api.crossref.org/works/{doi}"
    req = Request(url, headers={"User-Agent": "AOS/1.0 (mailto:chengs@aisi.ac.cn)"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data.get("message")
    except HTTPError as e:
        print(f"  ⚠️  HTTP {e.code} for {doi}")
        return None
    except Exception as e:
        print(f"  ⚠️  请求失败 {doi}: {e}")
        return None


def clean_abstract(raw: str) -> str:
    """清理 abstract 中的 HTML/XML 标签。"""
    if not raw:
        return ""
    text = re.sub(r'<[^>]+>', '', raw)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.strip()
    return text


def decode_openalex_abstract(inverted_index: dict) -> str:
    """OpenAlex 的倒排索引摘要 → 纯文本。"""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


def fetch_semanticscholar(doi: str) -> str | None:
    """从 Semantic Scholar API 获取摘要。"""
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract"
    time.sleep(1.5)  # 限速，避免 429
    try:
        with urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        abstract = data.get("abstract")
        return abstract if abstract else None
    except HTTPError as e:
        if e.code == 429:
            print(f"  ⚠️  Semantic Scholar 限速，跳过")
        return None
    except Exception:
        return None


def update_index(path: Path, dry_run: bool = False) -> bool:
    """对单个 index.md 尝试抓取摘要。返回是否做了修改。"""
    content = path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return False

    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError:
        return False

    doi = fm.get("doi", "")
    current_abstract = fm.get("abstract", "")

    if not doi:
        print(f"  ⏭️  {path.parent.name}: 无 DOI，跳过")
        return False

    # 如果已有摘要且不是"NO ABSTRACT"，跳过
    if current_abstract and "NO ABSTRACT" not in current_abstract and len(current_abstract) > 20:
        print(f"  ✅ {path.parent.name}: 已有摘要 ({len(current_abstract)} 字符)，跳过")
        return False

    print(f"  🔍 {path.parent.name}: 抓取 {doi}...")

    # 优先用 OpenAlex
    cleaned = ""
    oa_data = fetch_openalex(doi)
    if oa_data:
        inv_index = oa_data.get("abstract_inverted_index")
        if inv_index:
            cleaned = decode_openalex_abstract(inv_index)

    # 回退到 Crossref
    if not cleaned:
        msg = fetch_crossref(doi)
        if msg and msg.get("abstract"):
            cleaned = clean_abstract(msg["abstract"])

    # 再回退到 Semantic Scholar
    if not cleaned:
        cleaned = fetch_semanticscholar(doi)

    if not cleaned:
        print(f"  ⚠️  {path.parent.name}: 无摘要数据")
        return False

    if len(cleaned) < 10:
        print(f"  ⚠️  {path.parent.name}: 摘要太短，跳过")
        return False

    # 更新 YAML front-matter 中的 abstract
    # 重建 front-matter
    fm["abstract"] = cleaned

    # 序列化 YAML (保留字段顺序)
    new_fm_lines = ["---"]
    for key, value in fm.items():
        if key == "abstract":
            # 多行字符串
            new_fm_lines.append(f"abstract: >")
            for line in cleaned.split("\n"):
                new_fm_lines.append(f"  {line}" if line else "")
        elif isinstance(value, list):
            new_fm_lines.append(f"{key}:")
            for item in value:
                new_fm_lines.append(f"  - {json.dumps(item, ensure_ascii=False)}")
        elif isinstance(value, str) and "\n" in value:
            new_fm_lines.append(f"{key}: |")
            for line in value.split("\n"):
                new_fm_lines.append(f"  {line}")
        elif isinstance(value, bool):
            new_fm_lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            new_fm_lines.append(f"{key}: {value}")
        elif value is None:
            new_fm_lines.append(f"{key}: null")
        else:
            new_fm_lines.append(f'{key}: "{value}"')
    new_fm_lines.append("---")

    new_fm = "\n".join(new_fm_lines)
    body = content[fm_match.end():]

    if dry_run:
        print(f"  📝 {path.parent.name}: 将更新 abstract ({len(cleaned)} 字符)")
        print(f"     Abstract: {cleaned[:120]}...")
        return True

    path.write_text(f"{new_fm}\n{body}", encoding="utf-8")
    print(f"  ✅ {path.parent.name}: 摘要已更新 ({len(cleaned)} 字符)")
    return True


def main():
    global DRY_RUN
    args = sys.argv[1:]

    if "--dry-run" in args:
        DRY_RUN = True

    target_dois = []
    for a in args:
        if a.startswith("--doi="):
            target_dois.append(a.split("=", 1)[1])

    if target_dois:
        print(f"🔍 抓取指定 DOI: {target_dois}")
    else:
        print("🔍 扫描所有已发表论文...")

    updated = 0
    # 遍历 papers/ 下已发表论文目录（非 _ 开头）
    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir() or paper_dir.name.startswith("_"):
            continue
        idx = paper_dir / "index.md"
        if not idx.exists():
            continue

        # 如果指定了 DOI 列表，只处理匹配的
        if target_dois:
            with open(idx) as f:
                content = f.read()
            fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if fm_match:
                fm = yaml.safe_load(fm_match.group(1))
                if fm.get("doi", "") not in target_dois:
                    continue

        if update_index(idx, dry_run=DRY_RUN):
            updated += 1

    print(f"\n📊 总计: {updated} 篇论文摘要已{'准备更新' if DRY_RUN else '更新'}")


if __name__ == "__main__":
    main()
