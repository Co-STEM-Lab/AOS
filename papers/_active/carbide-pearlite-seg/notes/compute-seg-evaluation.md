---
id: "compute-seg-evaluation"
title: "语义分割结果评估计算器"
type: compute
tags: ["#方法组件", "#金相分析"]
project: "proj-carbide-pearlite-seg"
status: draft
source: "首钢驻场检测 AI 团队评估规范"
created: "2026-06-23"
script: "compute-seg-evaluation.py"
script_deps: ["numpy", "scikit-image"]
script_input: "data/seg-evaluation-input.csv"
script_input_desc: "CSV 格式：sample_id, pred_path, gt_path, 每行一对预测+真实掩膜路径"
script_args: ""
---

# 核心断言

从预测分割掩膜与人工标注的真值掩膜计算像素级语义分割指标：mIoU、Dice、Precision、Recall，并输出每类别分项指标。

## 输入格式

```csv
sample_id,pred_path,gt_path
5-1000x-1,data/pred/5-1000x-1.png,data/gt/5-1000x-1.png
```

## 输出指标

| 指标 | 含义 | 范围 |
|------|------|------|
| mIoU | 平均交并比（所有类别平均） | 0–1 |
| IoU_{carbide} | 碳化物类 IoU | 0–1 |
| IoU_{pearlite} | 片层珠光体类 IoU | 0–1 |
| Dice | Dice 系数（每个类别） | 0–1 |
| Precision | 精确率 | 0–1 |
| Recall | 召回率 | 0–1 |

## 适用场景

- 对比不同分割模型的量化性能
- 筛选 benchmark 子集的最优模型
- 验证标注质量（标注员间一致性）

## 关联

- `result-carbide-pearlite-dataset`：碳化物+片层珠光体金像AI数据集
- `method-semantic-seg-annotation`：语义分割标注方法
- `proj-carbide-pearlite-seg`：碳化物+片层珠光体图像分割项目
