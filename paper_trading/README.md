# Local Paper Trading

狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 7。

職責：另獲批准後的本機模擬 Broker、持倉、現金、風控及策略生命週期。

限制：目前沒有 Paper Trading 實作或執行；不得連真實／Testnet 下單 API、不得使用 API／Secret Key。未經人工批准不得更新啟用中的模擬策略。

未來驗收：人工狀態機、重連／重複事件、風控與成交假設；任何未來行情連線須另經批准；真實 receive timestamp 與階段採樣先驗收。

共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。
