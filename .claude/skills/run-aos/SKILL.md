---
name: run-aos
description: Build, run, and smoke-test the AOS academic homepage static site. Use when asked to start AOS, build the website, run the paper rendering pipeline, or verify the built site.
---

AOS（Academic Organization System）是一个静态网站生成器，从 `papers/`、`notes/` 等目录的 Markdown 源文件构建个人学术主页。驱动方式：运行 `smoke.sh` 一键构建+验证，或手动构建后用 `curl` 检查输出。

所有路径相对于仓库根目录。

## Prerequisites

```bash
# Python 3.10+ with venv
python3 --version

# 依赖已通过 venv 安装
source venv/bin/activate
pip install -r requirements.txt
```

## Build

```bash
source venv/bin/activate
python website/build.py
```

输出到 `website/public/`。同时构建中文 (`/`) 和英文 (`/en/`) 两个版本。

可选参数：
- `--serve` — 构建后启动本地预览服务器
- `--lang en` — 仅构建英文版

## Run (agent path)

一键构建 + 健康检查（推荐）：

```bash
bash .claude/skills/run-aos/smoke.sh
```

这会依次执行：
1. 构建网站（`python website/build.py`）
2. 验证所有关键静态文件存在
3. 启动本地 HTTP 服务器
4. 用 `curl` 检查每个页面返回 HTTP 200
5. 关闭服务器

参数：
- `--no-serve` — 跳过 HTTP 检查，仅验证文件存在性
- `--serve` — 构建后启动服务器并保持前台运行

### 手动操作

```bash
# 构建
source venv/bin/activate
python website/build.py

# 本地预览
cd website/public && python -m http.server 8000
# → http://localhost:8000
```

预览端口通过 `PORT` 环境变量覆盖（默认 8765）：

```bash
PORT=8080 bash .claude/skills/run-aos/smoke.sh
```

### 验证输出

用 `curl` 检查关键页面：

```bash
curl -s http://localhost:8000/ | grep '<title>'
# → <title>陈桂森 · 陈桂森 · 学术主页</title>

curl -s http://localhost:8000/notes/index.html | grep '<title>'
# → <title>笔记 · 陈桂森 · 学术主页</title>

curl -s http://localhost:8000/notes/ebsd-introduction/content.html | grep -oP '(?<=<p>)[^<]+' | head -1
# → 电子背散射衍射（Electron Backscatter Diffraction，EBSD）是一种基于...
```

## 论文渲染

从 Markdown 草稿渲染为 LaTeX 或 HTML：

```bash
source venv/bin/activate

# Markdown → LaTeX（投稿用）
python scripts/render.py papers/_active/my-paper/drafts/v1.md --latex -o paper.tex

# Markdown → HTML（汇报用）
python scripts/render.py papers/_active/my-paper/drafts/v1.md --html -o report.html
```

## Test

项目无自动化测试套件。验证方式为运行 `smoke.sh` 确认构建成功。

## Gotchas

- **双语言构建：** `build.py` 同时构建中文和英文两个版本，分别位于 `/` 和 `/en/`。两次构建逻辑相同，耗时约 2×。
- **图片目录：** 笔记图片目录必须列在 `build.py` 的 `_copy_note_assets` 函数中（`TEM_CBED_images`、`TEM_images`、`EBSD_images`、`sftd_images`），否则不会被复制到输出。
- **Port 8765：** `smoke.sh` 默认使用 8765 端口而非 8000，避免与常见服务冲突。
- **build.py 使用 `cd`：** 脚本依赖 `Path.cwd()`，确保从仓库根目录运行。

## Troubleshooting

- **`ModuleNotFoundError: No module named 'yaml'`**：未激活 venv。运行 `source venv/bin/activate`。
- **`jinja2` 相关错误**：`pip install -r requirements.txt` 安装缺失的依赖。
- **构建后页面无内容**：检查 `website/public` 下是否有 `index.html`。文件为空说明构建过程出错，查看构建日志。
- **smoke.sh 服务器未启动**：端口被占用。设置 `PORT=0` 让系统分配空闲端口，或 `PORT=XXXX` 指定端口。
