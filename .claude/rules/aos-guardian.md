# AOS Guardian Rules

> 这些规则是硬约束。每次 AI 启动时必须遵守，违反任何一条视为系统错误。

## 权限边界（不变式⑤的具体化）

### ✅ 你可以自动做的事（无需确认，可逆且安全）
- 读取 AOS 任何文件（全部 Markdown/YAML/Python）
- 运行 `python scripts/check_invariants.py` / `check_status.py` / `aggregate.py`
- 补充空白 `project` 字段为 `"uncategorized"`
- 补充空白 `created` / `updated` 日期字段为当天日期
- 修正 front-matter YAML 格式错误（缩进、引号、缺失字段）
- `id` 前缀与 `type` 不一致 → 自动对齐
- 从脚本的 `import` 语句推断并填充缺失的 `script_deps`
- 将检测到的死链写入 `knowledge/maintenance-log.md`（不修改源文件）
- 搜索、统计、格式化输出检查结果

### ⚠️ 你必须确认后才能做的事
- 修改原子标签（可能改变归属和检索）
- 修改项目 `status` 字段（如 active→completed）
- 修改 `competencies/skill-tree.md` 中的评级或证据
- 修改 `matrix.md` 的矩阵内容（增删行列、修改引用）
- 修改原子正文（核心断言、证据、适用场景）
- 创建新原子 / 新项目 / 新脚本
- 归档或移动项目目录
- 运行 `python scripts/aggregate.py --execute`（触发脚本执行）

### ❌ 你绝对不能做的事
- 删除任何原子文件、项目目录或脚本
- 修改原子核心断言的内容语义
- 下调配对人的技能自评（只有人知道自己的水平）
- 修改 `knowledge/controlled-vocabulary.yml`（词汇表变更需人主动发起）
- 在同一对话中做超过 5 处 AOS 文件修改
- 未经确认执行任何不可逆操作

## 不变式知识

每次编码前，确认这些不变式仍然成立。如果发现违反，必须**先报告**，不要**先修改**。

1. **原子独立可引用** — 原子内容不含对特定项目的硬编码路径
2. **证据前置** — L3/L4 技能必须有证据列
3. **矩阵封闭** — 每个项目在矩阵中；矩阵引用指向存在的项目
4. **标签一致** — 结构标签在 `knowledge/controlled-vocabulary.yml` 中
5. **人不可替代** — 你只提议，人决定
6. **脚本自包含** — compute 原子的脚本无硬编码路径，依赖已声明

## 检查命令

```bash
# 统一扫描
python scripts/scan.py              # 不变式 + 健康面板
python scripts/scan.py --json       # 机器可读

# 单项检查
python scripts/check_invariants.py          # 不变式
python scripts/check_invariants.py --json   # 机器可读
python scripts/check_status.py              # 状态面板
```

## 对话中的标准动作

当用户说"检查 AOS" / "扫描" / scan 或类似指令时：
1. 运行 `python scripts/scan.py`（或 `--json` 获取结构化数据）
2. 将结果结构化呈现（不复制粘贴原始输出）
3. 对每个违规/警告，给出 1 句话修复建议
4. 如果有 HARD 违规，优先处理
5. 将检查结果追加到 `knowledge/maintenance-log.md`
