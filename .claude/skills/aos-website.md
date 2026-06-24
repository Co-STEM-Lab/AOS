---
name: aos-website
description: >-
  AOS 个人学术网站维护——构建、预览、配置修改、部署。
  Use this skill whenever the user wants to build/update the website, change
  personal info, modify templates/styles, preview locally, deploy, or says
  any of: "建站", "更新网站", "改网站", "部署", "website", "build site",
  "build website", "preview", "publish", "网页".
---

# AOS Website Skill — 个人学术网站维护

## 能力

本 Skill 覆盖个人学术网站的全部维护操作，从构建到部署。

---

## 操作 1：构建网站

### 触发
- 用户说 "建站" / "构建" / "build" / "更新网站"
- 用户修改了 `config.yml` / `knowledge/atoms/` / `projects/` 等数据源后

### 流程

```bash
# 标准构建（全量）
python website/build.py

# 只构建一种语言（更快）
python website/build.py --lang=zh
python website/build.py --lang=en

# 构建 + 本地预览
python website/build.py --serve
```

### 后检
1. 检查 exit code（0=成功）
2. 检查 `website/public/` 下生成了 `index.html`
3. 提醒用户预览: `cd website/public && python -m http.server 8000`
4. 建议运行 `python scripts/check_invariants.py` 确保 AOS 系统健康

---

## 操作 2：修改个人信息

### 触发
- 用户说 "改名字" / "更新简介" / "换头像" / "改邮箱" / "update profile"

### 流程
1. 读取 `website/config.yml`
2. 定位到对应字段，确认修改内容
3. 修改后运行 `python website/build.py` 重建
4. 提醒预览确认

### 常用字段

| 字段 | 中文 | 英文 |
|------|------|------|
| `author.name_zh/en` | 姓名 | Name |
| `author.title_zh/en` | 头衔 | Title |
| `author.affiliation_zh/en` | 机构 | Affiliation |
| `author.bio_zh/en` | 简介 | Bio |
| `author.email` | 邮箱 | Email |
| `author.avatar` | 头像文件名（放 static/images/） | Avatar |
| `social.github` | GitHub 用户名 | — |
| `social.google_scholar` | Google Scholar ID | — |
| `social.twitter` | Twitter 用户名 | — |
| `social.orcid` | ORCID ID | — |

---

## 操作 3：修改主题样式

### 触发
- 用户说 "改颜色" / "换主题" / "调样式" / "change theme"

### 可修改项

**`config.yml` theme 区**：
```yaml
theme:
  primary_color: "#1a365d"    # 主色（导航/标题）
  accent_color: "#c53030"     # 强调色（链接 hover/标签）
```

**`website/static/css/style.css`**：全部样式变量，包括字体、间距、卡片样式、响应式断点。

### 注意事项
- 修改 CSS 后必须重建: `python website/build.py`
- 建议改完后在手机和桌面都预览一下

---

## 操作 4：本地预览

### 触发
- 用户说 "预览" / "看看效果" / "preview"

### 流程
```bash
cd website/public && python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

或带构建一步到位：
```bash
python website/build.py --serve
```

---

## 操作 5：部署到 GitHub Pages

### 触发
- 用户说 "部署" / "上线" / "发布" / "deploy" / "publish"

### 前置条件
- GitHub 仓库已创建
- 本地有 git 权限

### 流程

```bash
# 1. 构建最新版本
python website/build.py

# 2. 部署到 gh-pages 分支
# 方式 A：使用 gh-pages 工具
# npm install -g gh-pages
# gh-pages -d website/public

# 方式 B：手动推送
cd website/public
git init
git checkout -b gh-pages
git add -A
git commit -m "Deploy website"
git remote add origin https://github.com/<username>/<repo>.git
git push -f origin gh-pages

# 方式 C：GitHub Actions 自动部署（推荐）
```

### GitHub Actions 自动部署（推荐）

在 `.github/workflows/deploy-website.yml` 创建：

```yaml
name: Deploy AOS Website
on:
  push:
    branches: [main]
    paths:
      - 'website/**'
      - 'knowledge/**'
      - 'projects/**'
      - 'matrix.md'
      - 'competencies/**'
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pyyaml jinja2 markdown
      - run: python website/build.py
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: website/public
```

### 部署后检查
- 确认 GitHub Pages 已启用（Settings → Pages → Source: gh-pages）
- 访问 `https://<username>.github.io/<repo>/` 确认生效
- 中英文切换正常

---

## 操作 6：添加/修改页面

### 触发
- 用户说 "加页面" / "加博客" / "改布局" / "add page"

### 流程
1. 在 `website/templates/` 创建新的 Jinja2 模板（继承 `base.html`）
2. 在 `website/build.py` 的 `build_site()` 函数中注册新页面
3. 在 `config.yml` 的 `nav` 中添加导航项
4. 运行 `python website/build.py` 构建
5. 预览确认

### 模板编写示例
```jinja2
{% extends "base.html" %}
{% block title %}页面标题 · {{ config.site["title_" + lang] }}{% endblock %}
{% block content %}
<section class="section page-header">
  <h1>{{ t.mypage.title }}</h1>
</section>
{% endblock %}
```

### 翻译注册
在 `build.py` 的 `T` 翻译字典中，为每种语言添加 `mypage` 下的 key。

---

## 通用纪律

1. **改前读** — 修改 config.yml / 模板 / CSS 前先读取当前内容
2. **改后建** — 任何修改后必须运行 `python website/build.py`
3. **改后验** — 预览确认效果，检查中英文版本
4. **不变式** — 网站修改不影响 AOS 系统不变式（运行 `check_invariants.py` 确认）
5. **AI 权限** — 同 aos-guardian 规则：可提议，不可擅自改 config.yml 中的人名/头衔等身份信息，需用户确认后执行
