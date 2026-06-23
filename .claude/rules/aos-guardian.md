# AOS Guardian Rules

> 这些规则是硬约束。每次 AI 启动时必须遵守，违反任何一条视为系统错误。

## 权限边界（不变式⑤的具体化）

### 你可以做的事
- 读取 AOS 任何文件（全部 Markdown/YAML/Python）
- 运行 `python scripts/check_invariants.py` / `check_status.py` / `aggregate.py`
- **提议**修改：在对话中输出建议，标注"建议修改 X 为 Y"，等待人确认
- 搜索、统计、格式化输出检查结果

### 你必须确认后才能做的事
- 修改任何 `knowledge/atoms/` 下的原子文件
- 修改 `skills/skill-tree.md` 中的评级或证据
- 修改 `matrix.md` 的矩阵内容
- 修改 `projects/` 下的项目卡片
- 创建新原子 / 新项目
- 运行 `python scripts/aggregate.py --execute`（触发脚本执行）

### 你绝对不能做的事
- 删除任何原子文件或项目目录
- 下调配对人的技能自评
- 修改 `knowledge/controlled-vocabulary.yml`（词汇表变更需人主动发起）
- 未经确认执行任何会改变仓库内容的操作

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
# 人类可读
python scripts/check_invariants.py

# 机器可读（CI / pre-commit）
python scripts/check_invariants.py --json

# 状态面板
python scripts/check_status.py
```

## 对话中的标准动作

当用户说"检查一下 AOS"或类似指令时：
1. 运行 `python scripts/check_invariants.py`
2. 运行 `python scripts/check_status.py`
3. 将结果结构化呈现（不复制粘贴原始输出）
4. 对每个 SOFT 警告，给出 1 句话修复建议
5. 如果有 HARD 违规，优先处理
6. 将检查结果追加到 `knowledge/maintenance-log.md`
