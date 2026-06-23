#!/usr/bin/env python3
"""
AOS 渲染引擎 —— Markdown 论文草稿 → HTML 报告 或 LaTeX 论文。

用法：
    python scripts/render.py <input.md>                    # HTML 到 stdout
    python scripts/render.py <input.md> --html -o report.html     # HTML 报告
    python scripts/render.py <input.md> --latex -o paper.tex      # LaTeX 论文
    python scripts/render.py <input.md> --html --open      # 浏览器预览

HTML 用途：展示/汇报/快速预览
LaTeX 用途：期刊/会议投稿
依赖：pip install markdown (可选)
"""

import sys
import re
import subprocess
import tempfile
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = ROOT / "templates" / "output.css"
HTML_TEMPLATE = ROOT / "templates" / "paper-html.html"


def parse_front_matter(text: str) -> tuple[dict, str]:
    """解析 YAML front-matter，返回 (元数据, 正文)。"""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    import yaml
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    body = text[match.end():].strip()
    return meta, body


def md_to_html_simple(md: str) -> str:
    """内置简易 Markdown→HTML 转换器（零依赖）。"""
    lines = md.split("\n")
    out = []
    in_list = False
    in_ol = False
    in_code = False
    code_buf = []

    for line in lines:
        # 代码块
        if line.strip().startswith("```"):
            if in_code:
                lang = in_code
                code_text = "\n".join(code_buf)
                out.append(f'<pre><code class="language-{lang}">{_escape(code_text)}</code></pre>')
                code_buf = []
                in_code = False
            else:
                in_code = line.strip()[3:].strip() or "text"
            continue
        if in_code:
            code_buf.append(line)
            continue

        # 空行 → 关闭列表
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            if in_ol:
                out.append("</ol>")
                in_ol = False
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            if in_ol: out.append("</ol>"); in_ol = False
            level = len(m.group(1))
            out.append(f"<h{level}>{m.group(2)}</h{level}>")
            continue

        # 无序列表
        m = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if m:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline_md(m.group(2))}</li>")
            continue

        # 有序列表
        m = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if m:
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_inline_md(m.group(2))}</li>")
            continue

        # 引用
        m = re.match(r"^>\s?(.*)$", line)
        if m:
            if in_list: out.append("</ul>"); in_list = False
            if in_ol: out.append("</ol>"); in_ol = False
            out.append(f"<blockquote><p>{_inline_md(m.group(1))}</p></blockquote>")
            continue

        # 表格（简化：检测 | 开头）
        if line.strip().startswith("|") and "|" in line[1:]:
            if in_list: out.append("</ul>"); in_list = False
            if in_ol: out.append("</ol>"); in_ol = False
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]
            if all(re.match(r"^[-:]+$", c) for c in cells):
                continue  # 分隔行跳过
            tag = "th" if not out or not out[-1].startswith("<tr>") else "td"
            row = "".join(f"<{tag}>{_inline_md(c)}</{tag}>" for c in cells)
            if tag == "th":
                out.append(f"<table><tr>{row}</tr>")
            else:
                out.append(f"<tr>{row}</tr>")
                # 检查下一行是否还是表格
                continue
            continue
        elif out and out[-1].startswith("<tr>") and not line.strip().startswith("|"):
            out.append("</table>")

        # 普通段落
        if in_list: out.append("</ul>"); in_list = False
        if in_ol: out.append("</ol>"); in_ol = False
        out.append(f"<p>{_inline_md(line)}</p>")

    if in_list: out.append("</ul>")
    if in_ol: out.append("</ol>")
    if in_code: out.append(f'<pre><code>{_escape("\n".join(code_buf))}</code></pre>')

    return "\n".join(out)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline_md(text: str) -> str:
    """行内 Markdown：粗体、斜体、代码、链接、图片。"""
    import re as _re
    text = _escape(text)
    text = _re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = _re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = _re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = _re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img alt="\1" src="\2">', text)
    text = _re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def md_to_html(text: str) -> str:
    """Markdown→HTML：优先用 markdown 库，fallback 到简易转换器。"""
    try:
        import markdown
        return markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"])
    except ImportError:
        return md_to_html_simple(text)


def build_html(meta: dict, body_html: str) -> str:
    """将元数据和正文 HTML 注入模板。"""
    template = HTML_TEMPLATE.read_text(encoding="utf-8")

    title = meta.get("title", "未命名")
    authors = meta.get("authors", "")
    affiliation = meta.get("affiliation", "")
    abstract = meta.get("abstract", "")
    keywords = meta.get("keywords", "")
    refs = meta.get("references", [])

    html = template.replace("{{title}}", _escape(title))
    html = html.replace("{{authors}}", authors)
    html = html.replace("{{affiliation}}", affiliation)
    html = html.replace("{{abstract}}", abstract)
    html = html.replace("{{keywords}}", keywords)
    html = html.replace("{{body}}", body_html)

    if refs:
        refs_html = "\n".join(f"<li>{r}</li>" for r in refs)
        # 保留 Mustache 条件块
        html = re.sub(r'\{\{#references\}\}.*?\{\{/references\}\}', "", html, flags=re.DOTALL)
        html += f'\n<div class="page-break"></div>\n<h2>参考文献</h2>\n<ol class="references">\n{refs_html}\n</ol>'
    else:
        html = re.sub(r'\{\{#references\}\}.*?\{\{/references\}\}', "", html, flags=re.DOTALL)

    return html


LATEX_TEMPLATE_ZH = ROOT / "templates" / "paper-latex.tex"
LATEX_TEMPLATE_EN = ROOT / "templates" / "paper-latex-en.tex"


def build_latex(meta: dict, body_latex: str, lang: str = "zh") -> str:
    """将元数据和正文注入 LaTeX 模板。"""
    tpl_path = LATEX_TEMPLATE_EN if lang == "en" else LATEX_TEMPLATE_ZH
    template = tpl_path.read_text(encoding="utf-8") if tpl_path.exists() else ""
    if not template:
        return body_latex

    title = meta.get("title", "未命名")
    authors = meta.get("authors", "")
    abstract = meta.get("abstract", "")
    keywords = meta.get("keywords", "")
    refs = meta.get("references", [])

    tex = template.replace("{{title}}", title)
    tex = tex.replace("{{authors}}", authors)
    tex = tex.replace("{{abstract}}", abstract)
    tex = tex.replace("{{keywords}}", keywords)
    tex = tex.replace("{{body}}", body_latex)

    if refs:
        refs_tex = "\n".join(r"\bibitem{" + f"ref{i}" + "} " + r for i, r in enumerate(refs))
        tex = tex.replace(r"\bibliography{references}",
                          r"\begin{thebibliography}{99}\n" + refs_tex + r"\n\end{thebibliography}")
    else:
        tex = re.sub(r'\{\{#references\}\}.*?\{\{/references\}\}', "", tex, flags=re.DOTALL)

    return tex


def md_to_latex(md: str) -> str:
    """Markdown → LaTeX 简易转换。"""
    lines = md.split("\n")
    out = []
    in_itemize = in_enumerate = False

    for line in lines:
        if not line.strip():
            if in_itemize: out.append(r"\end{itemize}"); in_itemize = False
            if in_enumerate: out.append(r"\end{enumerate}"); in_enumerate = False
            out.append("")
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            if in_itemize: out.append(r"\end{itemize}"); in_itemize = False
            if in_enumerate: out.append(r"\end{enumerate}"); in_enumerate = False
            level = len(m.group(1))
            cmds = ["", r"\section{", r"\subsection{", r"\subsubsection{", r"\paragraph{", r"\subparagraph{"]
            if level <= 5:
                out.append(cmds[level] + m.group(2) + "}")
            else:
                out.append(r"\textbf{" + m.group(2) + "}")
            continue

        # 无序列表
        m = re.match(r"^[-*+]\s+(.+)$", line)
        if m:
            if not in_itemize: out.append(r"\begin{itemize}"); in_itemize = True
            out.append(r"\item " + _latex_inline(m.group(1)))
            continue

        # 有序列表
        m = re.match(r"^\d+\.\s+(.+)$", line)
        if m:
            if not in_enumerate: out.append(r"\begin{enumerate}"); in_enumerate = True
            out.append(r"\item " + _latex_inline(m.group(1)))
            continue

        # 普通段落
        if in_itemize: out.append(r"\end{itemize}"); in_itemize = False
        if in_enumerate: out.append(r"\end{enumerate}"); in_enumerate = False
        out.append(_latex_inline(line) + r"\\")

    if in_itemize: out.append(r"\end{itemize}")
    if in_enumerate: out.append(r"\end{enumerate}")
    return "\n".join(out)


def _latex_inline(text: str) -> str:
    """行内 LaTeX 转义。"""
    text = text.replace("\\", "\\textbackslash ")
    for ch in "&%$#_{}~^":
        text = text.replace(ch, "\\" + ch)
    # Markdown 粗体/斜体 → LaTeX
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
    text = re.sub(r'`([^`]+)`', r'\\texttt{\1}', text)
    return text


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python scripts/render.py <input.md> [--html|--latex] [--lang zh|en] [-o output] [--open]")
        print("  --html   输出 A4 HTML 报告（展示/汇报用）")
        print("  --latex  输出 LaTeX 论文（投稿用）")
        print("  --lang zh  中文 LaTeX 模板 (ctexart)")
        print("  --lang en  英文 LaTeX 模板 (article)")
        print("  默认: --html")
        sys.exit(1)

    input_path = None
    output_path = None
    open_browser = False
    mode = "html"
    lang = "zh"

    i = 0
    while i < len(args):
        if args[i] == "-o" and i + 1 < len(args):
            output_path = args[i + 1]; i += 1
        elif args[i] == "--open":
            open_browser = True
        elif args[i] == "--html":
            mode = "html"
        elif args[i] == "--latex":
            mode = "latex"
        elif args[i] == "--lang" and i + 1 < len(args):
            lang = args[i + 1]; i += 1
        elif not args[i].startswith("-") and input_path is None:
            input_path = args[i]
        i += 1

    if not input_path:
        print("❌ 请指定输入文件")
        sys.exit(1)

    src = Path(input_path)
    if not src.exists():
        print(f"❌ 文件不存在: {src}")
        sys.exit(1)

    text = src.read_text(encoding="utf-8")
    meta, body_md = parse_front_matter(text)

    if mode == "latex":
        body_converted = md_to_latex(body_md)
        result = build_latex(meta, body_converted, lang)
    else:
        body_html = md_to_html(body_md)
        result = build_html(meta, body_html)

    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
        print(f"✅ 已输出 ({mode}): {output_path}")
    else:
        print(result)

    if open_browser and output_path and mode == "html":
        abs_path = Path(output_path).resolve()
        subprocess.run(["xdg-open", str(abs_path)], check=False)


if __name__ == "__main__":
    main()
