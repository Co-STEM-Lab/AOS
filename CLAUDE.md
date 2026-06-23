# AOS — Academic Operating System

个人学术管理框架。知识库 + 能力库 + 产出矩阵融合成一个可迭代的活系统。

## 会话心跳（每次对话自动执行）

对话开始时：
1. 回想本项目的不变式（见下方"关键不变式"）
2. 如果用户提到 AOS 文件路径或要修改 AOS，先运行 `python scripts/check_invariants.py --json` 确认基线
3. 任何 AOS 文件修改完成后，主动建议运行不变式检查

## AI Skills（`.claude/skills/`）

本项目提供三个 AI 协作技能：

| Skill | 文件 | 用途 | 触发词 |
|-------|------|------|--------|
| `aos-guardian` | `.claude/skills/aos-guardian.md` | 系统守护——不变式巡检 + 新鲜度漂移 + 修复提案 | "检查 AOS" / "守护" / "维护" |
| `aos-operations` | `.claude/skills/aos-operations.md` | 操作引导——建原子/建项目/改词汇表/出初稿时自动检查 | 任何 AOS 文件修改操作时自动启用 |
| `qian-skill` | `.claude/skills/qian-skill/SKILL.md` | 钱学森系统科学方法论——复杂工程诊断 + 总体设计 + 涌现检查 | 多模块/跨服务/重构/性能排查时自动启用 |
| `run-aos` | `.claude/skills/run-aos/SKILL.md` | 构建、运行、烟雾测试 AOS 全部 CLI 入口 | "run AOS" / "test AOS" / "verify AOS" |

## 核心脚本

```bash
python scripts/aggregate.py  # 聚合原子生成初稿
python scripts/check_invariants.py  # 不变式校验引擎
python scripts/check_status.py  # 系统健康度 + 新鲜度
python scripts/install-hooks.sh  # 安装 pre-commit hook
python scripts/scan.py  # 统一扫描入口
python scripts/smoke.py  # 全量烟雾测试（= run-aos driver）
```

## 目录约定

```
CLAUDE.md                       # 本文件（每次对话自动加载）
.claude/skills/                 # AI 协作技能
.claude/rules/                  # AI 硬约束

competencies/skill-tree.md      # 人的学术能力库（不是 AI skill）
knowledge/atoms/                # 产出原子（最小可重组知识单元）
knowledge/atoms/scripts/        # 计算原子的可复用脚本
knowledge/controlled-vocabulary.yml  # 受控标签词汇表（唯一真相源）
knowledge/maintenance-log.md    # 维护审计日志
matrix.md                       # 研究领域 × 问题矩阵
projects/                       # 项目管线（active/completed/ideas）
templates/                      # 标准化模板
data/                           # 示例/测试数据
```

## 关键不变式

1. **原子独立可引用** — 删除项目不丢失原子
2. **证据前置** — 技能评级必须有证据
3. **矩阵封闭** — 每个项目落在唯一格子，格子引用有效
4. **标签一致** — 受控词汇表外不得创建新标签
5. **人不可替代** — 脚本聚合，人决策
6. **脚本自包含** — compute 脚本无隐式依赖

AI 权限：
- ✅ 可自动修：空白 project → "uncategorized"、空白 created → 当天日期、YAML 格式错误、从 import 推断缺失的 script_deps、标记死链
- ⚠️ 需人确认：修改标签、改项目状态、改技能评级、创建/归档文件
- ❌ 禁止：删除文件、改原子核心断言、改词汇表、改人的技能自评
