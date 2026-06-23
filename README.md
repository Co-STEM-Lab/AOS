# Academic Operating System (AOS)

> **你的学术底层操作系统。** 将能力库、知识库和产出管线融合成一个可迭代的活系统。
>
> 核心理念：**知识支撑能力 → 能力推动产出 → 产出倒逼知识和能力升级。**

---

## 管理命令

```bash
source venv/bin/activate

# 扫描系统健康（统一入口）
python scripts/scan.py
python scripts/scan.py --log        # 扫描 + 写维护日志

# 自动修复（文档同步 + 格式修正）
python scripts/check_invariants.py --fix

# 全量烟雾测试（验证所有脚本可用）
python scripts/smoke.py             # 10 项全检
python scripts/smoke.py --quick     # 8 项快检

# 聚合原子生成论文初稿
python scripts/aggregate.py <项目id>
python scripts/aggregate.py <项目id> --execute   # 执行计算原子

# 安装 pre-commit 硬守卫
bash scripts/install-hooks.sh
```

---

## 操控指南

**人不维护文档。** 系统自动同步 README 树、CLAUDE.md 列表、矩阵引用。人只做三件事：

| 你做的事 | 系统做的事 |
|---------|-----------|
| 写原子（`knowledge/atoms/xxx.md`） | `--fix` 自动校验格式、补全字段 |
| 写项目卡片（`projects/xxx/index.md`） | `--fix` 自动更新 matrix.md 矩阵 |
| `git diff` 审核变更 | `pre-commit` 自动拦截非法提交 |

### 日常操作

```bash
# 改完任何文件后
python scripts/check_invariants.py --fix   # 一键修复 + 同步全部文档
python scripts/scan.py                     # 确认全绿
git add -A && git commit -m "..."          # pre-commit 自动把关
```

### 新建原子

```bash
cp templates/atom-template.md knowledge/atoms/gap-0002.md
# 填写 front-matter + 核心断言
python scripts/check_invariants.py --fix   # 自动补全 created/status/id 前缀
```

### 新建项目

```bash
mkdir -p projects/active/proj-xxx
cp templates/project-template.md projects/active/proj-xxx/index.md
# 填写 domain + problem（必填！矩阵自动填充依赖这两个字段）
python scripts/check_invariants.py --fix   # matrix.md 自动更新
```

### 生成产出

```bash
python scripts/aggregate.py proj-xxx --html -o report.html  # HTML 报告
python scripts/aggregate.py proj-xxx > draft.md              # Markdown 草稿
python scripts/render.py draft.md --latex -o paper.tex        # LaTeX 论文
```

---

## AI 协作技能

对 Claude Code 说以下任意指令，AI 自动加载对应技能：

| 技能 | 触发方式 | 做什么 |
|------|---------|--------|
| `qian-skill` | 任何多模块/重构/性能排查 | 钱学森系统方法论：诊断 → 总体设计 → 涌现检查 |
| `aos-guardian` | "检查 AOS" / "扫描" | 不变式巡检 + 新鲜度漂移 + 修复提案 |
| `aos-operations` | 任何 AOS 文件修改 | 操作引导：建原子/建项目时自动检查格式和关联 |
| `aos-output` | "渲染" / "排版" / "导出" | 学术输出规范：图片/公式/表格/引用格式 |
| `run-aos` | "run AOS" / "test AOS" | 全量烟雾测试：12 项检查验证全仓可用 |

---

## 为什么需要 AOS？

三个最常见的学术工作断裂：

| 断裂 | 症状 | AOS 的解法 |
|------|------|------------|
| 知识散落 | 读过的论文、实验中间结果散落在 Zotero/Notion/本地文件夹，写作时找不到可用的材料 | **产出原子**：知识以最小可重组单元存储，带结构化标签，随时检索组合 |
| 能力不可见 | 感觉自己一直在进步，但没有证据，简历和基金申请时无法精确展示 | **技能树 + 证据链**：每条技能声明绑定具体项目和产出 |
| 产出模糊 | 不知道下一个项目做什么，手头几个项目进度不透明 | **产出矩阵**：领域×问题网格，空白即方向；项目状态一目了然 |

---

## 系统结构

```
academic-operating-system/
├── CLAUDE.md                     # 🤖 AI 入口（每次对话自动加载）
├── README.md                      # 本文件
├── matrix.md                     # 🎯 研究领域 × 核心问题矩阵
│
├── .claude/                      # AI 配置
│   ├── rules/                           # 硬约束
│   └── skills/                          # 协作技能
│
├── knowledge/                     # 🧠 知识库
│   ├── atoms/                        # 产出原子（最小可重组知识单元）
│   │   ├── scripts/                      # 计算原子配套的可复用脚本
│   │   │   └── compute-0001.py
│   │   ├── compute-0001.md
│   │   ├── example-compute-0001.md
│   │   └── example-gap-0001.md
│   ├── datasets/                     # 数据集描述
│   ├── literature/                   # 文献笔记
│   ├── controlled-vocabulary.yml     # 受控标签词汇表
│   └── maintenance-log.md            # 系统维护日志
│
├── competencies/                  # 💪 人的学术能力库
│   └── skill-tree.md                 # 技能树（自评 + 证据 + 成长路径）
│
├── projects/                      # 🔄 项目管线
│   ├── active/                       # 进行中
│   ├── completed/                    # 已完成
│   └── ideas/                        # 想法池
│
├── outputs/                       # 📄 聚合产物
│   ├── papers/                       # 论文草稿
│   ├── proposals/                    # 基金本子
│   └── talks/                        # 演讲 slides
│
├── templates/                     # 📋 标准化模板
│   ├── elsevier/
│   │   ├── cas-common.sty
│   │   ├── cas-dc.cls
│   │   ├── cas-model2-names.bst
│   │   └── cas-sc.cls
│   ├── atom-template.md              # 原子模板
│   ├── output.css
│   ├── paper-elsevier-sc.tex
│   ├── paper-template.md             # 论文草稿模板
│   ├── project-template.md           # 项目卡片模板
│   └── skill-template.md             # 技能项模板
│
├── scripts/                       # 🔧 辅助工具
│   ├── aggregate.py                  # 聚合原子生成初稿
│   ├── check_invariants.py           # 不变式校验引擎
│   ├── check_status.py               # 系统健康度 + 新鲜度
│   ├── install-hooks.sh              # 安装 pre-commit hook
│   ├── render.py
│   ├── scan.py                       # 统一扫描入口
│   └── smoke.py                      # 全量烟雾测试（= run-aos driver）
│
└── data/                          # 📊 示例/测试数据
    └── experiment_results.csv
```

---

## 核心概念：产出原子

**原子是 AOS 的最小可重组知识单元。** 每个原子含一句可独立引用的核心断言 + 支撑证据 + 适用场景标签。

### 原子结构

```yaml
---
id: "gap-0001"
title: "动态场景下X方法缺乏验证"   # ≤15 字
type: gap                           # gap | method | result | insight
tags: ["#引言缺口", "#医学影像"]     # 结构标签 + 领域标签
project: "proj-dynamic-X"           # 归属项目
status: final                       # draft | final
---
# 核心断言
现有研究仅在静态数据集上验证了X方法，尚未在动态流数据上测试。

## 证据
- Zhang et al. (2023) 的结论仅限于静态子集
- 我们的预实验精度下降 >15%

## 适用场景
写引言"研究缺口"段落时直接引用。
```

### 五种原子类型

| 类型 | 用途 | 标签 | 典型来源 |
|------|------|------|----------|
| `gap` | 研究缺口 | `#引言缺口` | 文献阅读、审稿意见 |
| `method` | 方法组件 | `#方法组件` | 论文复现、技术迁移 |
| `result` | 实验结果 | `#结果讨论` | 实验记录、基线对比 |
| `insight` | 洞察/解释 | `#结果讨论` | 事后分析、reviewer 反馈 |
| `compute` | ⚡ 可执行计算 | 任意结构标签 | 统计检验、数据预处理、可视化管线 |

### 计算原子：知识即代码

有些知识的本质是**过程性的**——预处理管线、统计检验、基线复现、可视化。它们的"原子形式"天然包含可执行脚本。

计算原子 = 标准原子 + 可复现脚本。

```
knowledge/atoms/
├── compute-0001.md                # 计算原子（描述脚本做什么）
├── compute-0002.md                # 另一个计算原子
└── scripts/                       # 所有可复用脚本集中存放
    ├── compute-0001.py            # 文件 = 原子 id 的去前缀部分
    └── compute-0002.py
```

**脚本约定**：
- 自包含：给定输入 → 独立运行 → 复现结果（不依赖隐式路径、全局状态）
- 命令行接口：`--input` 接收数据文件，stdout 输出结构化结果（JSON 推荐）
- 依赖声明：在原子 front-matter 的 `script_deps` 中标明（如 `["numpy", "scipy"]`）
- 纯文本优先：简单计算（≤30 行）可内嵌在原子正文；复杂计算独立脚本

**使用方式**：

```bash
# 纯文本聚合（不执行脚本，仅展示原子内容）
python scripts/aggregate.py proj-dynamic-X

# 执行模式：运行所有计算原子脚本，结果嵌入初稿
python scripts/aggregate.py proj-dynamic-X --execute

# 指定不同输入数据
python scripts/aggregate.py proj-dynamic-X --execute --input data/experiment_v2.csv
```

### 原子为何有效？

一篇论文本质上是一组原子的有序排列：
- **引言** = 缺口原子 × N → 串联成叙事
- **方法** = 方法原子 × 3~5 → 按逻辑排列
- **实验** = 结果原子 × 5~10 → 按假设分组
- **讨论** = 洞察原子 × 3~5 → 解释 + 对比 + 局限

**当原子库存 ≥ 50 时，初稿生成出现质变**——你不再对空白页发呆，而是在排列已有材料。

---

## 核心概念：产出矩阵

`matrix.md` 是一张 **"领域 × 核心问题"** 表格。它不是静态展示架，而是你的**学术产线机床**。

### 两种模式

**展示模式**（简历/基金申请时）：
- 一眼看清哪些格子有成果，哪些是空白
- 用符号标注状态：💡想法 / 🔬实验 / ✍️在写 / 📤已投 / ✅发表

**产出模式**（日常研究时）：
- 当某个格子的原子积累到阈值（如 ≥10 个缺口原子），在 `projects/ideas/` 创建新项目
- 空白格 = 战略方向（是否值得开新领域？）

### 矩阵示例

| 研究领域 \ 核心问题 | 可解释性 | 数据异质性 | 小样本泛化 |
|---------------------|----------|-----------|-----------|
| 医学影像            | ✅ 已发表 | ✍️ 在写    | 💡 想法    |
| 遥感                | —        | 🔬 实验中  | —         |

---

## 核心概念：技能树

`competencies/skill-tree.md` 是你的学术能力清单。**每条技能必须有证据。**

| 技能 | 评级 | 证据 |
|------|------|------|
| 文献批判性阅读 | L3 熟练 | 维护 50+ 核心文献笔记，可 3 天内梳理出研究缺口 |
| 实验方案设计 | L2 能做 | 独立设计过 2 个项目的实验方案 |
| 学术论文写作 | L3 熟练 | 发表 3 篇一作论文 |

评级标准：**L1** 了解 / **L2** 能做 / **L3** 熟练 / **L4** 精通（可教，有方法论输出）。

每季度回顾一次，更新评级与证据。

---

## 工作流：从想法到发表

```
碎片收集 ──→ 原子化 ──→ 矩阵审视 ──→ 项目启动 ──→ 聚合渲染 ──→ 发表回存
```

### 第 0 步：捕获（随时）

灵感、文献要点、实验中间结果 → **立即写成原子**，存入 `knowledge/atoms/`。不要等"整理的时候再写"——碎片超过 24 小时不记录，可复用性断崖下跌。

### 第 1 步：原子化（每 1–3 天）

给原子打标签（至少 1 个结构标签 + 1 个领域标签），关联项目。用 `scripts/check_status.py` 看原子库存增长趋势。

### 第 2 步：矩阵审视（每周 10 分钟）

打开 `matrix.md`，看三件事：
1. 哪些格子积累了足够原子（≥10 个）→ 值得立项
2. 哪些格子长期空白 → 战略方向 or 自然空白？
3. 进行中项目的状态是否需要更新

### 第 3 步：项目推进（持续）

在 `projects/active/` 下为每个进行中项目创建卡片（使用 `templates/project-template.md`）。项目卡片记录：
- 关联原子列表（按角色分组）
- 进度日志（日期 / 进展 / 阻塞）
- 产出链接

### 第 4 步：聚合渲染（写作时）

```bash
# 纯文本聚合：按项目提取原子，生成论文初稿
python scripts/aggregate.py proj-dynamic-X > outputs/papers/proj-dynamic-X-draft.md

# 执行模式：同时运行所有计算原子脚本，结果嵌在初稿中
python scripts/aggregate.py proj-dynamic-X --execute > outputs/papers/proj-dynamic-X-draft.md
```

脚本做的事：按 `#引言缺口` / `#方法组件` / `#结果讨论` 分组输出原子内容；`--execute` 模式下，计算原子的脚本被实际执行，输出（p 值、效应量、预处理统计等）自动嵌入对应段落。**你只做排列和润色，不做从零写作。**

### 第 5 步：发表后回存（每篇论文完成后）

论文发表后，把审稿意见、修改内容以新原子形式回存到 `knowledge/atoms/`，更新项目状态为 `published`，迁移到 `projects/completed/`。

---

## 系统不变式

这些规则保证系统长期可用，违反任何一条都会逐渐瓦解：

1. **原子独立可引用** — 删除任何项目，其关联原子不丢失信息，仍可被其他项目重组。
2. **证据前置** — 任何技能声明必须有对应项目或产出作为证据。无证据 = 不填写评级。
3. **矩阵封闭** — 每个项目必须映射到矩阵中的一个且仅一个格子。
4. **标签一致** — 原子标签使用受控词汇（`#引言缺口`、`#方法组件`、`#结果讨论`），不得自由创建以避免漂移。
5. **人不可替代** — 脚本只做聚合，不做决策。原子创建、技能评估、项目启动的决策权永远在人。
6. **脚本自包含** — 任何计算原子的脚本，提取文件 + 满足 `script_deps` + 给定 `script_input` → 应能独立运行并复现结果。禁止隐式依赖（硬编码绝对路径、未声明的系统库）。
7. **文档同步** — README.md 和 CLAUDE.md 中的目录结构、脚本列表、技能列表、不变式数量必须与实际项目一致。文档腐化 = 新成员无法上手。

---

## 系统守护：AOS Guardian

AOS 内置三层自主免疫系统，对应 Loop Engineering 的 Outer Loop 编排层，守护上述 7 条不变式不被侵蚀。

### 架构

```
Layer 1: 硬守卫（pre-commit hook）
  git commit → check_invariants.py → HARD 违规 = 拒绝提交

Layer 2: 软巡检（手动 / 定时触发）
  check_status.py → 新鲜度漂移检测 → 生成警告清单

Layer 3: 交互式 Loop（AI 对话触发）
  对 Claude Code 说 "检查 AOS" → AI 读取状态 → 提案 → 人拍板 → 执行 → 记录
```

### 安装

```bash
# 安装 pre-commit hook（一次性）
bash scripts/install-hooks.sh

# 之后每次 git commit 自动运行不变式检查
```

### 使用

```bash
# 不变式硬校验（commit 前 / CI）
python scripts/check_invariants.py           # 人类可读
python scripts/check_invariants.py --json    # 机器可读
python scripts/check_invariants.py --fix     # 尝试自动修复

# 系统健康面板（每周运行）
python scripts/check_status.py               # 完整面板
python scripts/check_status.py --freshness   # 仅漂移检测

# AI 辅助深度巡检（在 Claude Code 中）
"检查 AOS"
```

### 受控词汇表

`knowledge/controlled-vocabulary.yml` 是机器可读的唯一真相源。所有原子标签、类型枚举、技能等级都必须在此登记。新增标签需要先在词汇表注册，否则 pre-commit 拒绝。

### 维护日志

`knowledge/maintenance-log.md` 记录每次巡检和修复操作，形成不可篡改的审计轨迹。AI 巡检会自动追加记录。

### Guardian 不变式

8. **权限分级** — AI 只提议不擅改（Guardian Rules 显式声明）。自动修复仅限格式修正；内容修改必须人确认。紧急跳过 `SKIP_AOS_GUARDIAN=1 git commit`。

---

## 系统健康度指标

运行 `python scripts/check_status.py` 或 `python scripts/check_invariants.py`：

| 指标 | 健康阈值 | 警戒线 |
|------|----------|--------|
| 原子库存量 | ≥ 50 | < 10（初稿生成失效） |
| 矩阵覆盖率 | 领域持续增长 | 连续 3 月无新增项目 |
| 每月新增原子 | ≥ 5 | = 0（系统停转） |
| 想法→产出时间 | < 6 月 | > 12 月（项目停滞） |
| 技能证据密度 | ≥ 80% 技能有证据 | < 50%（可信度崩溃） |

---

## 立即启动

```bash
# 1. 克隆仓库
git clone <your-repo-url> academic-operating-system
cd academic-operating-system

# 2. 填写第一个真实内容
#    a. 打开 matrix.md，写下你最核心的一个领域和一个问题
#    b. 在 projects/active/ 下创建第一个项目卡片
#    c. 在 knowledge/atoms/ 中写下今天第一个原子

# 3. 上线
git add -A
git commit -m "Initialize my academic operating system"
git push

# 4. 安装脚本依赖（可选）
pip install pyyaml
python scripts/check_status.py
```

---

## 维护节奏

| 频率 | 动作 | 耗时 |
|------|------|------|
| 随时 | 捕获灵感 / 文献要点 → 写原子 | 2–5 分钟 |
| 每周 | 更新项目状态、审视矩阵、补原子 | 20 分钟 |
| 每季度 | 回顾技能树，更新评级与证据 | 30 分钟 |
| 每篇论文后 | 回存审稿原子，迁移项目 | 15 分钟 |

**核心心法**：让矩阵流动起来。想法 → 项目 → 原子 → 初稿 → 发表 → 新原子。你的学术产出不再是孤立文档，而是一个活的、可进化的知识网络。

---

## 设计原则

1. **可重组性 > 完整性** — 宁可原子少但粒度一致可重组，也不要大而全但无法调用的笔记
2. **流动性 > 精确性** — 系统必须流动（每周有更新），比精确但停滞更有价值
3. **产出速度 > 系统完善度** — 先产出、后优化系统，不追求完美架构再开工
4. **纯文本 > 工具链** — Markdown + YAML + Git，零平台锁定，任何编辑器可用
5. **控制论完备** — 可观性（`check_status.py`）/ 可控性（Git 回滚）/ 稳定性（单文件隔离，单点损坏不影响整体）

---

## 系统级涌现风险

AOS 的涌现行为需要主动管理：

- **反馈回路警惕**：当一个领域持续产出 → 更多原子流向该领域 → 更多项目启动 → 其他领域被挤压。定期用 `matrix.md` 审视平衡。
- **原子漂移**：随着时间推移，原子粒度可能变粗（"懒得拆"）→ 可重组性下降 → 初稿生成退化。每季度抽查 5 个原子检查粒度。
- **维护债务**：连续 2 周不更新，系统熵增加速。每周 20 分钟是维持流动性的最低门槛。
- **标签膨胀**：自由创建标签导致检索失效。标签词汇必须受控，新增标签需在 `README.md` 中登记。

---

## 许可

MIT — 这是你的系统，自由使用和修改。

---

*"知识支撑能力，能力推动产出，产出倒逼知识和能力升级。"*
