"""Load Part 2 benchmark and ground-truth files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_benchmark_with_ground_truth(root: Path) -> List[Dict[str, Any]]:
    """Return rows from benchmark_ground_truth_v1.jsonl.

    This file already contains query metadata and `ground_truth_structured_query`.
    """
    gt_path = root / "part2" / "data" / "benchmark_ground_truth_v1.jsonl"
    if not gt_path.exists():
        raise FileNotFoundError(f"Missing ground truth file: {gt_path}")
    return read_jsonl(gt_path)

