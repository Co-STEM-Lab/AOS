---
name: aos-operations
description: >-
  AOS 操作引导——在创建或修改原子、项目、词汇表、技能评级，或生成初稿时，
  自动执行预检、引导和后检。覆盖 AOS 全部 5 类高频操作。
  Use this skill whenever the user is about to or has just: created/edited
  files under knowledge/atoms/, created/edited a project under projects/,
  modified knowledge/controlled-vocabulary.yml, run scripts/aggregate.py,
  edited competencies/skill-tree.md, or any general modification to the
  AOS repository structure. Also when the user says any of: "建原子",
  "建项目", "立项", "出初稿", "生成初稿", "改词汇表", "更新技能", "评技能".
---

# AOS Operations Skill

本 Skill 覆盖 AOS 全部高频操作。每次相关操作触发时，自动执行预检、引导和后检。

---

## 操作 1：创建 / 编辑原子

### 触发
- 用户在 `knowledge/atoms/` 下新建 `.md` 文件
- 用户说 "建原子" / "写原子"

### 预检（修改前）
1. 读 `knowledge/controlled-vocabulary.yml`，确认可用标签和类型
2. 读 `templates/atom-template.md`，对照模板
3. 如果用户未提供项目 id → 询问关联哪个项目（或填 "uncategorized"）

### 引导（修改时）
自动补全（可无确认执行）：
- `created` 字段为空 → 填入当天日期
- `project` 字段为空 → 填入 "uncategorized"
- `status` 字段为空 → 填入 "draft"
- `id` 前缀与 `type` 不一致 → 自动修正

需提醒：
- 至少 1 个结构标签（`#引言缺口` / `#方法组件` / `#结果讨论`）+ 1 个领域标签
- compute 类型原子必须指定 `script` 文件名

### 后检（修改后）
```bash
python scripts/check_invariants.py --json
```
- 有 HARD 违规 → 自动修复可修的项，报告不可修的项
- 提醒用户将此原子关联到项目卡片的 "关联原子" 列表

---

## 操作 2：创建 / 修改项目

### 触发
- 用户在 `projects/` 下新建目录和 `index.md`
- 用户说 "建项目" / "立项"

### 预检
1. 读 `matrix.md`，确认用户指定的领域和问题已在矩阵中
2. 如果领域或问题是新的 → 提醒先更新 `matrix.md` 增加行列
3. 读 `templates/project-template.md`

### 引导
自动补全：
- `created` / `updated` 为空 → 填入当天日期

需提醒：
- `domain` 和 `problem` 必须精确匹配 `matrix.md` 中的行列名
- `status` 从 `idea` 开始
- 项目目录命名为项目 id（如 `proj-dynamic-X`）

### 后检
1. 运行 `python scripts/check_invariants.py --json` 确认矩阵封闭
2. 提醒在 `matrix.md` 对应格子中添加 `[proj-id](projects/active/proj-id/) 💡`
3. 提醒在项目卡片中填写关联原子

---

## 操作 3：修改受控词汇表

### 触发
- 用户编辑 `knowledge/controlled-vocabulary.yml`
- 用户说 "加标签" / "改词汇表"

### 预检
无。（词汇表是源头，修改它之前没有更上层检查）

### 引导
- 警告：词汇表是受控的。修改后所有现有原子必须重新通过校验。
- 新增标签 → 建议立即运行 `check_invariants.py` 确认无冲突
- 删除标签 → 警告会导致使用该标签的原子违规

### 后检（修改后必须）
```bash
python scripts/check_invariants.py --json
```
报告所有新产生的违规，逐条提示修复路径。

---

## 操作 4：聚合生成初稿

### 触发
- 用户运行 `scripts/aggregate.py` 或说 "出初稿" / "生成初稿"

### 预检
1. 确认项目存在且有关联原子
2. 如果项目有 compute 原子 → 建议加 `--execute` 运行脚本
3. 检查 `script_deps` 是否已安装

### 引导（生成后）
审查初稿质量：
- [ ] Introduction 段是否至少有一个缺口原子？
- [ ] Method 段是否有方法原子支撑？
- [ ] Results 段是否有结果原子？
- [ ] 是否有孤立原子（未被任何段落使用）？
- [ ] compute 原子输出是否已成功嵌入？

如果任何一项不合格 → 提示用户补充对应类型的原子。

### 后检
```bash
python scripts/check_invariants.py
```

---

## 操作 5：更新技能评级

### 触发
- 用户编辑 `competencies/skill-tree.md`
- 用户说 "更新技能" / "评技能"

### 预检
1. 读当前技能树，识别哪些技能评级变更了
2. 如果 L3/L4 → 确认是否新增了证据

### 引导
- 升级到 L3/L4 → 检查证据列是否非空。如果为空 → 警告不变式②。
- 降级 → 不需证据，但提醒更新 `last_reviewed` 日期
- 技能项增减 → 提醒更新 `controlled-vocabulary.yml` 中的 `skill_categories`（如需要）

### 后检
```bash
python scripts/check_invariants.py --json
```
特别关注 `证据前置` 违规。

---

## 通用纪律（所有操作）

1. **先读后写** — 改任何 AOS 文件前先读当前内容
2. **改完自查** — 每个修改操作后运行 `check_invariants.py`
3. **日志留痕** — 非平凡的修改追加到 `knowledge/maintenance-log.md`
4. **批量上限** — 同一次对话中 AOS 文件修改不超过 5 处（防批量错误）
5. **自动修>提议修>不动** — 优先级：能安全自动修的就自动修，需要判断的就提议，涉及内容或删除的绝不动
