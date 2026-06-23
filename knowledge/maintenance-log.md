# AOS 维护日志

> **用途**：记录每次系统巡检和修复操作。不可篡改的审计轨迹。
>
> **写入者**：AOS Guardian（pre-commit hook / check_invariants.py / AI 辅助巡检）
>
> **读取者**：人（回顾维护历史）/ AI（断点续跑）

---

## 巡检记录

| 时间 | 触发方式 | 🔴 HARD | 🟡 SOFT | 处置 |
|------|---------|---------|---------|------|
| 2026-06-23 | 初始化 | 0 | — | 系统建立，基线检查通过 |

---

## 修复记录

### 2026-06-23 初始基线
- [系统] AOS Guardian 框架初始化完成
  - `scripts/check_invariants.py` — 不变式校验引擎
  - `scripts/install-hooks.sh` — pre-commit 硬守卫
  - `.claude/rules/aos-guardian.md` — AI 权限边界
  - `.claude/skills/aos-guardian.md` — 巡检 Workflow
  - `knowledge/controlled-vocabulary.yml` — 受控词汇表

---

## 巡检协议

### 定期触发
- **每周**：用户运行 `python scripts/check_status.py` 或对 AI 说"检查 AOS"
- **每季度**：AI 辅助深度巡检（技能评级 + 矩阵覆盖率 + 原子库存质量）

### 事件触发
- **git commit**：pre-commit hook 自动运行 `check_invariants.py`
- **新建原子后**：建议运行不变式检查
- **项目状态变更后**：建议更新矩阵格子

### 紧急情况
- **跳过 pre-commit**：`SKIP_AOS_GUARDIAN=1 git commit -m "..."`
- **跳过原因必须在下次巡检中说明**
