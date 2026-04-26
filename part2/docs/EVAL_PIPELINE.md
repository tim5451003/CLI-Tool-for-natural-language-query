# Part 2 - Evaluation Pipeline Skeleton (Starter)

This is the starter pipeline for Part 2 Step 3 onward.

## Implemented now

- Dataset loader for `part2/data/benchmark_ground_truth_v1.jsonl`
- Schema validation for structured outputs by `status`
- Field-level scoring + exact-correct flag
- End-to-end runner that writes a full run artifact JSON

## Files

- `part2/eval/dataset.py`: load benchmark+ground truth
- `part2/eval/schema.py`: prediction schema validation
- `part2/eval/scoring.py`: field-level scoring logic
- `part2/eval/predictor.py`: prediction adapter (`oracle`/`naive` + real model modes)
- `part2/eval/run_eval.py`: run and write eval result file

## Dry run commands

Sanity check (should be 100% exact):

```bash
python -m part2.eval.run_eval --mode oracle
```

Weak baseline check:

```bash
python -m part2.eval.run_eval --mode naive
```

## Real model modes (4-model mix: 2 closed-source + 2 open-weight)

Implemented modes:

- `openai_gpt4o_mini` (closed-source via OpenAI API)
- `openai_gpt4_1` (closed-source via OpenAI API)
- `together_llama_3_1_70b` (open-weight via Together API)
- `ollama_qwen2_5_7b` (open-weight local deployment via Ollama)

Set environment variables before running:

```bash
# PowerShell
$env:OPENAI_API_KEY="..."
$env:TOGETHER_API_KEY="..."
$env:OLLAMA_BASE_URL="http://localhost:11434"   # optional
```

Example runs:

```bash
python -m part2.eval.run_eval --mode openai_gpt4o_mini
python -m part2.eval.run_eval --mode openai_gpt4_1
python -m part2.eval.run_eval --mode together_llama_3_1_70b
python -m part2.eval.run_eval --mode ollama_qwen2_5_7b
```

Outputs:

- `part2/eval/runs/eval_run_oracle.json`
- `part2/eval/runs/eval_run_naive.json`

## Next integration step

Add more model adapters if needed, while keeping the same scoring and summary format for fair comparison.
