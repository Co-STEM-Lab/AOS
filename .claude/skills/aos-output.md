---
name: aos-output
description: >-
  AOS 学术输出排版——将 Markdown 原子/聚合产物渲染为 A4 纸规格的 HTML，
  适合打印或导出 PDF。定义排版标准（页边距、字体、行距、标题层级）。
  Use this skill when the user asks to "render", "输出", "排版",
  "format paper", "格式化", "导出 PDF", "打印", "A4", or when
  generating final output from atoms/aggregates.
---

# AOS Output Skill

两种输出格式，用途不同：

| 格式 | 模板 | 用途 | 命令 |
|------|------|------|------|
| **HTML 报告** | `templates/output.css` | 展示/汇报/快速预览 | `--html` |
| **LaTeX 论文** | `templates/paper-latex.tex` | 期刊/会议投稿 | `--latex` |

## 渲染管线

```
原子 → aggregate.py --html → A4 HTML 报告（快速预览）
原子 → aggregate.py → Markdown → 人编辑 → render.py --latex → LaTeX 论文（投稿）
```

### 命令

```bash
# HTML 报告（展示用）
python scripts/aggregate.py <proj> --html -o report.html

# LaTeX 论文（投稿用）
python scripts/aggregate.py <proj> > draft.md       # 出 MD 草稿
# ... 人编辑 draft.md ...
python scripts/render.py draft.md --latex -o paper.tex

# 编译 LaTeX → PDF
xelatex paper.tex && xelatex paper.tex
```

## HTML 排版标准（`templates/output.css`）

A4 报告模板，适合打印/导出 PDF。

| 属性 | 值 |
|------|-----|
| 纸张 | A4 (210mm × 297mm) |
| 页边距 | 上/下 25mm，左/右 20mm |
| 正文字体 | Source Serif 4 / Noto Serif CJK SC，11pt |
| 标题字体 | Source Sans 3 / Noto Sans CJK SC |
| 代码字体 | Source Code Pro / monospace，9pt |
| 行高 | 1.8 |
| 首行缩进 | 2em（首段除外） |
| 对齐 | 两端对齐 (justify) |
| 页码 | 底部居中 |

## 渲染管线

```
原子 → aggregate.py → Markdown 初稿 → render.py → A4 HTML → 浏览器打印 → PDF
```

### 命令

```bash
# Markdown → 排好版的 A4 HTML
python scripts/render.py paper.md -o paper.html

# 生成并在浏览器打开
python scripts/render.py paper.md -o paper.html --open
```

### 输入格式

Markdown 文件带 YAML front-matter：

```yaml
---
title: "论文标题"
authors: "作者一, 作者二"
affiliation: "某某大学"
abstract: "摘要内容..."
keywords: "关键词1, 关键词2"
references:
  - "Author A. Title. Journal, Year."
  - "Author B. Another Title. Conf, Year."
---

# 引言

正文内容...
```

## LaTeX 排版标准（`templates/paper-latex.tex`）

中文 LaTeX 论文模板，基于 `ctexart`。

| 属性 | 值 |
|------|-----|
| 文档类 | ctexart 12pt A4 |
| 行距 | 1.5 倍 |
| 中文字体 | Noto Serif/Sans CJK SC |
| 英文字体 | Source Serif 4 / Source Sans 3 |
| 参考文献 | natbib + plainnat |

### 编译

```bash
xelatex paper.tex
xelatex paper.tex   # 两次以生成目录/参考文献
```

## 可选增强

```bash
# 安装完整 Markdown 解析器（表格、代码高亮更好）
pip install markdown
```

## 自定义

修改 `templates/output.css`（HTML）或 `templates/paper-latex.tex`（LaTeX）后，所有渲染自动生效。

## 输出位置

```
outputs/papers/     → 论文（.tex / .html）
outputs/proposals/  → 基金本子
outputs/talks/      → 演讲 slides
```
outputs/proposals/  → 基金本子
outputs/talks/      → 演讲 slides
```
