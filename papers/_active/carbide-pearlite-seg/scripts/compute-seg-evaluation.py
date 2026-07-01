#!/usr/bin/env python3
"""
语义分割结果评估计算器 — 从预测掩膜和真值掩膜计算 mIoU/Dice 等指标。

用法：
    python compute-seg-evaluation.py --input data.csv
    python compute-seg-evaluation.py --input data.csv --output results.json

输入格式 (CSV)：
    sample_id,pred_path,gt_path
    5-1000x-1,data/pred/5-1000x-1.png,data/gt/5-1000x-1.png

输出：JSON，每样本每类别 IoU + Dice + 汇总 mIoU。
"""
import sys
import json
import argparse
import csv
import numpy as np


def compute_ious(pred: np.ndarray, gt: np.ndarray, n_classes: int = 3) -> dict:
    """计算每个类别的 IoU 和 Dice。"""
    results = {}
    ious = []
    for c in range(n_classes):
        pred_c = (pred == c)
        gt_c = (gt == c)
        intersection = np.sum(pred_c & gt_c).item()
        union = np.sum(pred_c | gt_c).item()
        pred_sum = np.sum(pred_c).item()
        gt_sum = np.sum(gt_c).item()

        iou = intersection / union if union > 0 else (1.0 if intersection == gt_sum == 0 else 0.0)
        dice = 2 * intersection / (pred_sum + gt_sum) if (pred_sum + gt_sum) > 0 else (1.0 if intersection == 0 else 0.0)
        precision = intersection / pred_sum if pred_sum > 0 else 1.0
        recall = intersection / gt_sum if gt_sum > 0 else 1.0

        class_name = ["background", "carbide", "pearlite"][c]
        results[class_name] = {
            "iou": round(iou, 4),
            "dice": round(dice, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
        }
        ious.append(iou)

    results["mIoU"] = round(np.mean(ious).item(), 4)
    return results


def read_input(path: str) -> list[dict]:
    """读取 CSV 输入。"""
    samples = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append({
                "sample_id": row["sample_id"].strip(),
                "pred_path": row["pred_path"].strip(),
                "gt_path": row["gt_path"].strip(),
            })
    return samples


def main():
    parser = argparse.ArgumentParser(description="语义分割结果评估")
    parser.add_argument("--input", required=True, help="CSV 输入文件")
    parser.add_argument("--output", default=None, help="输出 JSON 路径（默认 stdout）")
    args = parser.parse_args()

    try:
        from skimage.io import imread
        samples = read_input(args.input)
        all_results = {}
        summary_ious = []

        for s in samples:
            pred = imread(s["pred_path"])
            gt = imread(s["gt_path"])
            if pred.shape != gt.shape:
                print(f"⚠️  {s['sample_id']} 形状不匹配: pred={pred.shape}, gt={gt.shape}", file=sys.stderr)
                continue
            result = compute_ious(pred, gt)
            all_results[s["sample_id"]] = result
            summary_ious.append(result["mIoU"])

        output = {
            "n_samples": len(all_results),
            "mean_mIoU": round(np.mean(summary_ious).item(), 4) if summary_ious else 0,
            "results": all_results,
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
