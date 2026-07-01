# 学术写作指南

> 从草稿到投稿的格式规范。搭配 `scripts/render.py` 使用，同一 Markdown 源输出 HTML 报告和 LaTeX 论文。

---

## 论文结构清单

| 章节 | 必须包含 | 常见错误 |
|------|---------|---------|
| **Title** | 研究对象 + 方法关键词 + 贡献暗示 | 太长（>20词）、太泛 |
| **Abstract** | ①问题 ②方法 ③关键结果（带数字）④结论 | 只描述做了什么不说发现了什么 |
| **Introduction** | ①背景 ②研究缺口 ③本文方案 ④贡献列表（3–5条） | 贡献写成"我们做了X"而非"我们首次证明X" |
| **Related Work** | 按主题分组，每组结尾指出与本文差异 | 流水账罗列、无批判 |
| **Method** | ①整体框架图 ②每模块描述 ③设计动机 | 只有公式无解释、缺实现细节 |
| **Experiments** | ①设置（数据/指标/基线/环境）②主结果表 ③消融 ④统计检验 | 只报最优值不提波动、缺误差线 |
| **Discussion** | ①结果解读 ②对比 ③局限性 ④实际意义 | 重复 Results、回避失败案例 |
| **Conclusion** | ①总结贡献 ②未来方向（≤2条） | 引入新材料、夸大结论 |

**每段 3–8 句，单一主题。**

---

## Markdown 源格式

HTML 和 LaTeX 都从同一份 Markdown 转换而来。

### 元素映射

| 元素 | Markdown | HTML 输出 | LaTeX 输出 |
|------|---------|-----------|-----------|
| 一级标题 | `# 标题` | `<h1>` | `\section{标题}` |
| 二级标题 | `## 标题` | `<h2>` | `\subsection{标题}` |
| 三级标题 | `### 标题` | `<h3>` | `\subsubsection{标题}` |
| 粗体 | `**文字**` | `<strong>` | `\textbf{文字}` |
| 斜体 | `*文字*` | `<em>` | `\textit{文字}` |
| 代码 | `` `code` `` | `<code>` | `\texttt{code}` |
| 无序列表 | `- 项目` | `<ul>` | `\begin{itemize}` |
| 有序列表 | `1. 项目` | `<ol>` | `\begin{enumerate}` |
| 行内公式 | `$E=mc^2$` | MathJax | 原样保留 |
| 独立公式 | `$$...$$` | MathJax | `\begin{equation}` |
| 图片 | `![图题](path)` | `<figure>` | `\begin{figure}` |
| 表格 | `\| A \| B \|` | `<table>` | 三线表 `\toprule` |
| 引用 | `[@key]` | `(Author, year)` | `\citep{key}` |

### 格式规则

- **段落间空一行**。不空行 = 同一段落。
- **标题后空一行**再写正文。
- **公式单独成段**，前后各空一行。
- **图片路径用相对路径**：`figures/fig1.png`
- **表格用简单 Markdown**，`render.py` 自动转 LaTeX 三线表。

---

## 图片规范

### 嵌入

```markdown
![图片说明](figures/architecture.png)
```

HTML 渲染为 `<figure><img><figcaption>`，LaTeX 为 `\begin{figure}`。

### 要求

| 要求 | HTML | LaTeX |
|------|------|-------|
| 格式 | PNG / JPEG / SVG | PDF（矢量）/ PNG（位图） |
| 分辨率 | ≥ 150 DPI | ≥ 300 DPI |
| 尺寸 | 宽度 ≤ 页面宽度 | `width=\linewidth` |

### 图题

- 图题在图**下方**。
- 中文章节：`图 X. 描述`。英文：`Figure X. Description.`
- 图题中引用文献：`[@key]`。

---

## 公式规范

### 嵌入

```markdown
行内公式: $E = mc^2$

独立公式:
$$
\mathcal{L} = -\frac{1}{N} \sum_{i=1}^{N} y_i \log(\hat{y}_i)
$$
```

### 符号规范

| 类别 | 格式 | 示例 |
|------|------|------|
| 标量 | 斜体 | $x$, $\alpha$ |
| 向量 | 粗斜体 | $\mathbf{x}$ |
| 矩阵 | 粗正体 | $\mathbf{X}$ |
| 集合 | 空心体 | $\mathbb{R}$ |
| 分布 | 书法体 | $\mathcal{N}$ |

- 需要引用的公式必须编号
- 公式视为句子的一部分，末尾加逗号或句号

---

## 表格规范

### Markdown 源（`render.py` 自动转 LaTeX 三线表）

```markdown
| 方法 | Dice (%) | HD (mm) |
|------|---------|---------|
| U-Net | 89.3 | 4.2 |
| Ours | **93.1** | **2.8** |
```

### 规则

- 表题在表**上方**：`表 X. 描述` / `Table X. Description.`
- 仅用横线，禁止竖线
- 最优值加粗
- 数值保留一致的有效位数

---

## 引用规范

### Markdown 源

```markdown
引用: [@zhang2023]
多篇: [@zhang2023; @li2024]
正文: 如 @zhang2023 所示...
```

### render.py 转换

| 输入 | LaTeX 输出 | 渲染效果 |
|------|-----------|---------|
| `[@zhang2023]` | `\citep{zhang2023}` | (Zhang et al., 2023) |
| `@zhang2023` | `\citet{zhang2023}` | Zhang et al. (2023) |

### 引用位置

- 引用放在标点**之前**：`效果显著 [@zhang2023]。`
- 不在章节标题中引用
- 摘要中尽量不引用

---

## 排版细则

### 数字与单位

- 数字与单位间有空格：`5.2 mm`、`37 °C`
- 范围用破折号：`3–5 mm`（非 `3-5 mm`）
- 百分号不空格：`95%`

### 缩写

- 首次出现必须全称 + 缩写：`convolutional neural network (CNN)`
- 摘要中也需定义（摘要独立阅读）

### 章节标题

- 使用名词短语，非完整句
- 标题不超过 4 级
- 不加粗关键词、不引用文献

### 标点

- 中文用中文标点（，。）；英文用英文标点 (, .)
- 引号：中文用「」，英文用 ""

---

## 渲染命令

```bash
# HTML 报告（展示/汇报）
python scripts/render.py draft.md --html -o report.html

# LaTeX 论文（Elsevier 投稿）
python scripts/render.py draft.md --latex -o paper.tex

# 编译 LaTeX
cp templates/elsevier/* .
xelatex paper && xelatex paper
```
