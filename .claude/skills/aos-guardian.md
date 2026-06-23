---
name: aos-guardian
description: AOS 系统守护——自主巡检不变式、检测漂移、生成修复建议、写维护日志。对应 Loop Engineering 的 Outer Loop 编排层。
trigger:
  - 用户说 "检查 AOS" / "check AOS" / "守护" / "guardian"
  - 用户说 "系统健康" / "维护" / "maintenance"
  - 每个大改动的 Step 5 涌现检查阶段
---

# AOS Guardian Skill

## 能力

本 Skill 赋予 AI 四种巡检模式，对应 Loop Engineering 的四类 Inner Loop：

### Loop 1: 不变式硬校验（每次 commit / 用户触发）
```
触发: pre-commit hook 或 python scripts/check_invariants.py
检查: 6 条不变式全部
输出: HARD 违规（阻断）/ SOFT 警告（记录）
```

### Loop 2: 新鲜度巡检（每周建议运行）
```
触发: python scripts/check_status.py
检查: 技能过期 / 项目停滞 / 原子草稿陈旧 / 矩阵覆盖率
输出: 新鲜度评分 + 处置建议
```

### Loop 3: 交叉引用审计（矩阵联动检查）
```
触发: 用户要求或 Loop 1/2 发现异常后
检查: 矩阵格子 ↔ 项目双向引用完整性
     原子 ↔ 项目归属一致性
     技能证据 ↔ 项目存在性
输出: 断裂引用清单 + 修复路径
```

### Loop 4: 计算原子可复现性测试（可选，需 venv）
```
触发: 用户要求
检查: 每个 compute 原子的脚本能否在 venv 中独立运行
输出: 通过/失败 + 失败原因
```

## 工作流

### 标准巡检（用户说"检查 AOS"）

```
Step 1: 运行 check_invariants.py --json
        ↓
    有 HARD? → 立刻报告并列出修复步骤（最优先）
        ↓ 无
Step 2: 运行 check_status.py
        ↓
Step 3: 解析新鲜度数据
        - 技能: 哪些超过 180 天未 review?
        - 项目: 哪些 active 超过 90 天无日志?
        - 原子: 哪些 draft 超过 60 天?
        ↓
Step 4: 生成维护报告（人类可读）
        - 标题: "AOS 维护报告 — YYYY-MM-DD"
        - 分区: 紧急 / 建议 / 良好
        ↓
Step 5: 将报告追加到 knowledge/maintenance-log.md
        ↓
Step 6: 询问用户是否处理建议项
```

### 修复流程（用户确认后）

```
Step 1: 用户说"处理 X"
Step 2: 列出具体修改内容（diff 形式）
Step 3: 用户确认 → 执行修改
Step 4: 重新运行 check_invariants.py 验证修复
Step 5: git diff 给用户看最终变更
Step 6: 更新 maintenance-log.md 记录修复
```

## 新鲜度判断函数

对 `check_status.py` 输出的理解：

- **技能过期**（末次 review > 180 天）
  - 建议: 用户自评当前水平，更新日期。如果确实不再使用，降级或保留但注明。
  - AI 不可自行修改评级。

- **项目停滞**（active/writing 但 > 90 天无进度日志）
  - 建议: ① 补日志 ② 改状态为 idea ③ 归档到 completed 并注明中止原因
  - AI 可提议，不可直接改。

- **原子草稿陈旧**（draft 且 > 60 天）
  - 建议: ① 完善为 final ② 合并到其他原子 ③ 删除（需人确认）
  - AI 可提议，不可直接改/删。

- **矩阵覆盖率低**（有项目格子 / 总格子 < 某阈值）
  - 建议: 审视空白格——是战略空白还是自然空白？
  - AI 可分析，战略判断在人。

## 维护日志格式

每次巡检后必须写入 `knowledge/maintenance-log.md`：

```markdown
| 时间 | 触发方式 | HARD | SOFT | 处置 |
|------|---------|------|------|------|
| 2026-06-23 | 用户手动 | 0 | 3 | 处理 2，遗留 1 |
```

每次修复后追加：

```markdown
### 2026-06-23 修复记录
- [已修复] atom-X 标签漂移 → 修正为 #方法组件
- [已修复] proj-Y 更新状态为 writing
- [遗留] skill-Z 缺乏证据 → 等待用户补充
```

## 禁止模式

- ❌ 在未经用户确认的情况下修改任何 .md 文件
- ❌ 对技能评级做主观判断（"这个应该是 L3"——不行，只有人知道）
- ❌ 删除未过期的原子或项目
- ❌ 修改 controlled-vocabulary.yml
- ❌ 在 1 次对话中做超过 5 项修改（批量修改风险高）
