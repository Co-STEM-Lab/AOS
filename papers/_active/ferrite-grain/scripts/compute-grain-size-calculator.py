#!/usr/bin/env python3
"""
晶粒度截点法计算器 —— GB/T 6394—2017。

从手动测量的截线长度和晶界交点数，计算每组样品的：
  - 平均截距 ā (mm)
  - 平均晶粒度级别数 G
  - 95% 置信区间

用法：
    python compute-0002.py --input data.csv
    python compute-0002.py --input data.csv --output results.json

输入格式 (CSV)：
    sample_id,magnification,line_length_mm,intercept_count
    1-边-1,1000,0.5,12
    1-边-2,1000,0.5,14
    1-心-1,1000,0.5,11

输出：JSON，每组样品包含平均截距、G 值、统计信息。
"""
import sys
import json
import argparse
import csv
from collections import defaultdict
import math


def calc_grain_size(intercept_length_mm: float) -> float:
    """
    从平均截距 (mm) 计算 ASTM 晶粒度级别数 G。
    
    GB/T 6394—2017 公式：
        G = -6.6457 log2(ā) - 3.298
    其中 ā 为平均截距（mm）。
    """
    if intercept_length_mm <= 0:
        return None
    return -6.6457 * math.log2(intercept_length_mm) - 3.298


def read_measurements(path: str) -> list[dict]:
    """读取 CSV 测量数据。"""
    measurements = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # 兼容 BOM
        fieldnames = [k.strip().lstrip('﻿') for k in reader.fieldnames]
        for row in reader:
            # 清理 key
            clean_row = {k.strip().lstrip('﻿'): v.strip() for k, v in row.items()}
            measurements.append({
                "sample_id": clean_row["sample_id"],
                "magnification": float(clean_row["magnification"]),
                "line_length_mm": float(clean_row["line_length_mm"]),
                "intercept_count": int(clean_row["intercept_count"]),
            })
    return measurements


def process(measurements: list[dict]) -> dict:
    """按样品分组处理测量数据。"""
    groups = defaultdict(list)
    for m in measurements:
        # 换算实际截线长度：图像长度 / 放大倍数
        actual_length_mm = m["line_length_mm"] / m["magnification"]
        groups[m["sample_id"]].append({
            "actual_length_mm": actual_length_mm,
            "intercept_count": m["intercept_count"],
        })

    results = {}
    for sample_id, data in groups.items():
        n = len(data)
        total_length = sum(d["actual_length_mm"] for d in data)
        total_intercepts = sum(d["intercept_count"] for d in data)

        if total_intercepts == 0:
            results[sample_id] = {"error": "交点数之和为 0，无法计算"}
            continue

        # 每条截线的截距
        intercepts = [
            d["actual_length_mm"] / d["intercept_count"]
            for d in data if d["intercept_count"] > 0
        ]

        if not intercepts:
            results[sample_id] = {"error": "无有效截线数据"}
            continue

        avg_intercept = sum(intercepts) / len(intercepts)
        g_value = calc_grain_size(avg_intercept)

        # 标准差和 95% 置信区间
        if len(intercepts) > 1:
            mean_val = sum(intercepts) / len(intercepts)
            variance = sum((x - mean_val) ** 2 for x in intercepts) / (len(intercepts) - 1)
            std_dev = math.sqrt(variance)
            se = std_dev / math.sqrt(len(intercepts))
            ci_95 = 1.96 * se
        else:
            std_dev = 0
            ci_95 = 0

        # 按截线长度加权的平均截距（更准确）
        weighted_intercept = total_length / total_intercepts

        results[sample_id] = {
            "n_lines": n,
            "total_length_mm": round(total_length, 6),
            "total_intercepts": total_intercepts,
            "mean_intercept_length_mm": round(avg_intercept, 6),
            "weighted_intercept_mm": round(weighted_intercept, 6),
            "grain_size_number_G": round(g_value, 2) if g_value else None,
            "std_dev_mm": round(std_dev, 6),
            "ci_95_mm": round(ci_95, 6),
            "ci_95_pct": round(ci_95 / avg_intercept * 100, 2) if avg_intercept > 0 else 0,
        }

    return results


def main():
    parser = argparse.ArgumentParser(description="晶粒度截点法计算器 — GB/T 6394—2017")
    parser.add_argument("--input", required=True, help="CSV 测量数据文件")
    parser.add_argument("--output", default=None, help="输出 JSON 文件路径（默认 stdout）")

    args = parser.parse_args()

    try:
        measurements = read_measurements(args.input)
        results = process(measurements)

        output = {
            "method": "GB/T 6394—2017 截点法",
            "n_measurements": len(measurements),
            "n_samples": len(results),
            "results": results,
        }

        json_out = json.dumps(output, indent=2, ensure_ascii=False)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_out)
            print(f"✅ 已输出: {args.output}")
        else:
            print(json_out)

    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
