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

定义 AOS 的学术输出排版标准，并提供 Markdown → A4 HTML 渲染管线。

## 排版标准（`templates/output.css`）

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

## 可选增强

```bash
# 安装完整 Markdown 解析器（表格、代码高亮更好）
pip install markdown
```

## 样式自定义

修改 `templates/output.css` 后，所有渲染自动生效。CSS 使用 `@media print` 确保打印/导出 PDF 时格式正确。

## 输出位置

```
outputs/papers/     → 论文
outputs/proposals/  → 基金本子
outputs/talks/      → 演讲 slides
```
