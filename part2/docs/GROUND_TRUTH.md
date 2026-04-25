# Part 2 - Requirement 2 (Ground Truth)

This document describes the ground truth labeling artifact for the 30-query benchmark.

## Output files

- `part2/data/benchmark_ground_truth_v1.jsonl`
- `part2/data/benchmark_ground_truth_v1_summary.json`

## Schema (per example)

- `id`
- `natural_language_query`
- `difficulty`
- `category`
- `ground_truth_structured_query`
- `notes`

## Ground truth policy

Ground truth is manually specified to match the Part 1 system design:

- `status = "ok"`: query is in-scope and maps to structured intent fields.
- `status = "needs_disambiguation"`: ambiguous entity/location; model should not guess.
- `status = "unsupported_or_underspecified"`: missing constraints or unsupported comparative logic.
- `status = "contradiction"`: internally inconsistent constraints.

This allows evaluation to score both successful mappings and safe handling of edge cases.

## Generate

```bash
python part2/scripts/generate_part2_ground_truth.py
```
