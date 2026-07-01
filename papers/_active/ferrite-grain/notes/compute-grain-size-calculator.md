---
id: "compute-grain-size-calculator"
title: "晶粒度截点法计算器"
type: compute
tags: ["#方法组件", "#金相分析"]
project: "proj-ferrite-grain"
status: draft
source: "GB/T 6394—2017"
created: "2026-06-23"
script: "compute-grain-size-calculator.py"
script_deps: []
script_input: "data/grain-size-measurements.csv"
script_input_desc: "CSV 格式：sample_id, magnification, line_length_mm, intercept_count, 每行一条截线数据"
script_args: ""
---

# 核心断言

根据 GB/T 6394—2017 截点法，从手动测量的截线长度和晶界交点数计算平均晶粒度级别数 G。

## 输入格式

```csv
sample_id,magnification,line_length_mm,intercept_count
1-边-1,1000,0.5,12
1-边-2,1000,0.5,14
1-心-1,1000,0.5,11
```

- `sample_id`: 样品标识（如 "1-边-1" = 1号样边部第1条截线）
- `magnification`: 显微镜放大倍数（如 200, 500, 1000）
- `line_length_mm`: 图像上测量的截线长度（mm）
- `intercept_count`: 该截线与晶界的交点数

## 输出

按样品分组输出：
- 平均截距 $\bar{l}$ (mm)
- 平均晶粒度级别数 $G$
- 95% 置信区间

## 适用场景

- 铁素体晶粒度测试数据的批量处理
- 手动计数后的标准化计算
- 多人测量的一致性检验

## 关联

- `method-gb-t6394-intercept`：GB/T 6394—2017 截点法
- `result-ferrite-grain-dataset`：铁素体晶粒度测试数据集
- `proj-ferrite-grain`：铁素体晶粒度自动化评级系统
