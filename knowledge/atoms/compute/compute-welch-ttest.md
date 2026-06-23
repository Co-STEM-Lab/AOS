---
id: "compute-welch-ttest"
title: "Welch t-test + Cohen's d"
type: compute
tags: ["#方法组件", "#统计检验"]
project: "uncategorized"
status: final
source: ""
created: "2026-06-23"
script: "compute-0001.py"
script_deps: []
script_input: "data/experiment_results.csv"
script_input_desc: "CSV 格式，含分组列和数值列。"
script_args: "--group-col treatment --value-col score"
---

# 核心断言

两组独立样本的 Welch t-test（不假设方差齐性）+ Cohen's d 效应量。适用于实验组 vs 对照组的均值差异检验。

## 证据

<!-- 运行后自动填入 -->

## 适用场景

- 方法对比实验的差异显著性检验
- 数据异质性分析
