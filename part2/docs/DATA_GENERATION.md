# Part 2 - Requirement 1 (Data Generation)

This folder contains the Part 2 dataset artifacts, fully separated from Part 1 code/files.

## What this delivers

- Programmatic generation of **30 realistic, diverse NL queries** for the Wikidata domain.
- Includes adversarial categories required by Part 2:
  - clean
  - typo_noisy
  - ambiguous
  - multilingual_mixed
  - underspecified
  - complex_constraints

## Schema

Each example in `part2/data/benchmark_queries_v1.jsonl` uses:

- `id`
- `natural_language_query`
- `difficulty`
- `category`
- `notes`

## Re-generate dataset

From project root:

```bash
python part2/scripts/generate_part2_queries.py
```

Outputs:

- `part2/data/benchmark_queries_v1.jsonl`
- `part2/data/benchmark_queries_v1_summary.json`

## Notes

- This step covers only Part 2 Requirement 1 (data generation).
- Ground truth labels and model evaluation pipeline are intentionally left for the next steps.
