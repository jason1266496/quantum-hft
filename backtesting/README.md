# Backtesting

狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 3。

職責：未來統一事件順序、策略輸出、持倉、費用、滑價及成交假設的歷史回測。

限制：本次未回測；歷史回測不等同 Live Paper Broker；不得跨 Session 搬移持倉而無明確政策。

未來驗收：人工交易序列可手算的持倉／現金／費用／equity、成本後報酬、最大回撤與交易次數。

共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。
