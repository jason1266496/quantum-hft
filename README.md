# Quantum-HFT

這是獨立的 Quantum-HFT 研究專案，位置為 `/home/jason/quantum-hft`。HFT C++ 來源專案位於 `/home/jason/hft-realtime-codex`；所有 HFT 輸入唯讀。這次只建立專案骨架、Phase 1 證據交接、資料契約、後續開發規格與交接驗證工具。

Phase 1 v2（`20261018T210029Z`）為 PASS；Timestamp Review（`20261018T212122Z`）為 WARNING，資料決策為 PASS_WITH_RESTRICTIONS。Phase 2 可在限制條件及人工批准下開發，尚未開始。證據：[Phase 1 v2 正式報告](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:3)、[Timestamp Review 決策](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:3)。

`local_timestamp_us` 不得用作網路延遲、Tick-to-Trade 或第一版模型特徵。歷史 exact producer 未證實，不能將該欄當真實 receive time。[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214)

本專案尚未建立模型、進行量子實驗、執行回測或 Paper Trading；本次沒有 Testnet 或真實交易、專題網路連線或套件安裝。這些陳述只描述本專案與本次交接，不抹除來源專案歷史活動。[Recovery 歷史活動限制](/home/jason/hft-realtime-codex/docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md:315)

## 證據與規格

- [交接報告](/home/jason/quantum-hft/docs/PHASE1_HANDOFF_REPORT.md)
- [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)
- [Phase 2 計畫](/home/jason/quantum-hft/docs/PHASE2_PLAN.md)
- [實驗計畫](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)
- [資料來源登錄](/home/jason/quantum-hft/configs/data_sources.json)
- [時間政策](/home/jason/quantum-hft/configs/timestamp_policy.json)
- [交接 Manifest](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/HANDOFF_MANIFEST.json)

市場資料只保存來源唯讀路徑，不複製 CSV、JSONL、Snapshot、src 或 results。交接證據的 CSV 統計摘要是研究報告，不是市場逐筆 CSV。Recovery 的歷史 FAIL 必須原樣保留，後續複核另列，不能回溯覆寫。

## 驗證

在 `/home/jason/quantum-hft` 執行下列命令。環境變數避免生成 pycache；測試人工暫存資料只能放在本專案 tests 中。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_verify_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/verify_handoff.py --manifest reference/hft_phase1/20261018T214147Z/HANDOFF_MANIFEST.json
```

驗證工具不修改被檢查檔案。正常交接可以保留歷史資料 WARNING；FAIL 退出碼必須非零。實際 stdout、stderr、exit code 與結果見交接報告；README 不預填測試通過。

## 後續順序

1. Phase 2：唯讀 Adapter、Registry、獨立 Book 重建、特徵、標籤、時間切分、版本化資料集。
2. Phase 3：經典模型與統一成本回測。
3. Phase 4：Quantum Kernel 與 QSVC。
4. Phase 5：QUBO 與 QAOA。
5. Phase 6：自動策略搜尋、重新訓練、退化監測與人工審核。
6. Phase 7：另經批准的本機 Live Paper Trading。

目前沒有 Phase 2 Adapter、Rebuilder、Feature Builder 或 Label Builder 實作；各模組 README 只是職責和驗收規格。下一階段必須等待人工批准。
