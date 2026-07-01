#!/usr/bin/env python3
"""
论文渲染引擎 —— Markdown 论文草稿 → HTML 报告 或 LaTeX 论文。

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
import html as html_mod
import yaml
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = ROOT / "templates" / "output.css"
HTML_TEMPLATE = ROOT / "templates" / "paper-html.html"


# ─── Front-matter 解析（内联，消除 aos_utils 依赖）────────────

_FM_PATTERN = re.compile(
    r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)",
    re.DOTALL,
)


def parse_front_matter(filepath: str | Path) -> dict | None:
    """从 Markdown 文件提取 YAML front-matter。"""
    try:
        content = Path(filepath).read_text(encoding="utf-8")
    except Exception:
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
    try:
        content = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return ""
    m = _FM_PATTERN.match(content)
    if m:
        return content[m.end():].strip()
    return content.strip()



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
        html = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite"])
    except ImportError:
        html = md_to_html_simple(text)

    # 后处理：将 <p><img...></p> 提升为 <figure><img...><figcaption>alt</figcaption></figure>
    # 确保图片在 A4 排版内宽度自适应
    def _wrap_img(m):
        tag = m.group(1)
        alt = ""
        alt_m = re.search(r'alt="([^"]*)"', tag)
        if alt_m:
            alt = alt_m.group(1)
        cap = f'<figcaption>{alt}</figcaption>' if alt else ''
        return f'<figure>{tag}{cap}</figure>'

    html = re.sub(r'<p[^>]*>(<img[^>]+>)</p>', _wrap_img, html)
    return html


# ─── 模板渲染引擎 ──────────────────────────────────────────────

def _render_template(template: str, context: dict) -> str:
    """简易 Mustache 风格模板渲染：{{var}} + {{#var}}...{{/var}} 条件块。

    支持：
      - {{var}}           → 简单变量替换
      - {{#var}}...{{/var}} → 条件块：var 为真值时保留，假值/空/None 时移除
      - 嵌套条件块有限支持（逐层收敛）
    """
    def _replace_var(m):
        key = m.group(1).strip()
        val = context.get(key, "")
        return str(val) if val else ""

    # 逐层清除条件块（从内向外，支持嵌套）
    prev = ""
    result = template
    while prev != result:
        prev = result
        result = re.sub(
            r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}',
            lambda m: m.group(2) if context.get(m.group(1)) else "",
            result,
            flags=re.DOTALL,
        )

    # 替换简单变量
    result = re.sub(r'\{\{(\w+)\}\}', _replace_var, result)
    return result


def _format_authors(authors) -> str:
    """将 authors 字段格式化为 HTML 或 LaTeX 字符串。

    接受格式：
      - 列表：["Name1", "Name2"] → "Name1, Name2"
      - 字符串原样返回
    """
    if isinstance(authors, list):
        return ", ".join(authors)
    return str(authors) if authors else ""


def build_html(meta: dict, body_html: str) -> str:
    """将元数据和正文 HTML 注入模板。"""
    template = HTML_TEMPLATE.read_text(encoding="utf-8")

    ctx = {}
    ctx["title"] = html_mod.escape(meta.get("title", "未命名"))
    ctx["authors"] = _format_authors(meta.get("authors", ""))
    ctx["affiliation"] = _format_authors(meta.get("affiliation", ""))
    ctx["abstract"] = meta.get("abstract", "")
    ctx["keywords"] = meta.get("keywords", "")
    ctx["body"] = body_html
    ctx["references"] = bool(meta.get("references"))

    html = _render_template(template, ctx)

    # 生成参考文献 HTML
    refs = meta.get("references", [])
    if refs:
        refs_html = "\n".join(f"<li>{r}</li>" for r in refs)
        html += f'\n<div class="page-break"></div>\n<h2>参考文献</h2>\n<ol class="references">\n{refs_html}\n</ol>'

    return html


LATEX_TEMPLATE = ROOT / "templates" / "paper-elsevier-sc.tex"


def build_latex(meta: dict, body_latex: str, style: str = "elsevier-sc") -> str:
    """将元数据和正文注入 LaTeX 模板。"""
    tpl_path = LATEX_TEMPLATE
    template = tpl_path.read_text(encoding="utf-8") if tpl_path.exists() else ""
    if not template:
        return body_latex

    ctx = {}
    ctx["title"] = meta.get("title", "未命名")
    ctx["shorttitle"] = meta.get("shorttitle", meta.get("title", ""))[:60]
    ctx["authors"] = _format_authors(meta.get("authors", ""))
    ctx["shortauthors"] = meta.get("shortauthors", "")
    ctx["abstract"] = meta.get("abstract", "")
    ctx["keywords"] = meta.get("keywords", "")
    ctx["body"] = body_latex
    ctx["bibfile"] = meta.get("bibfile", "references")
    ctx["highlights"] = bool(meta.get("highlights"))
    ctx["highlights_text"] = meta.get("highlights", "")
    ctx["bios"] = bool(meta.get("bios"))
    ctx["bios_text"] = meta.get("bios", "")

    # 作者详情（支持 up to 6 位作者，每位含 name/email/org/address/等）
    for i in range(1, 7):
        author_key = f"author{i}"
        author_data = meta.get(author_key, {})
        if isinstance(author_data, dict):
            ctx[f"author{i}"] = author_data.get("name", "")
            ctx[f"email{i}"] = author_data.get("email", "")
            ctx[f"org{i}"] = author_data.get("org", "")
            ctx[f"addr{i}"] = author_data.get("address", "")
            ctx[f"city{i}"] = author_data.get("city", "")
            ctx[f"postcode{i}"] = author_data.get("postcode", "")
            ctx[f"state{i}"] = author_data.get("state", "")
            ctx[f"country{i}"] = author_data.get("country", "")
            ctx[f"credit{i}"] = author_data.get("credit", "")
            ctx[f"orcid{i}"] = author_data.get("orcid", "")
        elif isinstance(author_data, str):
            ctx[f"author{i}"] = author_data
            for field in ("email", "org", "addr", "city", "postcode", "state", "country", "credit", "orcid"):
                ctx[f"{field}{i}"] = ""

    tex = _render_template(template, ctx)

    # 生成参考文献
    refs = meta.get("references", [])
    if refs:
        refs_tex = "\n".join(r"\bibitem{" + f"ref{i}" + "} " + r for i, r in enumerate(refs))
        tex = tex.replace(r"\bibliography{references}",
                          r"\begin{thebibliography}{99}\n" + refs_tex + r"\n\end{thebibliography}")

    return tex


def md_to_latex(md: str) -> str:
    """Markdown → LaTeX 简易转换。

    支持：
      - $$...$$ → \\begin{equation}...\\end{equation}
      - ![caption](path) → figure 环境
      - Markdown 表格 → LaTeX 三线表
      - [@citekey] → \\citep{citekey}
    """
    # 预处理：$$ 公式块 → \begin{equation}
    eq_count = [0]
    def _replace_eq(m):
        eq_count[0] += 1
        inner = m.group(1).strip()
        return f"\\begin{{equation}}\n{inner}\n\\end{{equation}}"

    md = re.sub(r'\$\$\s*\n(.*?)\n\s*\$\$', _replace_eq, md, flags=re.DOTALL)

    # 预处理：![caption](path) → figure 占位
    md = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
                r'\\begin{figure}[htbp]\n  \\centering\n  \\includegraphics[width=\\linewidth]{\2}\n  \\caption{\1}\n\\end{figure}',
                md)

    # 预处理：[@citation] → \citep{citation}  支持 [@key1; @key2]
    md = re.sub(
        r'\[@([^\]]+)\]',
        lambda m: r'\citep{' + m.group(1).replace('; ', ',').replace(';', ',') + '}',
        md,
    )
    # 也支持 plain @citation 在句子中
    md = re.sub(r'(?<!\w)@(\w[\w:-]+)', r'\\citet{\1}', md)

    # 保护预生成的 LaTeX 命令，防止 _latex_inline 转义反斜杠
    # 用 @P{n}@ 占位（@ 不在 _latex_inline 的转义列表中）
    protected = {}
    protect_count = [0]

    def _protect_latex(m):
        protect_count[0] += 1
        key = f"@P{protect_count[0]}@"
        protected[key] = m.group(0)
        return key

    # 保护所有 \command{...} 结构（已由预处理生成）
    md = re.sub(r'\\(?:citep|citet|begin|end|textbf|textit|texttt)\{[^}]*\}', _protect_latex, md)
    # 也保护单独的 \command
    md = re.sub(r'\\(?:toprule|midrule|bottomrule)', _protect_latex, md)

    lines = md.split("\n")
    out = []
    in_itemize = in_enumerate = in_verbatim = in_equation = in_figure = False
    in_table = False

    for line in lines:
        # 原样保留块
        if line.strip().startswith("```"):
            if in_verbatim:
                out.append(r"\end{verbatim}")
                in_verbatim = False
            else:
                out.append(r"\begin{verbatim}")
                in_verbatim = True
            continue
        if in_verbatim:
            out.append(line)
            continue

        # 数学环境：原样通过
        if line.strip().startswith(r"\begin{equation}"):
            if in_itemize: out.append(r"\end{itemize}"); in_itemize = False
            if in_enumerate: out.append(r"\end{enumerate}"); in_enumerate = False
            out.append(line)
            in_equation = True
            continue
        if in_equation:
            if line.strip().startswith(r"\end{equation}"):
                out.append(line)
                in_equation = False
            else:
                out.append(line)  # raw pass-through
            continue

        # figure 块：已由预处理器完整生成，直接通过
        if line.strip().startswith(r"\begin{figure}"):
            if in_itemize: out.append(r"\end{itemize}"); in_itemize = False
            if in_enumerate: out.append(r"\end{enumerate}"); in_enumerate = False
            in_figure = True
            out.append(line)
            continue
        if in_figure:
            out.append(line)
            if line.strip().startswith(r"\end{figure}"):
                in_figure = False
            continue

        # 表格：Markdown 表格 → LaTeX 三线表
        if line.strip().startswith("|") and line.count("|") >= 3:
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]

            # 分隔行（|---|---|）— 跳过，标记为表头已处理
            if all(re.match(r"^[-:\s]+$", c) for c in cells):
                continue

            if not in_table:
                # 计算列数和对齐
                n_cols = len(cells)
                out.append(r"\begin{table}[htbp]")
                out.append(r"\centering")
                out.append(r"\caption{待补充}\label{tbl:todo}")
                out.append(r"\begin{tabular}{" + "l" * n_cols + "}")
                out.append(r"\toprule")
                out.append(" & ".join(cells) + r" \\")
                out.append(r"\midrule")
                in_table = True
            else:
                # 内容行
                escaped = [_latex_inline(c) for c in cells]
                out.append(" & ".join(escaped) + r" \\")
            continue

        if in_table:
            out.append(r"\bottomrule")
            out.append(r"\end{tabular}")
            out.append(r"\end{table}")
            in_table = False
            # 不 continue，让当前行(非表格)被正常处理

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
    if in_verbatim: out.append(r"\end{verbatim}")
    if in_table:
        out.append(r"\bottomrule")
        out.append(r"\end{tabular}")
        out.append(r"\end{table}")

    # 恢复被保护的 LaTeX 命令
    result = "\n".join(out)
    for key, value in protected.items():
        result = result.replace(key, value)
    return result


def _latex_inline(text: str) -> str:
    """行内 LaTeX 转义。$...$ 内原样保留。"""
    # 分割 $...$ 内容，分别处理
    parts = re.split(r'(\$[^$]+\$)', text)
    result = []
    for part in parts:
        if part.startswith("$") and part.endswith("$"):
            result.append(part)  # 数学模式原样保留
        else:
            part = part.replace("\\", "\\textbackslash ")
            for ch in "&%#_{}~^":
                part = part.replace(ch, "\\" + ch)
            part = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', part)
            part = re.sub(r'\*(.+?)\*', r'\\textit{\1}', part)
            part = re.sub(r'`([^`]+)`', r'\\texttt{\1}', part)
            result.append(part)
    return "".join(result)


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python scripts/render.py <input.md> [--html|--latex] [-o output] [--open]")
        print("  --html   输出 A4 HTML 报告（展示/汇报）")
        print("  --latex  输出 Elsevier CAS 单栏论文（投稿）")
        print("  默认: --html")
        sys.exit(1)

    input_path = None
    output_path = None
    open_browser = False
    mode = "html"

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

    meta = parse_front_matter(str(src))
    body_md = parse_body(str(src))

    if mode == "latex":
        body_converted = md_to_latex(body_md)
        result = build_latex(meta, body_converted)
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
