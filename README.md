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

## Known baseline limitations (to be hardened in next step)

- Mostly English phrasing patterns
- Ambiguity is only signaled, not interactively clarified
- No typo correction
- No multi-constraint parsing (e.g., "capital and population of ...")
- No confidence score or clarification loop
