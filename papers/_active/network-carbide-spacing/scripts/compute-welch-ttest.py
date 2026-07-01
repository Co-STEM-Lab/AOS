#!/usr/bin/env python3
"""
两组独立样本 Welch t-test + Cohen's d 效应量。

用法：
    python compute-0001.py --input data.csv --group-col treatment --value-col score
    python compute-0001.py --input data.csv --group-col treatment --value-col score --group-a "Control" --group-b "Experimental"

输入格式 (CSV)：
    treatment,score
    Control,0.82
    Experimental,0.91
    ...

输出：JSON 格式，含统计量、p 值、效应量及文字解读。
"""
import sys
import json
import argparse
import csv
from collections import defaultdict
from math import sqrt


def welch_ttest(group_a: list[float], group_b: list[float]) -> dict:
    """Welch's t-test（不假设方差齐性）。"""
    n_a, n_b = len(group_a), len(group_b)
    if n_a < 2 or n_b < 2:
        return {"error": "每组至少需要 2 个样本"}

    mean_a = sum(group_a) / n_a
    mean_b = sum(group_b) / n_b

    var_a = sum((x - mean_a) ** 2 for x in group_a) / (n_a - 1)
    var_b = sum((x - mean_b) ** 2 for x in group_b) / (n_b - 1)

    se = sqrt(var_a / n_a + var_b / n_b)
    if se == 0:
        return {"error": "标准误为 0，两组无差异或样本完全一致"}

    t_stat = (mean_a - mean_b) / se

    # Welch-Satterthwaite 自由度
    df_num = (var_a / n_a + var_b / n_b) ** 2
    df_den = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    df = df_num / df_den if df_den != 0 else 1

    # p 值近似（正态近似，大样本合理）
    from math import erf
    def norm_cdf(x):
        return 0.5 * (1 + erf(x / sqrt(2)))

    p_value = 2 * (1 - norm_cdf(abs(t_stat)))

    # Cohen's d
    pooled_sd = sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    cohens_d = (mean_a - mean_b) / pooled_sd if pooled_sd != 0 else 0

    # 效应量解读
    d_abs = abs(cohens_d)
    if d_abs < 0.2:
        effect_label = "可忽略 (d < 0.2)"
    elif d_abs < 0.5:
        effect_label = "小 (0.2 ≤ d < 0.5)"
    elif d_abs < 0.8:
        effect_label = "中等 (0.5 ≤ d < 0.8)"
    else:
        effect_label = "大 (d ≥ 0.8)"

    alpha = 0.05
    significant = p_value < alpha

    return {
        "group_a": {"n": n_a, "mean": round(mean_a, 6), "std": round(sqrt(var_a), 6)},
        "group_b": {"n": n_b, "mean": round(mean_b, 6), "std": round(sqrt(var_b), 6)},
        "t_statistic": round(t_stat, 4),
        "df": round(df, 2),
        "p_value": round(p_value, 6),
        "significant_at_0.05": significant,
        "cohens_d": round(cohens_d, 4),
        "effect_size": effect_label,
        "mean_difference": round(mean_a - mean_b, 6),
    }


def read_csv_groups(path: str, group_col: str, value_col: str,
                    group_a_label: str = None, group_b_label: str = None) -> tuple[list[float], list[float], str, str]:
    """从 CSV 中读取两组数据。"""
    groups = defaultdict(list)
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            groups[row[group_col]].append(float(row[value_col]))

    group_names = sorted(groups.keys())
    if len(group_names) < 2:
        raise ValueError(f"CSV 中至少需要两个不同的分组值，找到: {group_names}")

    if group_a_label is None:
        group_a_label = group_names[0]
    if group_b_label is None:
        group_b_label = group_names[1]

    if group_a_label not in groups:
        raise ValueError(f"分组 '{group_a_label}' 不在数据中。可用分组: {list(groups.keys())}")
    if group_b_label not in groups:
        raise ValueError(f"分组 '{group_b_label}' 不在数据中。可用分组: {list(groups.keys())}")

    return groups[group_a_label], groups[group_b_label], group_a_label, group_b_label


def main():
    parser = argparse.ArgumentParser(description="Welch t-test + Cohen's d")
    parser.add_argument("--input", required=True, help="CSV 数据文件路径")
    parser.add_argument("--group-col", required=True, help="分组列名")
    parser.add_argument("--value-col", required=True, help="数值列名")
    parser.add_argument("--group-a", default=None, help="A 组标签（默认取第一组）")
    parser.add_argument("--group-b", default=None, help="B 组标签（默认取第二组）")

    args = parser.parse_args()

    try:
        group_a, group_b, label_a, label_b = read_csv_groups(
            args.input, args.group_col, args.value_col, args.group_a, args.group_b
        )
        result = welch_ttest(group_a, group_b)
        result["group_a"]["label"] = label_a
        result["group_b"]["label"] = label_b
        result["input_file"] = args.input
        result["test"] = "Welch's t-test (two-sided)"
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
