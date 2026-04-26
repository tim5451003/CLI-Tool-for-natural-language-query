"""Run the Part 2 evaluation skeleton end-to-end."""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .dataset import load_benchmark_with_ground_truth
from .predictor import AVAILABLE_MODES, predict_with_mode
from .scoring import score_single_prediction


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    exact = sum(r["score"]["exact_correct"] for r in results)
    tolerant = sum(r["score"].get("tolerant_correct", 0) for r in results)
    overall_accuracy = exact / total if total else 0.0
    tolerant_accuracy = tolerant / total if total else 0.0

    by_category: Dict[str, List[int]] = defaultdict(list)
    by_difficulty: Dict[str, List[int]] = defaultdict(list)
    schema_failures = 0
    for r in results:
        by_category[r["category"]].append(r["score"]["exact_correct"])
        by_difficulty[r["difficulty"]].append(r["score"]["exact_correct"])
        if not r["score"]["schema_valid"]:
            schema_failures += 1

    return {
        "total_examples": total,
        "exact_correct": exact,
        "overall_accuracy": round(overall_accuracy, 4),
        "tolerant_correct": tolerant,
        "tolerant_accuracy": round(tolerant_accuracy, 4),
        "schema_failure_rate": round(schema_failures / total, 4) if total else 0.0,
        "category_accuracy": {
            k: round(sum(v) / len(v), 4) for k, v in sorted(by_category.items())
        },
        "difficulty_accuracy": {
            k: round(sum(v) / len(v), 4) for k, v in sorted(by_difficulty.items())
        },
    }


def run(mode: str, output_dir: Path, sleep_seconds: float = 0.0) -> Path:
    root = Path(__file__).resolve().parents[2]
    rows = load_benchmark_with_ground_truth(root)

    detailed_results: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        gt = row["ground_truth_structured_query"]
        pred = predict_with_mode(mode, row)
        score = score_single_prediction(gt, pred)
        detailed_results.append(
            {
                "id": row["id"],
                "category": row["category"],
                "difficulty": row["difficulty"],
                "natural_language_query": row["natural_language_query"],
                "ground_truth": gt,
                "prediction": pred,
                "score": score,
            }
        )
        if sleep_seconds > 0 and idx < len(rows) - 1:
            time.sleep(sleep_seconds)

    summary = summarize(detailed_results)
    payload = {
        "run_mode": mode,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "results": detailed_results,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"eval_run_{mode}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Part2 evaluation skeleton runner")
    parser.add_argument(
        "--mode",
        default="oracle",
        choices=AVAILABLE_MODES,
        help="Prediction mode (dry-run or real model adapter)",
    )
    parser.add_argument(
        "--output-dir",
        default="part2/eval/runs",
        help="Directory to write evaluation run JSON",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Fixed delay between each query request (seconds)",
    )
    args = parser.parse_args()

    path = run(mode=args.mode, output_dir=Path(args.output_dir), sleep_seconds=max(0.0, args.sleep_seconds))
    print(f"Wrote evaluation run to: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

