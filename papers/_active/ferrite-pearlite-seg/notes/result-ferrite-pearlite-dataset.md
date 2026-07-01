---
id: "result-ferrite-pearlite-dataset"
title: "⚠️ F+P 组织金相AI数据集（含义待确认）"
type: result
tags: ["#结果讨论", "#金相分析", "#推测"]
project: "proj-ferrite-pearlite-seg"
status: draft
source: "首钢驻场检测，2026-06"
created: "2026-06-23"
---

# 核心断言

⚠️ 以下内容均为基于文件名的推断，未经原始来源确认。

F+P组织金相图像数据集包含 **3 个钢材试样**的 **29 张显微图像**，附带标注和 AI 处理结果。

> ⚠️ "F+P" 含义推测为 Ferrite（铁素体）+ Pearlite（珠光体），但无直接来源证实。也可能是其他金相组织的缩写。对比同级目录 "碳化物+片层珠光体-金相图片-AI" 为明确的中文命名，本数据集仅写 "F+P组织-AI组"，缩写含义待确认。

## 数据来源

原始图像位于首钢驻场资料编写/数据集/F+P组织-AI组/，与碳化物+片层珠光体数据集同根目录，推测为首钢驻场检测期间拍摄的钢材金相照片。

⚠️ 数据集组织者、拍摄条件、设备参数均无文档说明。

## 数据集组成

| 组件 | 数量 | 格式 | ⚠️ 说明（均为推测） |
|------|------|------|------|
| 原始图像 | 29 | JPG | 1280×960，3 个试样，center/quarter/bian 位置 |
| 预标注 | 29 | PNG | 推测为预标注（来源未知：AI/人工？） |
| vis_gt benchmark | 4 | PNG | "gt" 推测为 ground truth，benchmark 推测为评测基准 |
| vis_gt label | 21 | PNG | 推测为训练标签 |
| FH_vis | 25 | PNG | ⚠️ "FH" 含义未知，文件名含 "训练和推理" 推测为可视化结果 |
| FP_aigc | 500 | PNG | "aigc" = AI Generated Content，推测为 AI 生成数据 |
| FP_batch2 | 15 | PNG | 推测为第二批处理结果 |
| 可视化不反转 | 29 | JPG | ⚠️ 与原始图像关系待确认（"不反转"含义未验证） |
| canvas-image | 1 | PNG | uni-aims 模型零样本推理结果（微调前基线，用户确认） |

## 样品信息

| 样品 | 图像数 | ⚠️ 位置分布（均为文件名推测） | 说明 |
|------|--------|---------|------|
| 1 | 12 | center-2(7张), quarter-4(5张) | — |
| 2 | 10 | bian(1张), center-2(3张), quarter-4(6张) | — |
| 3 | 7 | Bian(1张), center-2(3张), quarter-4(3张) | — |

> ⚠️ "center-2" / "quarter-4" / "bian" 含义推测：中心 / 1/4 处 / 边缘。大小写不统一（"bian" vs "Bian"）。所有位置含义均未确认。
>
> ⚠️ 目录 "1-2-3-5/" 含样品 5（不同命名规范），是否属于本数据集待确认。

## 图像命名规范

```
{样品编号}-{位置}_{编码} ({序号}).{ext}
例：1-center-2_m001 (1).jpg → 样品 1，位置 center-2，编码 m001，第 1 张
```

> ⚠️ "_m001" / "_m002" / "_m003" 含义推测为显微镜/相机/物镜编号，未确认。

## 标注规范

⚠️ 本数据集无标注规范文档。像素值到语义类别的映射未知。

## 文件清单

### 原始图像（29 张）

| 样品 | ⚠️ 位置 | 文件列表 |
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
F+P组织-AI组/                     # ⚠️ "F+P" 含义待确认
├── 组织-AI组/                    # 29 JPG + canvas-image.png
│   ├── 1-center-2_m001 (1).jpg
│   ├── ...
│   └── canvas-image.png          # uni-aims 零样本推理结果（微调前基线）
├── 预标注/                       # ⚠️ 29 PNG，来源/方式未确认
├── FH_vis_训练和推理结果/         # ⚠️ "FH" 含义未知
├── FP_aigc/                      # 推测为 AI 生成数据
├── FP_batch2/                    # 推测为第二批结果
├── vis_gt/                       # ⚠️ "gt" = ground truth？推测
│   ├── benchmark/               # ⚠️ 4 张
│   └── label/                   # ⚠️ 21 张
├── 可视化不反转/                 # ⚠️ 与原始图像关系待确认
├── 1-2-3-5/                     # ⚠️ 含样品 5，是否属本集待确认
└── *.rar / *.zip                # 压缩包
```

## 适用场景

⚠️ 以下为推测，未经验证：

- F+P 显微组织图像分割模型训练
- F+P 组织形态学分析
- AI 在金相图像生成中的应用
- AI 分割算法评测

## 关联

- `proj-ferrite-pearlite-seg`：⚠️ F+P 图像分割项目（F+P 含义待确认）
