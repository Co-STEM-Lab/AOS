# Papers

> **个人论文仓库。** 每篇论文一个目录，自包含数据、脚本、草稿、图表。

```
papers/
├── _template/              # 📋 新论文模板
├── _active/                # 🔄 进行中
│   ├── carbide-pearlite-seg/
│   ├── ferrite-grain/
│   ├── ferrite-pearlite-seg/
│   └── network-carbide-spacing/
├── 2018-MnO2-graphene/     # ✅ 已发表
├── 2022-exit-wave/
├── 2024-STEM-multislice/
├── 2025-SiC-fibers/
├── 2025-T1-AlCuLiMg/
├── 2025-topological-tellurium/
└── 2026-theta-AlCu/
```

---

## 快速命令

```bash
source venv/bin/activate

# Markdown 草稿 → LaTeX 论文（投稿用）
python scripts/render.py draft.md --latex -o paper.tex

# Markdown → HTML 报告（展示/汇报用）
python scripts/render.py draft.md --html -o report.html

# 构建个人网站
python website/build.py                     # 全站
python website/build.py --serve             # 构建 + 预览
cd website/public && python -m http.server 8000
```

---

## 每篇论文的结构

```
papers/_active/my-new-paper/
├── index.md                 # 论文元数据（YAML front-matter）
├── data/                    # 原始数据、中间结果
├── scripts/                 # 分析/绘图脚本
├── drafts/                  # 草稿版本（v1.md, v2.md...）
│   └── report-*.html        # aggregate 生成的报告
├── figures/                 # 论文用图（PNG/SVG/PDF）
└── notes/                   # 研究笔记、文献笔记
```

**已发表论文**同样结构，`index.md` 包含完整的出版物信息（标题/作者/DOI/期刊等）。

---

## 新建一篇论文

```bash
# 初始化目录
mkdir -p papers/_active/my-new-paper/{data,scripts,drafts,figures,notes}
cp papers/_template/index.md papers/_active/my-new-paper/
# 编辑 index.md 填写标题、领域、问题
```

---

## 写论文流程

```
研究笔记 → 草稿 → render.py → LaTeX/HTML → 投稿
```

1. 在 `notes/` 中记录想法、文献要点、实验结果
2. 在 `scripts/` 中写分析脚本，结果输出到 `data/`
3. 在 `drafts/` 中写 Markdown 草稿（参考 `skills/writing.md` 格式规范）
4. 用 `scripts/render.py` 转为 LaTeX 或 HTML
5. 投稿后更新 `index.md`，论文移到 `papers/YYYY-name/`

### 渲染命令

```bash
# 生成 LaTeX（Elsevier CAS 单栏模板）
python scripts/render.py drafts/v2-draft.md --latex -o paper.tex

# 生成 HTML 报告
python scripts/render.py drafts/v2-draft.md --html -o report.html
```

---

## 初始化

```bash
bash setup.sh                    # 安装依赖
python website/build.py          # 构建网站
```

---

## 目录说明

| 目录 | 内容 |
|------|------|
| `papers/` | 全部论文，按 `_active/`（进行中）和 `YYYY-name/`（已发表）组织 |
| `skills/` | LLM 协作技能（给 Claude Code / Codex 用） |
| `templates/` | 论文模板、LaTeX 类文件、CSS |
| `scripts/` | `render.py` — Markdown→LaTeX/HTML 渲染引擎 |
| `website/` | 个人学术网站生成器（中英文双语） |

网站从 `papers/` 自动读取论文列表和进行中项目，无需手动配置。

---

## LLM 技能

`skills/` 目录下的技能文件给 Claude Code / Codex 使用，自动加载对应能力：

| 技能 | 用途 | 触发词 |
|------|------|--------|
| `skills/writing.md` | 学术写作规范（结构/图片/公式/表格/引用） | "写论文" / "排版" / "渲染" |
| `skills/figure.md` | 学术图片规范（字体/panel/分辨率/配色） | "插图" / "图片" / "figure" |
| `skills/research.md` | 研究方法论（设计/假设/统计/可复现） | "实验设计" / "研究方法" |
| `skills/survey.md` | 文献调研与综述方法论 | "文献调研" / "综述" / "survey" |

新建 `skills/xxx.md` 即可添加技能，文件头部声明 name + description + 触发词。

---

## 设计原则

1. **论文自包含** — 打开一个目录就能找到该论文的全部材料
2. **纯文本优先** — Markdown + YAML + Git，零平台锁定
3. **渐进式渲染** — Markdown → HTML（汇报）/ LaTeX（投稿），同一源文件两种输出
4. **最小依赖** — 只需 Python + PyYAML，网站可选 Jinja2 + Markdown

