---
id: "type-meaningful-slug"    # 必填。格式 {type}-{有意义的英文短横线命名}
                               # 如 result-ferrite-grain-dataset, method-intercept-gb-t6394
                               # 文件名必须与 id 一致：{id}.md，放在 knowledge/atoms/{type}/ 下
title: ""                # 必填。≤15 字，用于列表展示
type: gap                # 必填。gap | method | result | insight | compute
tags: []                 # 必填。至少 2 个：一个"结构标签" + 一个"领域标签"
project: ""              # 必填。关联项目 id，无项目填 "uncategorized"
status: draft            # 必填。draft | final
source: ""               # result/insight 必填。文献 key / 实验编号 / 数据来源文档
created: ""              # 自动或手动填写日期 YYYY-MM-DD
version: "1"             # 可选。版本号，每次实质性修改递增

# --- 以下仅 type=compute 时填写 ---
script: ""               # 脚本文件名，位于 knowledge/atoms/scripts/
script_deps: []           # pip 依赖列表，如 ["numpy", "scipy"]
script_input: ""          # 默认输入数据文件路径（相对于仓库根）
script_input_desc: ""     # 输入格式说明（供人阅读）
script_args: ""           # 额外命令行参数，如 "--group-col treatment --value-col score"
script_output: ""         # 输出说明：脚本输出什么（JSON 字段、表格等）
# --------------------------------
---

# 核心断言

<!-- 一句可独立引用的话。如果是 compute 类型：描述脚本做什么、输出什么。 -->
<!-- ⚠️ 对缩写/命名规律/领域术语的解释若无书面来源，必须用 ⚠️ 标注 + #推测 tag -->

## 证据

<!-- 支撑证据：数据、引文链接、图表路径。 -->
<!-- 每一项事实性断言必须有 source 字段支撑。无 source = 不可引用。 -->
<!-- compute 类型：运行 `python scripts/aggregate.py <proj> --execute` 后自动填入。 -->

## 适用场景

<!-- 何时提取此原子。例："写引言缺口段时"、"讨论与 X 方法对比时"。 -->

## 关联

<!-- 链接到其他原子 id。 -->
