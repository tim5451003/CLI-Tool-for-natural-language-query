# Part 1 - Human-Engineered NL2SPARQL Baseline

這份 README 對應的是我在 Part 1 的工程反思：我沒有把它做成「一個聰明但不透明的黑盒」，而是做成一條可檢查、可回放、可失敗得很誠實的 pipeline。

核心邏輯是：

1. 先把自然語言壓成可執行意圖（intent + slots）
2. 再做 entity resolution（而不是反過來猜）
3. 再用模板化 SPARQL 生成與執行
4. 最後把系統不確定的地方，明確地回傳給人，而不是硬猜

---

## Engineering Logic Reflection

我在這題的取捨是「穩定正確 > 華麗泛化」：

- **可追溯性優先**：每一步都可 log（解析、候選、查詢、結果）
- **可控失敗優先**：遇到 ambiguity、contradiction、underspecified 時回傳明確狀態
- **規則先行，不盲目 overfit**：先用可解釋規則打底，再逐步補 typo/multilingual hardening

這種做法的代價是天花板不會像大型端到端模型那麼高；但優點是每個錯誤都能定位、修正、驗證。

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

快速測試：

```bash
python wikidata_cli.py "capital of canada"
```

---

## Usage

```bash
python wikidata_cli.py "what is the capital of japan"
python wikidata_cli.py "population of taiwan"
python wikidata_cli.py "who is the head of state of france"
python wikidata_cli.py "top 10 cities in germany by population" --show-intent
python wikidata_cli.py "cities in japan" --json
```

---

## Module Map

- `cli.py`: CLI 主流程與參數入口
- `parser.py`: 自然語言解析（NL -> ParsedQuery）
- `intents.py`: intent 與 schema 常數定義
- `resolver.py`: entity resolution
- `sparql_builder.py`: SPARQL 模板組裝
- `wikidata_client.py`: SPARQL 執行與資料正規化
- `formatter.py`: CLI 輸出格式
- `logging_utils.py`: JSONL trace logging
- `wikidata_cli.py`: 相容入口（呼叫 `cli.main()`）
- `normalize_nl.py`: typo / multilingual normalize
- `contradictions.py`: 矛盾輸入檢查
- `scope_checks.py`: 超出 baseline 範圍檢查

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Network or unexpected error |
| 2 | Out of scope / unresolved entity |
| 3 | Needs disambiguation |
| 4 | Contradiction detected |

---

## What Part 1 Handles Well

- 常見事實型查詢：`capital_of`, `population_of`, `head_of_state`
- 基本 list/ranking：`list_by_type_and_location`, `top_entities_by_property`
- 可控輸出：`--show-intent`, `--show-sparql`, `--json`
- 安全機制：遇到不確定時拒答或要求澄清，不製造看似合理的錯答案

---

## What Remains Fundamentally Hard

1. **Open-world ambiguity**：像 `Georgia`, `Washington` 需要額外語境
2. **Ontology mismatch**：人類詞彙（best/high/biggest）不等於可直接映射 property
3. **Compositional constraints**：比較式、多條件邏輯會快速增加模板複雜度
4. **Compounded uncertainty**：typo + multilingual + ambiguity 疊加時穩定度下降
5. **Temporal semantics**：`current` / `in 2010` 這類時間語意需額外建模

---

## Safety-First Principle

我在 Part 1 的原則是：

- 寧可明確說「需要澄清／不支援」
- 也不要給出語意上高風險但自信的錯誤答案

這個原則讓系統更像工程產品，而不是只追單次展示效果的 demo。

---

Part 2 的 README 內容會放在 `part2` 資料夾中。
