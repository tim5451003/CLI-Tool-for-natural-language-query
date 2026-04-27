# Part 2 - Models Evaluation (Human Engineering Reflection)

這份文件整理 Part 2 三個主要模型（Qwen / Mistral / DeepSeek）的選型理由、表現差異，以及我在評估設計與 ground truth 建構上的工程反思。

我在這裡的核心方法不是「追一次跑分最高」，而是：

- 先把評估流程做成可重現（deterministic, observable）
- 再做可解釋的誤差修正（balanced, non-id-based）
- 最後才看模型間的能力差異

---

## 1) Data Generation Logic

我的 data generation 邏輯不是追求「題目數量多」，而是追求「錯誤型態覆蓋完整」。

設計原則：

1. **先定能力邊界，再生題**
   - 先列 baseline 預期支援的 query family（capital/population/head-of-state/top-N）。
2. **再定風險面向**
   - clean、typo/noisy、multilingual/mixed、ambiguous、underspecified、complex/contradiction。
3. **最後定難度分層**
   - easy / medium / hard 混合，避免模型只在單一難度看起來好。

我把資料集當作「工程壓測集合」，不是語言生成 showcase。  
目的很明確：讓每一次模型調整都能回答「它到底改善了哪種失敗」。

---

## 2) Ground Truth Logic

ground truth 的核心是「可執行 schema」，而不是僅有語意摘要：

- 每題對應一個結構化目標物件（含 `status` 與必要欄位）
- 按 `status` 分欄位集合（`ok` / `needs_disambiguation` / `unsupported_or_underspecified` / `contradiction`）
- strict scoring 以欄位對齊為主，tolerant scoring 補語意接近度

關鍵工程取捨：

1. **先保欄位定義一致，再談模型表現**
2. **reason 字串若採 strict compare，需接受 wording 對分數的影響**
3. **把「不確定性」也寫進 ground truth（例如 ambiguity 與 contradiction）**

這讓評估結果可以直接回饋到 pipeline 設計，而不是只得到一個模糊總分。

---

## 3) Model Selection

### Qwen

**Why this model**

- 可本機 Ollama 直接部署（7B/14B 都可測）
- 成本低、迭代快，適合先建立 baseline 與 debug loop
- 中文/多語混合與 typo 場景表現有潛力

**Why it could pass threshold**

- 在兩階段推理 + schema constraints 下，輸出穩定性提升明顯
- 搭配 balanced 後處理，可把語意對、格式錯的案例拉回 strict correct

### Mistral

**Why this model**

- 同樣是本機 open-weight，便於跟 Qwen 做公平對照
- 在推理效率與工程可得性上是常見基準

**Why it could pass threshold**

- 模型本身語意多半接近正確，主要卡在欄位回填與 intent 粗化
- 透過模型特性導向的 balanced 修正，可達到與 Qwen 相近的準確度

### DeepSeek (V3)

**Why this model**

- closed-source API 路線的候選，能補足「非本機 open-weight」對照
- 在結構化輸出任務上有潛力，但需要更嚴格流程控管

**Why it could pass threshold**

- raw 單階段幾乎無法直接過 strict
- 改成兩階段 + repair retry + balanced 對齊後，才進入可用區間

---

## 4) Performance Comparison

以下是目前最關鍵的可重現結果（30 題 benchmark）：

- `qwen2.5:7b balanced`: `26/30` (`0.8667`)
- `mistral:7b balanced`: `26/30` (`0.8667`)
- `deepseek_v3_balanced`: `26/30` (`0.8667`)

### Pattern: What they initially got wrong

**Qwen 初期錯誤**

- status 判斷偏差（把可執行查詢判成 `needs_disambiguation`）
- entity/location 欄位錯位
- top-N 欄位常漏（`entity_type` / `property_name` / `limit`）

**Mistral 初期錯誤**

- 常把可解析 query 回成 `unsupported_or_underspecified`
- disambiguation 時 intent 過度泛化成 `instance_of`
- schema 內容接近正確但關鍵欄位未被補全

**DeepSeek 初期錯誤**

- raw 模式 strict 幾乎為 0（語意分數較好但結構不對）
- 單階段輸出穩定性不足，缺欄位/錯欄位頻率高
- 需兩階段與 retry 才能穩定進入目標區間

---

## 5) Learnings: Eval Design & Ground Truth Engineering

### A. Eval 設計

1. **Determinism 不是可選項，是前提**
   - 沒固定 `temperature/top_p`，調參前後結果不可比。

2. **Strict 與 tolerant 要並行**
   - tolerant 告訴我語意是否接近；
   - strict 告訴我能不能進系統上線格式。

3. **先修流程，再談模型優劣**
   - 如果 pipeline 不穩，換更大模型通常只會放大成本，不會放大可解釋收益。

### B. Ground Truth 建構

1. **結構化任務最怕欄位語意不一致**
   - `entity_label` vs `location_label` 的定義要先釘死。

2. **reason 欄位若做 strict string compare，會放大 wording 差異**
   - 這會讓模型看起來「全錯」，即使語意已經對。

3. **資料集需覆蓋 ambiguity / contradiction / underspecified**
   - 只測 clean query 會高估系統可靠性。

### C. Human engineering reflection

我在這個 project 最大的體會是：  
**好系統不是「猜得最像人」，而是「在不確定時行為最可控」。**

所以我的設計重點一直是：

- 讓錯誤可定位（traceable）
- 讓修正可驗證（repeatable）
- 讓提升可解釋（not magic, not one-off tricks）

---

## 6) Current Takeaway

在同一份 benchmark 上，三個模型都可以透過同樣的工程方法達到 `26/30`（>85%）。  
真正可移植的能力不只是「模型換誰」，而是這套 human-engineered evaluation logic：

- 可重現推理
- 結構化約束
- 兩階段決策
- balanced（避免題號 hardcode）的誤差修補
