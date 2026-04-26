# Part 2 - Ollama Model 選用與調整紀錄

本文件記錄 Part 2 在本機 Ollama 模型上的選型、調整方式、評估結果與觀察。

## 1) 模型選用

本輪主要測試：

- `qwen2.5:7b`（主力）
- `qwen2.5:14b`（對照）

選用原因：

- 皆可本機推論，便於重複實驗。
- 同模型家族（7b/14b）可比較參數量提升帶來的差異。
- 能直接接到既有 `part2/eval/run_eval.py` 評估流程。

## 2) 訓練說明（Training / Fine-tuning）

本專案目前**沒有做模型再訓練或微調（fine-tuning）**，主要是：

- Prompt 設計調整
- 輸出結構約束
- 推論流程調整（兩階段）
- 輕量通用語意後處理（非題號硬編碼）

也就是「inference-time optimization」，不是 weight update。

## 3) 主要調整策略

### (A) 可重現性

- Ollama options 固定：`temperature=0`, `top_p=1`
- 目的：降低 run-to-run 浮動，讓結果可比較。

### (B) 結構化輸出約束

- 要求模型只輸出單一 JSON 物件。
- 依 `status` 強制欄位集合與型別（例如 `limit` 必須可轉整數）。

### (C) 兩階段推理

1. 先判斷 `status / intent / normalized_query`
2. 再填入完整 schema 欄位

相較一次生成整包 JSON，穩定度較高。

### (D) 一次自動修復重試

- 若第一次輸出 schema 不合法，回傳錯誤摘要後重生 1 次。

### (E) Balanced 路線（避免 overfitting）

- 不使用題號級硬編碼。
- 保留通用語意修正：
  - intent 同義詞映射
  - 常見欄位錯位修復（例如 `capital_of`）
  - top-N 查詢欄位補全（`entity_type`, `property_name`, `limit`）
  - ambiguity / contradiction / underspecified 的通用守門

## 4) 目前觀察到的結果

核心現象：

- `raw` 能反映模型原生能力，但 strict 偏低、格式和欄位容易漂移。
- `balanced` 可明顯提升 strict，且 schema failure 低。
- 只靠放大模型（7b -> 14b）不一定直接提升；輸出約束與後處理策略同樣關鍵。

在當前 benchmark（30 題）上，調整後可把 `7b_balanced` 控制在約 26/30（或更高），並可依需求避免追求 30/30 的過度對齊。

## 5) 學到的重點（Lessons Learned）

1. **可重現性先於準確率**
   - 沒有固定隨機性時，分數波動會掩蓋真實改動效果。

2. **格式錯誤是第一個瓶頸**
   - 很多 strict 掉分不是語意錯，而是 schema/欄位不穩。

3. **兩階段通常比單階段穩**
   - 先分類再填欄，能降低 JSON 欄位混亂。

4. **Balanced 比 hard-rule 更適合泛化**
   - hard-rule 可快速拉高分，但有 overfitting 風險。
   - balanced 在保留泛化前提下，仍可顯著改善。

5. **Reason 文案會影響 strict**
   - 若評分是字串完全比對，reason wording 差異會造成 strict 掉分。
   - 後續可考慮把 reason 的評分改成語意比對或模板級比對。

## 6) 下一步建議

- 建立 holdout 題集（不重複既有模板）驗證泛化。
- 併行回報 `raw / balanced / hard-rule` 三條曲線。
- 若要更公平比較模型能力，可加上多次重跑平均與標準差。
