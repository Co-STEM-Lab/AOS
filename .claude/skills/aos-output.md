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

两种输出格式：

| 格式 | 模板 | 用途 |
|------|------|------|
| **HTML 报告** | `templates/output.css` | 展示/汇报/快速预览 |
| **LaTeX 论文** | `templates/paper-elsevier-sc.tex` | 投稿（Elsevier CAS 单栏） |

## 渲染管线

```
原子 → aggregate.py --html → A4 HTML 报告（快速预览）
原子 → aggregate.py → Markdown → 人编辑 → render.py --latex → LaTeX 论文（投稿）
```

### 命令

```bash
# HTML 报告（展示/汇报）
python scripts/aggregate.py <proj> --html -o report.html

# LaTeX 论文（投稿）
python scripts/aggregate.py <proj> > draft.md
# ... 人编辑 draft.md ...
python scripts/render.py draft.md --latex -o paper.tex

# 编译（需复制 templates/elsevier/* 到 .tex 同目录）
cp templates/elsevier/* .
xelatex paper && xelatex paper
```
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

## 输入格式

Markdown 文件带 YAML front-matter。HTML 报告用简单字段，LaTeX 论文用 Elsevier 完整字段。

### HTML 报告（简单）

```yaml
---
title: "论文标题"
authors: "张三, 李四"
affiliation: "某某大学"
abstract: "摘要..."
keywords: "关键词1, 关键词2"
---
```

### LaTeX 论文（Elsevier CAS 完整）

```yaml
---
title: "A Novel Method for Medical Image Segmentation"
shorttitle: "Novel Medical Image Segmentation"
shortauthors: "Zhang et al."
author1: "San Zhang"
orcid1: "0000-0001-2345-6789"
email1: "zhang@university.edu"
credit1: "Conceptualization, Methodology"
org1: "University of Science"
city1: "Beijing"
country1: "China"
# author2, author3 ... 同上
abstract: "We propose..."
keywords: "deep learning \\sep medical imaging \\sep segmentation"
bibfile: "references"
---
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
