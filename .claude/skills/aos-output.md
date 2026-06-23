---
name: aos-output
description: >-
  AOS 学术输出规范——定义论文/报告的排版标准、图片嵌入、公式规范、
  表格、引用、交叉引用等全部格式要求。覆盖 HTML 报告和 LaTeX 论文两种输出。
  Use this skill when generating any formatted output from atoms/aggregates,
  or when the user asks about "格式", "排版", "图片", "公式", "引用",
  "render", "输出", "export PDF", "A4", "format paper".
---

# AOS 学术输出规范

两种输出格式，规则统一：

| 格式 | 模板 | 用途 |
|------|------|------|
| HTML 报告 | `templates/output.css` | 展示/汇报/快速预览 |
| LaTeX 论文 | `templates/paper-elsevier-sc.tex` | 投稿（Elsevier CAS 单栏） |

---

## 零、结构规范

生成任何学术产出前，先检查结构完整性。

### 学术论文（LaTeX 投稿用）

| 章节 | 必须包含 | 常见错误 |
|------|---------|---------|
| **Title** | 研究对象 + 方法关键词 + 贡献暗示 | 太长（>20词）、太泛（"A Study on..."） |
| **Abstract** | ①问题 ②方法 ③关键结果（带数字）④结论 | 只描述做了什么不说发现了什么 |
| **Introduction** | ①背景 ②研究缺口 ③本文方案 ④贡献列表（3–5条） | 贡献写成"我们做了X"而非"我们首次证明X" |
| **Related Work** | 按主题分组，每组结尾指出与本文差异 | 流水账罗列文献、无批判 |
| **Method** | ①整体框架图 ②每模块数学/算法描述 ③设计动机 | 只有公式无解释、缺实现细节无法复现 |
| **Experiments** | ①实验设置（数据/指标/基线/环境）②主结果表 ③消融 ④可视化 ⑤统计检验 | 只报最优值不说波动、缺误差线/显著性 |
| **Discussion** | ①结果解读 ②与已有工作对比 ③局限性 ④实际意义 | 重复 Results、回避失败案例 |
| **Conclusion** | ①总结贡献 ②未来方向（≤2条） | 引入新材料、夸大结论 |
| **References** | 全、新、相关，覆盖关键基线 | 自引过多、缺关键基线文献 |

**结构检查清单**（AI 生成初稿后必须过一遍）：

- [ ] 摘要含具体数字（不是"性能提升显著"）
- [ ] Introduction 末尾有 3–5 条贡献
- [ ] Method 有框架图引用
- [ ] Experiments 主表有统计检验（p 值/标准差）
- [ ] Discussion 明确写了局限性
- [ ] Conclusion 无新信息出现

### 汇报报告（HTML 展示用）

| 要素 | 规则 |
|------|------|
| **一页一主题** | 禁止在一页挤多个论点 |
| **先说结论** | 每页第一行是该页核心信息 |
| **图表 > 文字** | 核心信息用图/表呈现，文字是注解 |
| **关键数字突出** | 提升 3.2% → 大号加粗或变色 |
| **统一配色** | ≤3 种主色，图表风格一致，中英文字体统一 |
| **Take-home message** | 最后一页：一句话总结，听众唯一该记住的 |
| **页码 + 进度** | 每页显示"3/12"样式进度 |

---

## 一、图片规范

### 1.1 嵌入方式

**HTML 报告：**
```markdown
![图片说明](../data/figures/fig1-architecture.png)
```
渲染为 `<figure><img><figcaption>` 结构，居中，不跨页断裂。

**LaTeX 论文：**
```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\linewidth]{figures/fig1-architecture.pdf}
  \caption{模型架构示意图。\label{fig:architecture}}
\end{figure}
```

### 1.2 图片要求

| 要求 | HTML | LaTeX |
|------|------|-------|
| 格式 | PNG / JPEG / SVG | PDF（矢量） / PNG（位图） |
| 分辨率 | ≥ 150 DPI | ≥ 300 DPI（位图） |
| 颜色模式 | RGB | CMYK（印刷）/ RGB（在线） |
| 尺寸 | 宽度 ≤ 页面宽度 | `width=\linewidth` 或 `0.8\linewidth` |
| 编号 | 手动 | `\label{fig:xxx}` 自动 |

### 1.3 图题（Caption）

- 图题在图片**下方**
- 格式：`图 X. 描述内容`（中文）/ `Figure X. Description.`（英文）
- 图题不以句号结尾（英文除外，且英文用句号）
- 图题中引用文献用 `\citep{xxx}`（LaTeX）或 `[@xxx]`（Markdown）

### 1.4 子图

**LaTeX 子图：**
```latex
\begin{figure}[htbp]
  \centering
  \subfloat[子图A说明]{\includegraphics[width=0.45\linewidth]{fig-a.pdf}\label{fig:a}}
  \hfill
  \subfloat[子图B说明]{\includegraphics[width=0.45\linewidth]{fig-b.pdf}\label{fig:b}}
  \caption{总图题。\label{fig:combined}}
\end{figure}
```

**HTML 子图：**并排排列，各带 `<figcaption>`。

---

## 二、公式规范

### 2.1 嵌入方式

**HTML 报告**（Markdown 中）：
```
行内公式: $E = mc^2$
独立公式:
$$
\mathcal{L} = -\frac{1}{N} \sum_{i=1}^{N} y_i \log(\hat{y}_i)
$$
```
CSS 自动居中独立公式并编号。

**LaTeX 论文**：标准 LaTeX 数学模式。

### 2.2 公式编号

- 需要引用的公式必须编号
- LaTeX：`\begin{equation}...\label{eq:xxx}\end{equation}`
- HTML：`$$...$$` 后手动标注 `(1)`
- 编号按章节：(1.1)、(1.2)，或全文连续：(1)、(2)

### 2.3 符号规范

| 类别 | 格式 | 示例 |
|------|------|------|
| 标量 | 斜体 | $x$, $y$, $\alpha$ |
| 向量 | 粗斜体 | $\mathbf{x}$, $\boldsymbol{\alpha}$ |
| 矩阵 | 粗正体 | $\mathbf{X}$, $\mathbf{A}$ |
| 集合 | 空心体 | $\mathbb{R}$, $\mathbb{E}$ |
| 分布 | 书法体 | $\mathcal{N}$, $\mathcal{L}$ |
| 转置 | $^\top$（非 $^T$） | $\mathbf{X}^\top$ |
| 期望 | $\mathbb{E}[\cdot]$ | $\mathbb{E}_{x\sim p}[f(x)]$ |

### 2.4 公式标点

公式视为句子的一部分，末尾加逗号或句号：
```latex
\begin{equation}
  f(x) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{x^2}{2\sigma^2}\right),
  \label{eq:gaussian}
\end{equation}
```

---

## 三、表格规范

### 3.1 表格格式

**LaTeX**（Elsevier 推荐三线表）：
```latex
\begin{table}[htbp]
  \caption{实验结果对比。\label{tbl:results}}
  \begin{tabular*}{\tblwidth}{@{}LLL@{}}
  \toprule
    方法 & Dice (\%) & HD (mm) \\
  \midrule
    U-Net & 89.3 & 4.2 \\
    Ours & \textbf{93.1} & \textbf{2.8} \\
  \bottomrule
  \end{tabular*}
\end{table}
```

**HTML**：标准 Markdown 表格，CSS 自动三线样式。

### 3.2 表格规则

- 表题在表格**上方**
- 格式：`表 X. 描述` / `Table X. Description.`
- 仅使用横线（三线表），禁止竖线
- 数据右对齐，文字左对齐
- 最优值加粗
- 数值保留有效位数一致（如全部保留 1 位小数）
- 大表用 `\scriptsize` 或 `\footnotesize`

---

## 四、引用规范

### 4.1 文献引用

**LaTeX：**
```latex
\citep{zhang2023}     % 括号引用：(Zhang et al., 2023)
\citet{zhang2023}     % 正文引用：Zhang et al. (2023)
```
引用格式：作者-年份（`natbib` authoryear）。

**HTML/Markdown：**
```
[@zhang2023]          % 渲染为 [1] 或 (Zhang et al., 2023)
```

### 4.2 引用位置

- 引用放在标点符号**之前**：`...效果显著\citep{zhang2023}。`
- 不要放在章节标题中
- 摘要中不引用文献（除非必要）

### 4.3 交叉引用

| 引用对象 | LaTeX | Markdown |
|---------|-------|----------|
| 图 | `图\ref{fig:xxx}` | `[图 X](#fig-xxx)` |
| 表 | `表\ref{tbl:xxx}` | `[表 X](#tbl-xxx)` |
| 公式 | `公式\eqref{eq:xxx}` | `公式 (X)` |
| 节 | `第\ref{sec:xxx}节` | `[第 X 节](#sec-xxx)` |

---

## 五、排版细则

### 5.1 数字与单位

- 数字与单位之间有空格：`5.2 mm`、`37 °C`、`128×128 pixels`
- 千位分隔用逗号（英文）/ 空格（中文）：`1,024` / `1 024`
- 范围用破折号：`3–5 mm`（非 `3-5 mm`）
- 百分号与数字不空格：`95%`

### 5.2 缩写

- 首次出现必须全称 + 缩写：`convolutional neural network (CNN)`
- 摘要中也需定义（摘要独立阅读）
- 常见缩写可免定义：`RGB`、`GPU`、`CPU`、`PDF`

### 5.3 章节标题

- 不使用编号为 0 的节（如 `0. Introduction`）
- 标题层级不超过 4 级
- 标题不加粗关键词、不引用文献、不加脚注
- 标题使用名词短语，非完整句

### 5.4 段落与行文

- 每段 3–8 句，单一主题
- 首段（摘要后的第一段）不缩进
- 避免一个句子超过 3 行
- 中文用中文标点（，。）；英文用英文标点 (, .)
- 引号：中文用「」，英文用 ""

---

## 六、页面布局

| 属性 | HTML | LaTeX |
|------|------|-------|
| 纸张 | A4 | A4 |
| 页边距 | 上/下 25mm, 左/右 20mm | 同 |
| 行距 | 1.8 | 1.5 倍 |
| 正文字号 | 11pt | 12pt |
| 字体 | Source Serif / Noto Serif CJK SC | 同 |
| 页码 | 底部居中 | `\fancyfoot[C]{\thepage}` |

---

## 七、命令速查

```bash
# HTML 报告（展示/汇报）
python scripts/aggregate.py <proj> --html -o report.html

# LaTeX 论文（投稿）
python scripts/aggregate.py <proj> > draft.md        # 出 Markdown 草稿
# ... 人编辑草稿 ...
python scripts/render.py draft.md --latex -o paper.tex

# 编译
cp templates/elsevier/* .
xelatex paper && xelatex paper
```
