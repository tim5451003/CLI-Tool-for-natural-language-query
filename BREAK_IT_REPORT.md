# Break-It Report (Step 11-12)

This document captures the systematic break-it phase for the baseline Wikidata CLI and ranks failures by severity.

## Method (Step 11)

- Built an adversarial test matrix with categories: ambiguous input, typos, mixed language, underspecified questions, conflicting constraints, and unsupported comparative logic.
- Executed all queries against the live baseline CLI using `python wikidata_cli.py "<query>" --json`.
- Kept baseline control queries to ensure normal in-scope behavior still passes.

## Test Matrix Summary

- Total tests: 14
- Baseline control pass: 3/3
- Adversarial cases: 11
  - Failed or incorrect: 11/11

## Failure Ranking (Step 12)

### Critical

1. Ambiguity not detected with confident wrong resolution:
   - `capital of georgia` resolved to Georgia (U.S. state), not country, with `ambiguous=false`.
   - `population of washington` resolved to Washington state with `ambiguous=false`.
2. Why critical:
   - Returns plausible but potentially wrong answers without warning.
   - Highest correctness risk for end users.

### Major

1. Typos fail hard:
   - `poplation of japen`, `capitol of caneda`.
2. Mixed-language phrasing unsupported:
   - `capital de canada`, `poblacion of japan`.
3. Contradiction/validation checks absent:
   - `smallest cities by highest population`.
   - `capital of japan in europe`.
4. Why major:
   - Common real-world inputs fail even when user intent is recoverable.

### Minor

1. Underspecified or unsupported logic falls back poorly:
   - `biggest cities`
   - `countries with high gdp`
   - `countries with higher population than france but lower gdp than japan`
2. Why minor:
   - These are outside the initial baseline scope, but error handling could be more helpful.

## Stage-Level Failure Mapping

- Intent parsing failures: mixed-language, underspecified, unsupported comparative logic.
- Parser validation failures: contradictory qualifiers embedded in entity text.
- Entity resolution failures: ambiguity not surfaced.
- Query execution stage: stable for in-scope intents.

## Key Takeaways

1. Baseline execution works for narrow in-scope templates and live query execution.
2. The most important risk is silent ambiguity, not crashes.
3. Hardening should prioritize:
   - ambiguity detection + clarification,
   - typo tolerance,
   - contradiction checks,
   - explicit unsupported-intent messaging.

## Repro Commands

```bash
python wikidata_cli.py "capital of georgia" --json
python wikidata_cli.py "population of washington" --json
python wikidata_cli.py "poplation of japen" --json
python wikidata_cli.py "capital de canada" --json
python wikidata_cli.py "smallest cities by highest population" --json
python wikidata_cli.py "countries with higher population than france but lower gdp than japan" --json
```
