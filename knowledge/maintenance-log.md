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
| 2026-06-24 20:12 | scan --log | 0 | 3 | 待处理 |
| 2026-06-23 15:21 | scan --log | 0 | 0 | ✅ 无需处置 |
| 2026-06-23 | 初始化 | 0 | — | 系统建立，基线检查通过 |
| 2026-06-23 | 用户手动 (Claude Code) | 0 | 0 | 全部通过，附填充建议 |

---

## 修复记录

### 2026-06-23 第一次巡检报告

**状态**: ✅ 全部通过，无违规

| 分区 | 内容 |
|------|------|
| ✅ **良好** | Guardian 三层架构完备；受控词汇表完整；compute-0001 原子质量达标；4 个核心脚本功能正常 |
| 💡 **建议** | ① 在 `matrix.md` 填入核心领域和问题 ② 在 `skill-tree.md` 填写技能自评 ③ 创建 5-10 个真实原子 ④ 在 `projects/ideas/` 创建第一个项目 |
| ❌ **紧急** | 无 |

### 2026-06-23 初始基线
- [系统] AOS Guardian 框架初始化完成
  - `scripts/check_invariants.py` — 不变式校验引擎
  - `scripts/install-hooks.sh` — pre-commit 硬守卫
  - `.claude/rules/aos-guardian.md` — AI 权限边界
  - `.claude/skills/aos-guardian.md` — 巡检 Workflow
  - `knowledge/controlled-vocabulary.yml` — 受控词汇表

---


### 2026-06-24 20:12 扫描发现
- [SOFT] README.md: README 目录树与实际文件系统不一致
- [SOFT] CLAUDE.md: 脚本 scripts/aos_utils.py 实际存在但 CLAUDE.md 未列出
- [SOFT] CLAUDE.md: 脚本 scripts/test_check_invariants.py 实际存在但 CLAUDE.md 未列出

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
