# 老三论 + 新三论：系统科学的两套理论支柱

钱学森把现代系统科学的方法论根基分为两批：

```
老三论（1940s–60s 奠基）：
  ├─ 系统论（General Systems Theory，Bertalanffy）
  ├─ 控制论（Cybernetics，Wiener）
  └─ 信息论（Information Theory，Shannon）

新三论（1970s–80s 新增）：
  ├─ 耗散结构论（Dissipative Structures，Prigogine）
  ├─ 协同学（Synergetics，Haken）
  └─ 突变论（Catastrophe Theory，Thom）
```

钱学森的工作是把这六者**统合成系统科学的方法论体系**，并应用到工程。对 AI 编码，这六套理论提供了精确的**词汇**和**框架**，让你能 talk about emergence、failure modes、phase transitions 而不流于"感觉"。

下面把每套理论的核心 idea 映射到软件工程，做成可直接套用的清单。

---

## 1. 系统论（General Systems Theory）

**核心 idea**：系统 = 部分 + 关系；整体行为不可由部分单独推出。

**关键概念**：
- 边界（boundary）：什么在系统里、什么是环境
- 层次（hierarchy）：系统的系统的系统
- 目的性（teleology / purposefulness）：系统有目标函数
- 整体性（holism）：整体>部分之和

**软件工程映射**：
- 边界 → 服务边界、模块边界、数据库 schema 边界
- 层次 → 单体 / 进程 / 服务 / 部门 / 公司 / 用户
- 目的性 → SLO、business KPI、product north star
- 整体性 → "我们都达标了为什么 P99 不达标"

**核心问题**：你能写出系统的**目标函数**吗？如果不能，你是在没有方向感地优化。

---

## 2. 控制论（Cybernetics）

**核心 idea**：通过反馈实现目标。**反馈**是控制论的中心概念。

**关键概念**：
- 反馈回路（feedback loop）：负反馈稳定、正反馈放大
- 目标 → 测量 → 比较 → 修正
- 稳定性、可控性、可观性（stability / controllability / observability）
- 黑箱方法（black-box modeling）

**软件工程映射**：

| 控制论 | 软件 |
|---|---|
| 负反馈 | autoscaling、退避重试、限流、PID 控制 |
| 正反馈 | 缓存击穿放大、推荐系统单点偏好放大、failover 风暴 |
| 测量 | metrics、tracing、SLI |
| 比较 | SLO / alert / regression test |
| 修正 | rollback、feature flag、circuit breaker |

**控制论三性**（强烈建议作为软件工程检查清单——本 Skill 的一个核心补充）：

- **可观性（observability）**：在任意时刻能否知道系统在做什么？
  - 检查：logs、metrics、distributed tracing、profiler、event sourcing
  - 反模式：黑盒部署，故障后只能猜
- **可控性（controllability）**：能否在不重启的情况下改变系统行为？
  - 检查：feature flag、kill switch、config hot-reload、graceful drain
  - 反模式：bug 只能等下次发布修
- **稳定性（stability）**：扰动后能否收敛回稳定态？
  - 检查：mean time to recovery、idempotency、retry semantics、queue depth bound
  - 反模式：一次抖动引发雪崩

**这三性应该和不变式一起，作为复杂系统设计的硬约束。**

---

## 3. 信息论（Information Theory）

**核心 idea**：信息有度量（熵）、有传输容量（信道）、有压缩极限。

**关键概念**：
- 信息熵（entropy）：不确定性的度量
- 信道容量（channel capacity）：传输速率上限
- 冗余（redundancy）：用于纠错
- 压缩 vs 准确性的 trade-off

**软件工程映射**：

| 信息论 | 软件 |
|---|---|
| 熵 | 日志的"信息量"（无脑 println 是低熵） |
| 信道容量 | 带宽、QPS、消息队列吞吐上限 |
| 冗余 | replication、erasure coding、checksum |
| 压缩 | protobuf vs JSON、log sampling、metric aggregation |
| 信噪比 | alert quality（"alert fatigue" = 信噪比低） |

**实用启发**：
- 加日志前问：这条日志会增加多少 "排查信息熵"？
- 设计 alert 前问：这个 alert 的"误报熵 / 漏报熵"是多少？
- 选择数据结构前问：要传递多少不可压缩的信息？

---

## 4. 耗散结构论（Dissipative Structures）

**核心 idea**（Prigogine 1977 诺奖）：**远离平衡态、开放系统**可以自发产生有序结构，前提是持续的能量/物质输入。

**关键概念**：
- 远离平衡（far from equilibrium）：不是稳态而是稳定流
- 自组织（self-organization）：无需中央指挥的秩序涌现
- 临界点（critical point）：在某些参数下系统突然组织起来

**软件工程映射**：

| 耗散结构 | 软件 |
|---|---|
| 持续能量输入 | 服务持续运行的进程、CPU 时间、网络流量 |
| 远离平衡的稳定流 | 一个高并发服务在稳定吞吐下的"动态稳定" |
| 自组织 | 分布式共识（Raft/Paxos）、Kubernetes 调度自愈、CRDT 收敛 |
| 临界点 | 流量达到某个阈值后 queue 突然崩 / cache 突然击穿 |

**关键启发**：
- 你的服务**不是"静止地正确"**，是"在持续输入下动态地正确"。
- 一旦停止输入（缩容、断电），结构会瓦解（队列堆积、连接超时、缓存冷启动）
- **设计要考虑"维持稳定流"的能量代价**，不只是峰值能力

---

## 5. 协同学（Synergetics）

**核心 idea**（Haken）：当系统接近临界点时，**少数"序参量"（order parameters）**支配整个系统的行为。

**关键概念**：
- 序参量（order parameter）：决定系统宏观状态的少数变量
- 涌现（emergence）：序参量从微观相互作用中突现
- 模式选择（pattern selection）：临界点附近的小扰动决定最终模式

**软件工程映射**：

| 协同学 | 软件 |
|---|---|
| 序参量 | 系统级 KPI（端到端 P99、转化率、用户活跃度） |
| 涌现 | 微服务集群的链路 P99、bug 报告趋势、技术债曲线 |
| 模式选择 | 早期架构决定演化方向；早期社区文化决定后期生态 |

**实用启发**：
- 找出你系统的**序参量**（≤5 个）。如果找不到，说明你不知道在优化什么。
- 关键 PR 是模式选择点——一旦合并，后续演化路径被锁定。慎重。
- "为什么集成测试通过但生产出问题"——因为序参量在生产环境的耦合中才涌现。

---

## 6. 突变论（Catastrophe Theory）

**核心 idea**（Thom）：连续的参数变化可以产生**不连续的状态跳变**。

**关键概念**：
- 突变（catastrophe）：参数渐变，但状态突然跳到另一个吸引子
- 滞后（hysteresis）：反向调参时不在同一点回去
- 分岔（bifurcation）：参数过某点后稳态分裂

**软件工程映射**：

| 突变 | 软件 |
|---|---|
| 状态跳变 | 系统从"正常"到"雪崩"的瞬间崩溃 |
| 滞后 | 服务挂了之后扩容也不会立即恢复（缓存冷、连接池要重建） |
| 分岔 | 同样的输入序列，因为顺序不同导致两种完全不同的状态 |

**实用启发**：
- 知道你系统的**突变点**：当某个指标过多少时会发生雪崩？
- 设计**滞后保护**：扩容比缩容更激进，恢复比劣化更慢
- **测试分岔**：chaos engineering 就是主动找突变点

---

## 把六论整合到工作流

总的来说：

1. **架构/设计阶段** → 用**系统论**框定边界与目的、用**控制论三性**做硬约束
2. **构建/编码阶段** → 用**信息论**思考接口/日志的信噪比
3. **运行/演化阶段** → 用**耗散结构**理解为什么需要持续能量、用**协同学**找序参量
4. **故障/危机阶段** → 用**突变论**识别雪崩边界、用控制论反馈分析根因

钱学森的统合在于：**这六论不是六个独立工具，是一组互补的"看复杂系统"的角度**。AI 编码场景里，他们提供了讨论涌现、稳定性、反馈、临界的精确词汇，比"我感觉这里会崩"高级得多。
