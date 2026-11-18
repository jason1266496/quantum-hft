# Phase 2：統一 Order Book、特徵、標籤與版本化資料集

狀態：SPECIFICATION_ONLY／NOT_IMPLEMENTED。這份文件只定義待批准的開發與驗收順序。本次不讀原始市場資料、不重建 Book、不產生特徵或標籤、不訓練模型、不回測、不啟動 Paper Trading。

依據：Phase 1 v2 PASS 與 Timestamp Review WARNING／PASS_WITH_RESTRICTIONS。[Phase 1 v2 正式報告](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:3)；[Timestamp 決策](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:3)。資料契約是 [HFT_INPUT_DATA_CONTRACT.md](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)。

## Phase 2A：Read-only Data Adapter 與 Dataset Registry

工作：讀取已登錄 CSV、Snapshot、Replay JSONL，所有 HFT 輸入唯讀開啟，SHA-256／size 與登錄值完全相同才接受。每個 CSV 使用獨立 research_session_id；兩組 Snapshot／Replay 各用明示 pair_id，真實 collector session_id 不明時標 UNKNOWN。不得跨 Session，不寫回 HFT results。

輸出：版本化來源登錄、schema、唯讀讀取結果及錯誤報告，只放 quantum-hft 新 run。驗收：人工小檔覆蓋缺檔、hash 錯、非法欄位、symlink/path escape、唯讀來源、非空輸出拒覆寫；真實九來源只在 Phase 2 獲批後驗證。

依據：[Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33)、[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50)、[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)。

## Phase 2B：Order Book Reference Rebuilder

1. Snapshot 初始化已知 bid/ask 價位與 lastUpdateId。
2. 跳過 finalUpdateId <= lastUpdateId 的過期事件並記錄；首個有效事件必須滿足 firstUpdateId <= lastUpdateId + 1 <= finalUpdateId。
3. quantity=0 刪除價位；quantity>0 覆寫絕對數量，不是增量相加。負數、非有限、非法價格拒絕。
4. 依 high-water ID 偵測 gap、重複與倒退。不能靜默跳過 gap 後宣稱連續重建；失效區段及重新初始化策略須明記。
5. 輸出 Best Bid、Best Ask、前五檔價量與 Book 摘要；少於五檔、空側或 crossed book 明列無效，不補造。
6. 小型人工事件測試覆蓋 snapshot 初始化、過期事件、跨 snapshot event、插入／覆寫／刪除、未知價位刪除、價位排序、重複／倒退／gap。
7. 與第二個獨立參考實作逐事件比較完整可知 Book 狀態，含所有側別價位／數量／lastUpdateId；不能只比較 top-5 或共用同一 applyEvent 核心。
8. 記錄初始 Snapshot 深度涵蓋限制；全交易所簿的未知價位不能被叫作完整重建。

驗收前只稱「Snapshot＋Replay 條件可重建」。既有配對 PASS 僅證明 payload／序列銜接，未在新專案執行 Book 重建。[Phase 1 v2 Snapshot／Replay 配對](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:148)、[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63)

## Phase 2C：Feature Builder

第一版保存 best_bid、best_ask、mid_price、spread、bid_volume_5、ask_volume_5、obi_5 與 event_time_ms。前七項是數值特徵候選；event_time_ms 是排序／對齊／切分 metadata，不默認將 raw epoch 輸入模型。local_timestamp_us 保留於診斷 provenance 時也不得加入特徵。

Replay 重建及 Phase 2B 驗收後，才可加入 bid_price_level_1 至 5、bid_quantity_level_1 至 5、ask_price_level_1 至 5、ask_quantity_level_1 至 5、level-wise imbalance、microprice、depth slope。每項寫清公式、缺值、分母零、價位不足及來源時間；microprice 必須用實際 Level 1 數量，不以五檔總量冒充。

驗收：人工已知 Book 手算對照、價差／OBI 重算一致、來源 row/event 可追溯、只用當時與過去資訊；不得為 CSV 捏造不存在的逐檔價量。[Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33)、[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50)、[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214)

## Phase 2D：Label Builder

候選標籤為 future_return_100ms、future_return_200ms、future_return_500ms、future_return_1000ms；每筆報酬為目標有效 mid／來源有效 mid − 1。

每筆保存 requested_horizon_ms、actual_horizon_ms、target_event_time_ms、match_error_ms、valid_label、invalid_reason，另保存 source_event_time_ms、source/target row identity、research_session_id、segment_id。

在同 Session 與同有效 segment 中，選第一個 event time >= source time + requested horizon；match error = actual horizon − requested horizon。禁止跨檔／Session、禁止時間插值與未來回填。找不到未來價格、資料缺口、超過 match error、Session 尾端不足、crossed 或 invalid book 均排除並保留明確原因。

max_match_error_ms=null，selection_status=TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL；gap 閾值同樣未定案。不得把舊提案 25ms 或 200ms 當成 final 值。Training profile、候選政策與保留率分析完成並審核後凍結，再套 Validation／Test／Final Holdout。

驗收：人工不規則 event time、精確匹配、超標、gap、跨 Session、尾端、非法 Book；核算 actual horizon 與 match error；驗證每一無效原因有測試。實際有效標籤數目前 NOT_AVAILABLE。[Timestamp Review 檔內與跨檔間隔](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:139)、[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)

## Phase 2E：Time Split 與 Leakage Protection

按 event time 建立 Train、Validation、Test，另封存 Final Holdout；不隨機 shuffle。來源檔隔離不等於已經有正確時間切分，必須檢查跨資料來源日期與來源重疊。

Scaler 僅 Training fit；選參只用 Training 及事先宣告的 Validation。對 label 的實際 future endpoint 觸及後一 split 者 purge；feature lookback 若跨邊界也須遵循明確歷史可用規則。Final Holdout 不參與特徵、gap、match error、模型、成本或交易門檻搜尋。

保存每個 split 的起訖時間、row identity、來源 SHA-256、資料 SHA-256、purge 數量與原因；禁止依測試結果重選日期。驗收包含故意跨邊界重疊標籤、scaler 洩漏偵測與 holdout 使用審計。依據：[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)、[Timestamp Review 使用規則](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/phase2_time_rules.json)。

## Phase 2F：版本化資料集

只有 Phase 2A–2E 驗收後建立唯一 `/home/jason/quantum-hft/artifacts/datasets/<dataset_run_id>/`。必須拒絕覆寫既有 run；HFT inputs 仍只記唯讀路徑與 hash。

至少包含 dataset_manifest.json、source_files.json、feature_schema.json、label_schema.json、quality_report.json、train/、validation/、test/。Final Holdout 的封存位置、hash、存取紀錄另在 manifest 明記；不允許作日常調參輸入。

manifest 記錄程式版本／SHA、環境、參數、原始資料 SHA、schema、timestamp policy、split、invalid／purged 數量及執行命令。未實際產出的指標標 NOT_AVAILABLE，不預填 PASS。

## 完成驗收與停止點

完成需有唯讀與隔離證據、兩個獨立 Book 實作逐事件一致、人工及實際資料品質報告、特徵／標籤 lineage、時間切分無洩漏、版本資料集完整性與人工審核。任何一項未通過保留 FAIL／NOT_AVAILABLE，不推進下階段。

Phase 2 完成時仍不得訓練模型。後續 Phase 3 需另獲批准；本次骨架交接完成即停止。
