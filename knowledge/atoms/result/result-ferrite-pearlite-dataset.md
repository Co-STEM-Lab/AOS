---
id: "result-ferrite-pearlite-dataset"
title: "铁素体+珠光体（F+P）金相AI数据集"
type: result
tags: ["#结果讨论", "#金相分析"]
project: "proj-ferrite-pearlite-seg"
status: final
source: "首钢驻场检测，2026-06"
created: "2026-06-23"
---

# 核心断言

铁素体+珠光体（F+P）金相图像数据集包含 **3 个钢材试样**的 **29 张显微图像**，附带 AI 预标注和人工精标注，用于铁素体-珠光体组织的图像分割模型训练与评估。

## 数据来源

原始图像为首钢驻场检测时拍摄的钢材金相照片。⚠️ 数据集组织者待确认（无直接来源，推测可能与邱宇团队相关）。包含 AI 自动分割、AIGC 生成等多种结果。

## 数据集组成

| 组件 | 数量 | 格式 | 说明 |
|------|------|------|------|
| 原始图像 | 29 | JPG | 1280×960，3 个试样，center/quarter/bian 位置 |
| 预标注（AI） | 29 | PNG | AI 自动预分割结果 |
| GT 可视化 benchmark | 4 | PNG | 人工精标注的评测基准 |
| GT 可视化 label | 21 | PNG | 人工精标注的训练标签 |
| FH 训练推理可视化 | 25 | PNG | 训练/推理结果可视化（含红/白叠加） |
| AIGC 生成结果 | 500 | PNG | 25 张基础图 ×20 帧，AI 生成 |
| FP_batch2 | 15 | PNG | 第二批结果 |
| 可视化不反转 | 29 | JPG | 同原始图像但不反转显示 |
| canvas-image | 1 | PNG | ⚠️ 内容待确认（含底部疑似标注文字区域） |

## 样品信息

| 样品 | 图像数 | 位置分布 | 说明 |
|------|--------|---------|------|
| 1 | 12 | center-2(7张), quarter-4(5张) | — |
| 2 | 10 | bian(1张), center-2(3张), quarter-4(6张) | — |
| 3 | 7 | Bian(1张), center-2(3张), quarter-4(3张) | — |

> ⚠️ "bian"（边）含义待确认，推测为试样边缘位置。大小写不统一（"bian" vs "Bian"）。

## 图像命名规范

```
{样品编号}-{位置}_{相机编号} ({序号}).{ext}
例：1-center-2_m001 (1).jpg → 样品 1，中心位置，相机 m001，第 1 张
```

## 标注规范

⚠️ 本数据集的标注像素值映射目前未知，以下信息待确认：

- 有 4 张 benchmark、21 张 label 的 GT 可视化文件（vis_gt/）
- 预标注（预标注/）为 AI 自动生成结果
- 未见独立的标注规范文档

## 文件清单

### 原始图像（29 张）

| 样品 | 位置 | 文件列表 |
|------|------|---------|
| 1 | center-2 | `1-center-2_m001 (1).jpg` ~ `1-center-2_m001 (7).jpg` |
| 1 | quarter-4 | `1-quarter-4_m001 (1).jpg` ~ `1-quarter-4_m001 (5).jpg` |
| 2 | bian | `2-bian-_m002 (3).jpg` |
| 2 | center-2 | `2-center-2_m001 (1).jpg` ~ `2-center-2_m001 (3).jpg` |
| 2 | quarter-4 | `2-quarter-4_m001 (1).jpg` ~ `2-quarter-4_m001 (6).jpg` |
| 3 | Bian | `3-Bian-_m001 (3).jpg` |
| 3 | center-2 | `3-center-2_m003 (1).jpg` ~ `3-center-2_m003 (3).jpg` |
| 3 | quarter-4 | `3-quarter-4_m001 (1).jpg` ~ `3-quarter-4_m001 (3).jpg` |

### 目录结构

```
F+P组织-AI组/
├── 组织-AI组/                    # 原始图像（29 JPG + canvas-image.png）
│   ├── 1-center-2_m001 (1).jpg
│   ├── ...
│   └── canvas-image.png          # ⚠️ 内容待确认
├── 预标注/                       # AI 预标注（29 PNG）
├── FH_vis_训练和推理结果/         # 训练/推理可视化（25 PNG）
├── FP_aigc/                      # AIGC 生成结果（500 PNG, 25×20）
├── FP_batch2/                    # 第二批结果（15 PNG）
├── vis_gt/                       # GT 可视化
│   ├── benchmark/               # 评测基准（4 PNG）
│   └── label/                   # 训练标签（21 PNG）
├── 可视化不反转/                 # 非反转显示（29 JPG）
├── 1-2-3-5/                     # 原始图像另存（样品 1/2/3/5 子目录）
└── *.rar / *.zip                # 归档压缩包
```

## 适用场景

- 铁素体+珠光体显微组织语义分割模型训练
- F+P 组织形态学分析与定量测量
- AIGC 在金相图像生成中的应用研究
- AI 分割算法在钢材料显微图像上的评测

## 关联

- `proj-ferrite-pearlite-seg`：铁素体+珠光体图像分割项目
