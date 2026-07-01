---
title: ""                                # 必填。论文标题
project: ""                              # 必填。关联项目 id
venue: ""                                # 目标期刊/会议
status: drafting                         # drafting | submitted | revision | accepted | published
version: "0.1"
authors: []                              # 作者列表：["Name1", "Name2"] 或按详情格式
affiliations: []                         # 机构列表
corresponding: ""                        # 通讯作者邮箱
abstract: ""                             # 论文摘要
keywords: ""                             # 关键词，逗号分隔
shorttitle: ""                           # 短标题（LaTeX 用，≤60 字符）
shortauthors: ""                         # 短作者（LaTeX 用）
funding: ""                              # 基金致谢
data_availability: ""                    # 数据开放声明
conflict_of_interest: ""                 # 利益冲突声明
highlights: ""                           # 研究亮点（LaTeX 用，可选）
bios: ""                                 # 作者简介（LaTeX 用，可选）
bibfile: "references"                    # .bib 文件名（不含扩展名）
created: ""                              # YYYY-MM-DD
updated: ""                              # YYYY-MM-DD

# --- 可选：每位作者的详细信息（LaTeX 投稿用）---
# author1: {name: "", email: "", org: "", address: "", city: "",
#           postcode: "", state: "", country: "", credit: "", orcid: ""}
# author2: {name: "", email: "", ...}
# ...
# --------------------------------------------
---

# {{title}}

## Abstract

<!-- 一句话概括：①研究问题 ②方法 ③关键结果（含数字）④结论 -->

## 1. Introduction

<!-- 缺口原子 → 研究问题原子 → 贡献列表（3–5 条） -->

## 2. Related Work

<!-- 按主题分组，每组结尾指出与本文差异 -->

## 3. Method

<!-- 整体框架图 + 每模块描述 + 设计动机 -->

## 4. Experiments

<!-- 实验设置（数据/指标/基线）→ 主结果表 → 消融实验 → 可视化 -->

## 5. Discussion

<!-- 结果解读 → 与已有工作对比 → 局限性 → 实际意义 -->

## 6. Conclusion

<!-- 总结贡献 + 未来方向（≤2 条，不引入新材料） -->

## 致谢

<!-- funding 信息 -->

## 数据与代码可用性

<!-- data_availability 信息 -->

## 作者贡献

<!-- 每位作者的具体贡献 -->

## 参考文献

<!-- 使用 [@citekey] 格式引用，render.py 自动转 LaTeX \citep -->

## Appendix: 原子索引

<!-- 列出这篇论文消费了哪些原子，发表后回存新原子 -->

