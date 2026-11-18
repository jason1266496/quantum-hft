# Data Pipeline

狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 2。

職責：唯讀 Adapter、Dataset Registry、兩套獨立 Book 重建參考、Feature Builder、Label Builder、時間切分及版本化資料集。

限制：不得寫回 HFT；禁止跨檔／Session labels、local timestamp 特徵與未經核准 gap／match error 門檻。

未來驗收：人工事件逐步完整 Book 對照、來源 SHA、標籤有效性、purge 與 feature lineage。

共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。
