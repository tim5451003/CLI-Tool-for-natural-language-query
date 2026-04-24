# Harden & Fix Report

This phase addresses the highest-severity issues from `BREAK_IT_REPORT.md` and `tests/failure_cases.yaml`.

## Changes Implemented

1. **Ambiguity handling (critical)**  
   - Entity resolution now filters obvious non-geographic noise hits (moths, taxa, personal names, etc.).  
   - When multiple Wikidata items share the same surface label and **scores are too close to call**, the CLI stops and returns `needs_disambiguation` instead of silently picking one.  
   - Verified: `capital of georgia` now exits with code **3** and lists the U.S. state vs the country.

2. **Typo + light multilingual normalization (major)**  
   - `normalize_nl.py` applies high-confidence corrections (`poplation` → `population`, `japen` → `japan`, `capitol` → `capital`, `caneda` → `canada`, `capital de` → `capital of`, `población` → `population`) plus optional `rapidfuzz` token fixes.  
   - Verified: `poplation of japen` resolves to `population of japan` and returns a population result.

3. **Contradiction checks (major)**  
   - `contradictions.py` rejects internally inconsistent phrasing before SPARQL generation.  
   - Verified: `smallest cities by highest population` → exit **4**; `capital of japan in europe` → exit **4**.

4. **Scope / unsupported comparative messaging (minor → clearer UX)**  
   - `scope_checks.py` detects underspecified ranking questions and unsupported multi-country comparative queries, returning structured JSON in `--json` mode.  
   - Verified: `biggest cities` and long comparative queries return exit **2** with an explanatory message.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Network or unexpected runtime error |
| 2 | Entity not found, or question out of baseline scope (underspecified / unsupported pattern) |
| 3 | **Disambiguation required** (ambiguous entity resolution) |
| 4 | **Contradiction** (input is internally inconsistent) |

## Known Remaining Gaps

- **Washington**: `population of washington` may still resolve to the U.S. state when the user meant Washington, D.C. (different surface form). A full fix needs explicit `"Washington, D.C."` handling or user-provided QID.  
- **Multilingual coverage** is intentionally small (baseline vocabulary only).  
- **Confidence scores** are implicit via resolver ranking thresholds, not yet exposed as numeric fields in JSON output.

## Suggested Re-test Commands

```bash
python wikidata_cli.py "capital of georgia" --json
python wikidata_cli.py "poplation of japen" --json
python wikidata_cli.py "capital of japan in europe" --json
python wikidata_cli.py "smallest cities by highest population" --json
python wikidata_cli.py "biggest cities" --json
```
