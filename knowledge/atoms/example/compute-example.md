---
id: "compute-NNNN"
title: "Welch t-test + Cohen's d"
type: compute
tags: ["#方法组件", "#统计检验"]
project: "uncategorized"
status: final
source: ""
created: "2026-06-23"
script: "compute-NNNN.py"
script_deps: []
script_input: "data/experiment_results.csv"
script_input_desc: "CSV 格式，含分组列和数值列。例：treatment,score"
script_args: "--group-col treatment --value-col score"
---

# 核心断言

两组独立样本的 Welch t-test（不假设方差齐性）+ Cohen's d 效应量。适用于实验组 vs 对照组的均值差异检验。

## 证据

<!-- 运行 `python scripts/aggregate.py <proj> --execute` 后自动填入脚本输出。 -->

## 适用场景

- 方法对比实验（如消融研究中 A 方法 vs B 方法的性能差异检验）
- 数据异质性分析（子集 A 与子集 B 的分布差异定量判断）
- 任何需要提供 "p < 0.05" 和效应量的段落

## 关联

- 可被 method 类型原子引用，如 "组间差异由 Welch t-test 检验（详见 `compute-0001`）"
