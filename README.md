# Wikidata NL Query CLI (Baseline)

This project is a baseline implementation for the take-home assessment:

- Input: natural language question
- Conversion: structured request + SPARQL query
- Execution: query against Wikidata
- Output: returned rows from the actual API/database query

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Important:
- Always activate the virtual environment before installing dependencies and running commands.
- Run `pip install -r requirements.txt` inside the activated `.venv` so all required packages (including `rapidfuzz`) are available.

Quick smoke test after setup:

```bash
python wikidata_cli.py "capital of canada"
```

## Usage

```bash
python wikidata_cli.py "what is the capital of japan"
python wikidata_cli.py "population of taiwan"
python wikidata_cli.py "who is the head of state of france"
python wikidata_cli.py "top 10 cities in germany by population" --show-intent
python wikidata_cli.py "cities in japan" --json
python wikidata_cli.py "what is python" --json
```

## Module Map

- `cli.py`: 主流程與 CLI 參數
- `parser.py`: 自然語言解析（NL -> ParsedQuery）
- `intents.py`: `ParsedQuery` 與常數（entity/property 映射）
- `resolver.py`: Wikidata entity resolution
- `sparql_builder.py`: SPARQL 模板生成
- `wikidata_client.py`: SPARQL 執行與結果正規化
- `formatter.py`: CLI 輸出格式化
- `logging_utils.py`: JSON-lines logging 工具
- `wikidata_cli.py`: 相容入口（呼叫 `cli.main()`）
- `normalize_nl.py`: typo／少量多語片語正規化（Harden）
- `contradictions.py`: 輸入矛盾檢查（Harden）
- `scope_checks.py`: 範圍外或資訊不足問題的提示（Harden）

## Exit codes (after hardening)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Network or unexpected error |
| 2 | Entity not found, or question out of baseline scope |
| 3 | Disambiguation required (ambiguous entity) |
| 4 | Contradiction (internally inconsistent input) |

## What baseline supports now

- Intents:
  - `capital_of`
  - `population_of`
  - `head_of_state`
  - `list_by_type_and_location`
  - `top_entities_by_property`
  - fallback `instance_of`
- Entity resolution layer: alias normalization + API candidate search + simple ranking/ambiguity signal
- Template-based SPARQL generation per intent
- SPARQL execution via Wikidata Query Service
- CLI flags: `--show-intent`, `--show-sparql`, `--language`, `--json`
- JSON-lines logging in `wdq.log` (raw input, parsed intent, resolved entities, query, result)
- Human-readable output and JSON output

## Explain: Why remaining failures are fundamentally hard

This section explains the unresolved failure cases after hardening and why they are difficult in principle (not just missing engineering work).

1. **Open-world ambiguity is intrinsic (not fully eliminable)**  
   - Example: `Georgia` can mean a country or a U.S. state; `Washington` can refer to a state, D.C., people, or places.  
   - Even with better ranking, surface text often lacks enough information to select one meaning deterministically.  
   - Fundamental issue: user intent is under-specified relative to Wikidata's many valid entities sharing similar labels.

2. **Ontology mismatch between human language and Wikidata schema**  
   - Users ask with vague concepts like "best", "high GDP", or "biggest", while SPARQL templates need explicit property IDs, thresholds, sort directions, and scope.  
   - Fundamental issue: natural concepts do not always map 1:1 to a single Wikidata property or query operator.

3. **Compositional and comparative logic quickly exceeds template complexity**  
   - Example: "countries with higher population than France but lower GDP than Japan".  
   - This requires multi-entity binding, cross-property constraints, and careful semantic composition.  
   - Fundamental issue: rule templates scale poorly for deeply nested constraints without introducing many false parses.

4. **Multilingual + typo + ambiguity is a compounded uncertainty problem**  
   - Current hardening adds limited vocabulary normalization (e.g., `capital de`, `poblacion`) and typo correction.  
   - Full multilingual support would require broader lexical resources, morphology handling, and language-aware intent parsing.  
   - Fundamental issue: multiple uncertainty sources interact, so confidence drops non-linearly.

5. **Missing temporal/context dimensions**  
   - Questions like "current head of state", "historical capital", or "GDP in 2010" require explicit time semantics.  
   - Fundamental issue: user text often omits temporal qualifiers, but Wikidata facts can be time-dependent.

## What the system does safely for unresolved cases

- Returns explicit statuses instead of silent guessing:
  - `exit code 3`: `needs_disambiguation`
  - `exit code 2`: unsupported/underspecified scope
  - `exit code 4`: contradiction detected
- Logs normalized input, parse output, and resolution stages for traceability (`wdq.log`).
- Prefers "ask for clarification / reject safely" over confident wrong answers.
