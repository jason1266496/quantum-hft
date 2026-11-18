# HFT Input Data Contract

版本：1.0（規格，尚未實作）。來源只允許 `/home/jason/hft-realtime-codex/results` 的九個已登錄輸入；本次沒有重新掃描市場資料。身份、SHA-256、size、audit status 與時間範圍必須從 [data_sources.json](/home/jason/quantum-hft/configs/data_sources.json) 及其證據取得。

## 1. 已證實可用

| 項目 | 已證實範圍 | 證據 |
| --- | --- | --- |
| CSV 欄位 | 五檔均有 local_timestamp_us、event_time_ms、update_id、best_bid、best_ask、mid_price、spread、bid_volume_5、ask_volume_5、obi_5 | [Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33) |
| CSV 品質 | 共 269,416 列；本次引用的 v2 Audit 解析、數值、mid/spread/OBI 一致性檢查通過，五檔仍 WARNING | [v2 報告第 15–17 節](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:108) |
| CSV event time | 五檔各自嚴格遞增，缺失／非法時間為零；可按獨立研究 Session 離線排序 | [Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67) |
| CSV 時間間隔 | 最大檔內 event interval 為 241ms；13.327507 秒是 local 間隔，不是同等長度市場資料缺口 | [Timestamp Review 檔內與跨檔間隔](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:139) |
| Snapshot／Replay 格式與銜接 | 兩組 Snapshot＋Replay 有效、初始銜接 PASS；Replay 1,000／50,000 事件的 gap、duplicate、backward 檢查皆為 0 | [Phase 1 v2 Snapshot／Replay 配對](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:148)；[v2 Replay 檢查](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:125) |

上述是既有稽核的範圍，不等於新專案已驗證市場真實性、完整 Book 狀態或策略效益。[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63)

## 2. 可由現有資料計算

| 衍生項目 | 計算與依賴 | 狀態及限制 |
| --- | --- | --- |
| mid_price | (best_bid + best_ask) / 2 | 可重算；現有 CSV 已保存，仍需 Phase 2 adapter 驗證數值精度 |
| spread | best_ask − best_bid | 可重算；crossed 或非法 Book 不能產生有效標籤 |
| OBI 前五檔總量比例 | (bid_volume_5 − ask_volume_5) / (bid_volume_5 + ask_volume_5) | 分母零時依既有規則取 0，需在 feature schema 記錄規則 |
| 未來報酬 | mid_price(t_target) / mid_price(t_source) − 1 | 待 Phase 2；100／200／500／1000ms，按 event time 配對，不得跨檔或 Session |
| Replay Book | 合法 Snapshot 初始化後，依銜接且完整的 Replay 更新價位 | 條件可行；僅限保存 Snapshot 涵蓋且更新可知的錄製範圍，不能保證全交易所無限深度 |

公式與格式來源：[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50)。Snapshot＋Replay 可以作為錄製期間 Order Book 重建的輸入，但本交接尚未重建；初始 Snapshot 範圍外未更新價位仍不可知，前五檔充足性與完整可知 Book 狀態必須由 Phase 2B 驗證。銜接 PASS 不取代重建測試或第二個獨立參考實作。[Phase 1 v2 Snapshot／Replay 配對](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:148)、[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63)

## 3. 缺失或證據不足

| 項目 | 狀態 | 證據邊界 |
| --- | --- | --- |
| CSV 每側逐檔五組價格／數量 | NOT_AVAILABLE | 十欄 schema 只有 best bid/ask 及五檔總量，不能逆推出逐檔分布；[Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33) |
| 真實 Local Receive Time | NOT_AVAILABLE | 現存來源在 Book 更新後取時；歷史 CSV exact producer 為 UNKNOWN，不得當成 receive；[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214) |
| 真實 collector session_id、producer binary/source identity | NOT_AVAILABLE | 檔案研究 Session 是隔離識別，不等同已知連線生命週期；[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)、[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214) |
| 原始 WebSocket JSON 逐字紀錄 | NOT_AVAILABLE | 此九來源提供 CSV 摘要及 normalized Replay（eventTime／firstUpdateId／finalUpdateId／bids／asks）與 Snapshot，沒有建立逐字 wire payload 保存證據；不能宣稱能還原原始 WebSocket bytes。[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50) |
| 網路、parse、queue、Book、decision 各階段延遲 | NOT_AVAILABLE | CSV 只有晚期 local 採樣與 exchange time，沒有完整同一事件階段端點；[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214) |
| Testnet ACK 對應實際成交 | NOT_AVAILABLE | Testnet ACK 不等於成交；此九來源稽核不含成交回報／fill verification，不能拿 ACK 推論成交品質。[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63) |
| Live Paper Broker | NOT_AVAILABLE | 現有歷史回測不等於 Live Paper Broker；本交接的稽核沒有驗證 broker 狀態機、持倉、成交、重連或風控。[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63) |
| CPU isolation 完整驗證 | NOT_AVAILABLE | CPU affinity 不等於 CPU isolation；v2 environment 明列隔離未完整驗證。[Phase 1 v2 環境限制](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:50) |

「沒有逐字保存」只限本契約九個已登錄來源的可用證據，不推論未檢視檔案一概不存在。歷史 Testnet 或交易曾否發生也不能由本次無交易倒推；Recovery 保留相關 UNVERIFIED CLAIM。[Recovery 歷史活動限制](/home/jason/hft-realtime-codex/docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md:315)

## 4. 禁止使用

- 不得修改 HFT 輸入或寫回 results，不得複製原始資料到 quantum-hft。
- 不得將 `local_timestamp_us` 當成可靠 Local Receive Time，或用於網路延遲、Tick-to-Trade、第一版模型特徵；禁止將負差解讀成負網路延遲。[Timestamp Review 警告定義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:35)、[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214)
- 不得用 CSV 捏造逐檔價量、深度斜率或 Level 1 microprice；總量不能識別各 level。
- 不得跨檔或跨 Session 建立標籤。四個日期為 20260827 的 CSV 在 8 月，Replay eventTime 在 9 月；`obi_market_data.csv` 的 event 範圍實為 10 月，亦獨立。檔名或相同商品不構成同 Session 證據。[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)；[Replay 1000 稽核時間](/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json:129)；[Replay 50000 稽核](/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.json:129)
- 跨檔 event interval 不具備檔內市場資料缺口的意義。各檔間未涵蓋期間不得插值、補造或跨越建標籤。[Timestamp Review 檔內與跨檔間隔](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:139)
- raw epoch 不默認是模型預測變數；event time 第一版只作排序、切分與對齊 metadata。
- 不得用 Final Holdout 決定 split、gap、match error、特徵、成本或策略參數。

## 5. 尚待 Phase 2 驗證

1. Adapter 唯讀開啟、拒絕寫回與路徑跳轉、SHA 不符中止；audit status WARNING 的可用範圍要保留。
2. Snapshot 檔本身若無 event time，不得把 Replay 首時間寫成 Snapshot 原生時間；研究 pair_id 與 collector session_id 分開。
3. Book 初始化、過期事件跳過、首有效事件銜接、quantity=0 刪除、quantity>0 覆寫、gap／重複／倒退隔離。
4. 每步完整可知 Book 狀態與第二個獨立參考實作比較，不只驗 best bid/ask 或終態摘要；前五檔不足、crossed 或空側都要標示。
5. 價量採可重現的精確十進位或明確 tick/lot 轉換政策，不能不加說明沿用浮點誤差。
6. 每個 horizon 保存 requested_horizon_ms、actual_horizon_ms、target_event_time_ms、match_error_ms、valid_label、invalid_reason。
7. 配對候選為同 Session／segment 第一個 event time >= source_time + requested_horizon；actual horizon 為兩 event time 差，match error 為 actual − requested。缺目標、跨 gap、尾端不足、非法 Book 或超標全部無效，不能填 0 假裝有效報酬。
8. max_match_error_ms 與 gap 閾值尚未定案；只用 Training profile 及人工審核研究 protocol 選定後凍結。舊 Timestamp Review 的 25ms／200ms 僅提案，不是本契約 final 值。
9. 時間切分、Training-only scaler、重疊標籤 purge、Final Holdout 隔離與資料集版本 manifest。

以上是驗收要求，並無實作或測試結果。本次不進行 Phase 2。
