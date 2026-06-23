# Industry Benchmark × Qian-Xuesen-Systems-Science Skill

把 14 个主流 AI-coding / agent benchmark 映射到本 Skill 的预期行为、评估方法、可行性。

## 关键判断维度

对每个 benchmark 看四件事：

1. **任务复杂度**：单函数 / 多文件 / 多模块 / 跨系统
2. **是否涉及"系统性思考"**：耦合、不变式、涌现、总体设计
3. **预期 skill 行为**：HELP（强力辅助）/ NEUTRAL（不动作）/ SKIP（应主动退出，不污染上下文）
4. **本会话可执行性**：能否在 skill-creator 流程内真实运行；不能则用"代表性样本"代理

---

## 完整映射表

| Benchmark | 任务类型 | 复杂度 | 预期 Skill 行为 | 评估方法 | 本会话可执行? |
|---|---|---|---|---|---|
| **SWE-bench (full)** | 真实 GitHub Issue 端到端修复 | 高（多文件） | **HELP**（强诊断 + 总体设计 + 综合集成调试） | 真跑：每个实例需 Docker + repo checkout + test verification | ❌ 需要外部 harness |
| **SWE-bench Lite** | SWE-bench 子集（300 例） | 中-高 | **HELP**（同上，但部分例可能简单） | 同上，规模小一些 | ⚠️ 子集子集（5-10 例）可勉强真跑，全跑不行 |
| **SWE-bench Verified** | 高质量 SWE-bench 子集（500 例） | 高 | **HELP** | 同 SWE-bench | ❌ |
| **HumanEval** | 单函数代码补全（164 例） | **极低** | **SKIP**（第一步诊断应判简单系统并退出） | 真跑：164 例可全跑，验证 (a) skill 没触发 (b) pass@1 不下降 (c) token 消耗不增加 | ✅ 完全可执行 |
| **MBPP** | Python 单函数问题（974 例） | **极低** | **SKIP** | 真跑：可全跑或采样 100 例 | ✅ 可执行 |
| **Aider (polyglot)** | 多语言代码编辑 benchmark（225 例） | 中 | **混合**：复杂例 HELP / 简单例 SKIP | 真跑：Aider 的 leaderboard 评测脚本可直接调用 | ⚠️ 部分可执行（需 Aider 环境） |
| **OpenHands (原 OpenDevin)** | 多步骤端到端软件开发 | 高 | **HELP**（典型 OCGS 场景） | 真跑：OpenHands 的评估套件，含 SWE-bench、WebArena 等 | ❌ 需要其整套环境 |
| **AppWorld** | 复杂 API 交互任务 | 中-高 | **NEUTRAL**（工具使用为主，系统思考帮助有限） | 真跑：需 AppWorld 沙箱 | ❌ |
| **WebArena** | 网页交互任务 | 中 | **NEUTRAL**/**SKIP**（UI 交互非系统设计） | 真跑：需浏览器沙箱 | ❌ |
| **OSWorld** | 操作系统级任务 | 中-高 | **NEUTRAL**（OS 操作非软件设计） | 真跑：需 VM | ❌ |
| **AgentBench** | 多维度 agent 能力 | 混合 | **混合**（看子任务） | 真跑：需子任务环境 | ❌ |
| **ToolBench** | API 调用正确性 | 低-中 | **SKIP**（工具调用非系统设计） | 真跑 | ❌ |
| **Inspect (UK AISI)** | 安全评估 | 低 | **SKIP**（与系统科学无关） | 不评估 | — |
| **GAIA** | 多模态推理问答 | 中 | **NEUTRAL**（推理而非编码） | 真跑 | ❌ |
| **MMLU / GSM8K** | 学术知识 / 数学 | 极低 | **SKIP**（与编码无关） | 不评估 | — |

---

## 本会话现实可执行的评估子集

考虑到 skill-creator 流程的资源边界，**本会话内**做以下三档评估：

### Tier A：直接可真跑（验证负例 / 不过度触发）

- **HumanEval（采样 20 例）**：验证 skill 在简单任务上**主动退出**、不污染上下文、不增加 token / 延迟
- **MBPP（采样 20 例）**：同上

**评测指标**：
- `trigger_rate`（应 ≤ 5%——只允许少数边界例触发然后退出）
- `pass@1`（with vs without skill；with 不应低于 baseline）
- `avg_tokens`（with 不应超 baseline 的 1.2 倍）
- `avg_latency`（同上）

### Tier B：代表性样本（覆盖 SWE-bench / Aider / OpenHands 等高复杂度场景）

用**精心构造的 6 个测试用例**模拟真实 benchmark 的任务分布：

1. **SWE-style 多文件 bug 修复**（含真实代码上下文 + issue 文本）
2. **Aider-style 跨语言重构**（一段需要在 Python + Rust + TS 同步改动的接口变更）
3. **OpenHands-style 端到端任务**（"实现登录限流 + 监控"完整链路）
4. **OCGS 仪器场景**（保留原 TOF-MS 用例）
5. **跨服务性能问题**（保留原 P99 飙升用例）
6. **跨子系统调试**（保留原分布式训练 hang 用例）

**评测方式**：with-skill / without-skill 两版 subagent 输出，定性 review（人工 + AI 评分），定量打 6-8 个客观 assertion（"是否做了诊断"、"是否列了 ≥3 个假设"、"是否提到反馈回路"等）。

### Tier C：建议但不在本会话执行（需要外部 harness）

- **SWE-bench Lite（5-10 例真跑）**：需要 Docker、SWE-bench 评测脚本、repo 准备
- **Aider polyglot leaderboard**：需 Aider CLI 集成
- **OpenHands suite**：需其评估容器

为这一档我**会写好运行说明文档**，但实际跑放到后续会话（你能给出 Docker 或专门评测机的环境时再做）。

---

## Tier A 评估的预期结果

对 HumanEval / MBPP，本 Skill 应表现为**几乎不可见**：

- 加载 skill 描述 ≈ 几百 tokens 一次性开销
- 但因任务都是单函数，**第一步诊断会立即判为简单系统并退出**，不会进入后面四步
- 因此 pass@1 应与 baseline 持平（甚至略好，因为有更明确的"不要过度设计"的引导）

如果观察到 trigger_rate > 5% 或 pass@1 下降 > 2%，说明 skill 描述写得过于"宽口径"，需要收紧 description 中的 "do NOT use" 子句。

## Tier B 评估的预期结果

对真正的复杂任务，本 Skill 应表现为**显著的结构化思考差异**：

- 诊断步骤是否被执行（是 / 否，objective）
- 是否列出耦合矩阵 / 子系统清单（objective）
- 是否在调试任务上**列假设再验证**而不是直接 grep 改代码（objective）
- 是否警告反馈回路 / 涌现风险（objective）
- 是否回答更"对"（subjective 人工评分）
- token / 延迟是否在可接受范围（objective）

---

## Tier C 真跑 SWE-bench Lite 的运行说明（备查）

```bash
# 准备：拉取 SWE-bench Lite 数据集（300 例）
git clone https://github.com/princeton-nlp/SWE-bench
cd SWE-bench && pip install -e .

# 准备：Docker 环境（每个实例都有特定 repo + commit + test）
# SWE-bench 提供预构建镜像：
# ghcr.io/swe-bench/sweb.eval.x86_64.<instance_id>:latest

# 评估流程（伪代码）：
for instance in swe-bench-lite-sample:
    # 1. checkout repo at base_commit
    # 2. apply skill: 让 claude with-skill 读 problem_statement + 代码，产出 patch
    # 3. apply patch
    # 4. run test_patch；验证 PASS_TO_PASS + FAIL_TO_PASS
    # 5. 记录 pass / fail / time / tokens

# 对照组 without-skill 同上
```

需要的资源：Docker、~20 GB 磁盘（实例镜像）、能调用 claude CLI 的脚本环境。**这是真正 industry-grade 的评估，但不适合在 skill-creator 流程里跑。**

---

## 一句话总结

- **真跑 HumanEval/MBPP**：验证不过度触发（必须做）
- **代表性样本 SWE/Aider/OpenHands 模拟**：验证有效辅助（必须做）
- **真跑 SWE-bench Lite**：留给下一阶段，需要外部 harness（必要时再约一次会话）
