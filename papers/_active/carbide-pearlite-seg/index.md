---
id: "proj-carbide-pearlite-seg"
title: "碳化物+片层珠光体图像分割"
domain: "金相分析"
problem: "碳化物+片层珠光体分割"
status: active
priority: medium
skills_required: ["金相分析", "图像分割", "计算机视觉"]
target_venue: ""
deadline: ""
created: "2026-06-23"
updated: "2026-06-23"
---

# 碳化物+片层珠光体图像分割

## 一句话定位

对首钢驻场采集的钢材金相图像，基于深度学习方法，进行碳化物析出相和片层珠光体两类的像素级语义分割。

## 数据集

原始金相图像位于：
/media/chenguisen/WD_BLACK1/AISI/首钢驻场资料编写/数据集/碳化物+片层珠光体-金相图片-AI/

共 20 张 1000× 图像（样品 5–8），附带人工标注和 AI 分割结果。

## 关联原子

### 方法组件
- method-semantic-seg-annotation：语义分割标注方法

### 结果讨论
- result-carbide-pearlite-dataset：碳化物+片层珠光体金像AI数据集

### 计算工具
- compute-seg-evaluation：分割结果评估计算器

## 进度日志

| 日期 | 进展 | 阻塞 |
|------|------|------|
| 2026-06-23 | 数据集入库（result），标注方法文档化（method），评估工具建成（compute） | 需确认标注结果的具体模型来源 |

## 产出链接

<!-- 论文草稿 / 提交记录 / 演讲 slides 路径 -->

## 复盘

<!-- 完成后填写 -->
