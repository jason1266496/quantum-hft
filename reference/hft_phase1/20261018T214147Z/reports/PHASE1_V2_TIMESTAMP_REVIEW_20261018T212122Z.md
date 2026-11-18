# Phase 1.5 CSV 時間欄位審查

**Timestamp Review：WARNING。時間資料決策：PASS_WITH_RESTRICTIONS。**

負差定義與269,284筆來源已確認。event time支持受限離線排序與標籤；歷史local語義與時鐘根因未完全證實，不可作網路延遲。本次未進入Phase 2，等待人工審核。

## 1. 工作目錄與安全邊界

所有實際專題shell命令顯式指定workdir /home/jason/hft-realtime-codex、login=false。pwd與realpath完全相同，findmnt為Linux ext4；不使用應用程式的WindowsApps預設目錄作專題路徑。

保留資料夾 /home/jason/hft-realtime 與 /home/jason/hft-realtime-codex-incomplete-20261018T194544Z 未寫入。新增僅限本次run及此報告。開始前968/968 SHA一致；另在run建立前記錄1522既存葉節點（1483 regular、38 symlink、1 special），不展開symlink、不開啟FIFO。

[initial_integrity_check.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/initial_integrity_check.json)；[preexisting_inventory.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/preexisting_inventory.json)。

## 2. Review run_id與方法環境

run_id：20261018T212122Z；來源Phase 1 v2：20261018T210029Z。Python 3.14.4；Linux 6.6.114.1-microsoft-standard-WSL2。Git commit：NOT AVAILABLE，本次未取得可驗證commit，以輸入與source SHA識別。不使用隨機性，seed不適用。

以Python標準函式庫逐列csv.reader讀取，只保存必要timestamp/delta整數向量、unique sets、統計及異常定位，未載入完整市場CSV表。分位數採精確Type 7，h=(n−1)p、排序後線性插值，Fraction保留exact分數；epoch相減用整數。record為不含header的1起算資料列，physical_line含header。

[timestamp_statistics.py](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_statistics.py)保存可重現分析方法。

## 3. CSV清單及SHA-256

| 代稱／檔案 | bytes | SHA-256 |
| --- | --- | --- |
| session1 / [results/obi_market_data_20260827_session1.csv](/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session1.csv) | 8019032 | 9931b0d9ef9be5dba36ea26cdd4d6d7fd1552a195af53460c59ffe415ceea8d3 |
| session2 / [results/obi_market_data_20260827_session2.csv](/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session2.csv) | 13226704 | 363e81f86de61a3acc697216082770f11a7158935c8745e172235ee6f9e1fd7c |
| session3 / [results/obi_market_data_20260827_session3.csv](/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session3.csv) | 7691375 | 72decc3d89cf833f6327bb11dfe66f3a9371fb932df290b54f7b5250d1a4e1b4 |
| test / [results/obi_market_data_test_20260827.csv](/home/jason/hft-realtime-codex/results/obi_market_data_test_20260827.csv) | 126181 | aa9bb47e598aaa024640c079654ed17da1e70552ed06632361dc4cb607b8171f |
| obi_market_data / [results/obi_market_data.csv](/home/jason/hft-realtime-codex/results/obi_market_data.csv) | 6683124 | e71676d8d2d6c04e6cf9b4f80ef3eb113de78a92eff8a280fd633541ac8231e7 |

欄位均為：local_timestamp_us, event_time_ms, update_id, best_bid, best_ask, mid_price, spread, bid_volume_5, ask_volume_5, obi_5。日期檔名不是時間戳證據。

## 4. 警告精確定義

[dataset_audit.py::audit_csv](/home/jason/hft-realtime-codex/tools/dataset_audit.py:329)第329–336行：offset_ms = Decimal(local_timestamp_us) / 1000 − event_time_ms；offset_ms < 0才記local_event_clock_order / WARNING。

本次等價整數公式：delta_us = local_timestamp_us − event_time_ms × 1000；delta_us < 0，單位µs。Audit把µs除1000轉ms，本次把ms乘1000轉µs；沒有epsilon。兩timestamp有效且列可解析才能比較，missing/invalid不當成非負；本次全列符合。

這不是網路延遲、處理耗時或獨立clock offset量測。schema、logger、Audit JSON/Markdown/errors.csv證據：[warning_definition.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/warning_definition.json)。

## 5. 269,284筆來源

| 檔案 | 列數 | 負差WARNING | 零差 | 正差 | 負差比例 |
| --- | --- | --- | --- | --- | --- |
| session1 | 60558 | 60558 | 0 | 0 | 100.000000% |
| session2 | 99871 | 99871 | 0 | 0 | 100.000000% |
| session3 | 58037 | 57905 | 0 | 132 | 99.772559% |
| test | 951 | 951 | 0 | 0 | 100.000000% |
| obi_market_data | 49999 | 49999 | 0 | 0 | 100.000000% |

269,284是五檔同一check合計，總列269,416；不是單檔或多種warning混合。五份errors.csv全串流核對JSON各check與Markdown，未混入其他錯誤類別。session3其餘132列正差、全體零差0。各稽核路徑與JSON/errors位置見[warning_definition.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/warning_definition.json)。

## 6. 逐檔時間統計

| 檔案 | total/parseable | parse error | event首/末 ms | local首/末 µs |
| --- | --- | --- | --- | --- |
| session1 | 60558/60558 | 0 | 1787767099114 / 1787773157814 | 1787767099004356 / 1787773157660177 |
| session2 | 99871/99871 | 0 | 1787773384514 / 1787783377014 | 1787773384358777 / 1787783372472319 |
| session3 | 58037/58037 | 0 | 1787808550014 / 1787814356615 | 1787808549721624 / 1787814356279986 |
| test | 951/951 | 0 | 1787765781314 / 1787765876414 | 1787765781213756 / 1787765876313057 |
| obi_market_data | 49999/49999 | 0 | 1791238160414 / 1791243186114 | 1791238160061328 / 1791243185740672 |

所有檔案missing/invalid timestamp皆0（row及cell皆0）。完整定義與數據見[csv_timestamp_summary.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/csv_timestamp_summary.json)、[csv_timestamp_summary.csv](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/csv_timestamp_summary.csv)。parseable只驗指定schema與數值語法，不代表獨立驗證交易所行情真實性。

## 7. Event單調性與研究Session範圍

| 檔案 | 單調不減 | 倒退 | 非首次重複 | event UTC首 | event UTC末 |
| --- | --- | --- | --- | --- | --- |
| session1 | True | 0 | 0 | 2026-08-26T17:58:19.114000Z | 2026-08-26T19:39:17.814000Z |
| session2 | True | 0 | 0 | 2026-08-26T19:43:04.514000Z | 2026-08-26T22:29:37.014000Z |
| session3 | True | 0 | 0 | 2026-08-27T05:29:10.014000Z | 2026-08-27T07:05:56.615000Z |
| test | True | 0 | 0 | 2026-08-26T17:36:21.314000Z | 2026-08-26T17:37:56.414000Z |
| obi_market_data | True | 0 | 0 | 2026-10-05T22:09:20.414000Z | 2026-10-05T23:33:06.114000Z |

五檔嚴格遞增、彼此範圍不重疊。每檔視作獨立研究Session，但CSV沒有真實session_id，不能斷言每檔只含單次collector連線或沒有重新連線。UTC只供顯示，不改原始epoch。

## 8. Local單調性

| 檔案 | 單調不減 | 倒退 | 非首次重複 | 相鄰重複 | local UTC首 | local UTC末 |
| --- | --- | --- | --- | --- | --- | --- |
| session1 | True | 0 | 0 | 0 | 2026-08-26T17:58:19.004356Z | 2026-08-26T19:39:17.660177Z |
| session2 | True | 0 | 5 | 5 | 2026-08-26T19:43:04.358777Z | 2026-08-26T22:29:32.472319Z |
| session3 | True | 0 | 19 | 19 | 2026-08-27T05:29:09.721624Z | 2026-08-27T07:05:56.279986Z |
| test | True | 0 | 0 | 0 | 2026-08-26T17:36:21.213756Z | 2026-08-26T17:37:56.313057Z |
| obi_market_data | True | 0 | 0 | 0 | 2026-10-05T22:09:20.061328Z | 2026-10-05T23:33:05.740672Z |

session2有5次、session3有19次重複；本資料非首次與相鄰重複計數相同。單調不減不證明receive邊界正確或system_clock未被調整。

## 9. Delta統計

下表單位µs；均值展示6位小數，exact有理數保留JSON。

| 檔案 | min | max | mean | median/p50 |
| --- | --- | --- | --- | --- |
| session1 | -155713 | -31951 | -131558.046666 | -131382.5 |
| session2 | -4541681 | -47570 | -193569.743579 | -192442 |
| session3 | -337505 | 12901877 | -297667.892534 | -313138 |
| test | -102803 | -53977 | -100658.541535 | -100753 |
| obi_market_data | -375662 | -304107 | -363639.544571 | -363913 |

| 檔案 | p1 | p5 | p25 | p50 | p75 | p95 | p99 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| session1 | -153655 | -151456.3 | -142621.75 | -131382.5 | -120483 | -112295.55 | -110071.57 |
| session2 | -229683.3 | -227023 | -211389.5 | -192442 | -173734 | -159491.5 | -156618.7 |
| session3 | -335403.64 | -333176 | -324208 | -313138 | -302178 | -293408.8 | -291694.08 |
| test | -101665.5 | -101510 | -101108 | -100753 | -100409.5 | -99786.5 | -98907 |
| obi_market_data | -373736.02 | -372558 | -368726 | -363913 | -358599 | -354361.9 | -352631 |

| 檔案 | 首/末負差record | 最大正向delta跳變 µs（record） | 最大負向delta跳變 µs（record） |
| --- | --- | --- | --- |
| session1 | 1 / 60558 | 101441 (33320→33321) | -100988 (33425→33426) |
| session2 | 1 / 99871 | 112365 (6582→6583) | -102000 (99839→99840) |
| session3 | 1 / 58037 | 13227507 (45032→45033) | -103999 (45085→45086) |
| test | 1 / 951 | 45723 (45→46) | -46275 (46→47) |
| obi_market_data | 1 / 49999 | 54212 (35650→35651) | -40202 (35681→35682) |

跳變=delta_after−delta_before，不是local interval。五檔首末列皆負差；完整定位、physical_line、分布：[clock_delta_statistics.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/clock_delta_statistics.json)。

## 10. 偏移、漂移與區段異常

四檔全列負值；session3為99.772559%負值，132筆正值連續位於record45033–45164後回負值。

| 檔案 | 首1000列block median µs | 末block median µs |
| --- | --- | --- |
| session1 | -110268 | -154171 |
| session2 | -156434.5 | -230184 |
| session3 | -292508 | -336352 |
| test | -100753 | -100753 |
| obi_market_data | -353229.5 | -373275 |

test只有951列、首末是同一block，不能由兩值相同斷言無漂移。其餘首末block中心向負值移動，不是每列單調漂移。session2 record99839→99871的event增加3200ms、local只增加291µs，末列delta=−4,541,681µs。

session3 record45032→45033：local增加13,327,507µs（13.327507秒）、event只增加100ms、delta跳增13,227,507µs。之後132筆正差回落。這是欄位進度/採樣異常，不能直接確認系統時鐘跳動。EventQueue加消費端取時允許停頓/追趕表徵，但僅為候選機制，歷史具體原因UNKNOWN。

較晚採樣通常增加delta，LOCAL_TIMESTAMP_NOT_RECEIVE_TIME本身不能解釋負號。沒有歷史NTP/WSL或成對monotonic證據。session3全體OLS受正差影響，不得當硬體clock drift。必要37筆視窗及trend：[timestamp_anomaly_examples.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_anomaly_examples.json)。

## 11. 時間間隔、缺口及跨檔範圍

| 檔案 | 欄位 | 數值單位 | min | max | median | 0 | <0 | >100ms | >200ms | >500ms | >1000ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| session1 | event_intervals | ms | 63 | 208 | 100 | 0 | 0 | 3622 | 3 | 0 | 0 |
| session1 | local_intervals | µs | 9 | 210127 | 99989 | 0 | 0 | 29892 | 14 | 0 | 0 |
| session2 | event_intervals | ms | 62 | 201 | 100 | 0 | 0 | 5574 | 2 | 0 | 0 |
| session2 | local_intervals | µs | 0 | 212365 | 99988 | 5 | 0 | 49249 | 32 | 0 | 0 |
| session3 | event_intervals | ms | 1 | 241 | 100 | 0 | 0 | 2843 | 4 | 0 | 0 |
| session3 | local_intervals | µs | 0 | 13327507 | 99990 | 19 | 0 | 28691 | 21 | 1 | 1 |
| test | event_intervals | ms | 94 | 200 | 100 | 0 | 0 | 37 | 0 | 0 | 0 |
| test | local_intervals | µs | 53725 | 199957 | 99995 | 0 | 0 | 470 | 0 | 0 | 0 |
| obi_market_data | event_intervals | ms | 68 | 202 | 100 | 0 | 0 | 3621 | 24 | 0 | 0 |
| obi_market_data | local_intervals | µs | 59798 | 203784 | 100001 | 0 | 0 | 25009 | 134 | 0 | 0 |

門檻欄均以ms語義換算，local原值是µs。event median均100ms，但不是嚴格固定粒度，session3最短1ms。

| 檔案 | interval數 | 恰100ms筆數 | 恰100ms比例 | 95–105ms比例 |
| --- | --- | --- | --- | --- |
| session1 | 60557 | 53347 | 88.094% | 99.666% |
| session2 | 99870 | 88777 | 88.893% | 99.711% |
| session3 | 58036 | 52377 | 90.249% | 99.714% |
| test | 950 | 876 | 92.211% | 99.684% |
| obi_market_data | 49998 | 42997 | 85.997% | 99.408% |

最大檔內event gap為**241ms**，session3 record8446→8447（physical_line8447→8448），event1787809395014→1787809395255。

| 檔案 | max event gap ms | record | physical_line | max local interval µs（record） |
| --- | --- | --- | --- | --- |
| session1 | 208 | 7499→7500 | 7500→7501 | 210127 (7499→7500) |
| session2 | 201 | 2739→2740 | 2740→2741 | 212365 (6582→6583) |
| session3 | 241 | 8446→8447 | 8447→8448 | 13327507 (45032→45033) |
| test | 200 | 248→249 | 249→250 | 199957 (248→249) |
| obi_market_data | 202 | 1766→1767 | 1767→1768 | 203784 (44509→44510) |

沒有event interval>500ms或>1000ms。13.327507秒是local採樣間隔，**不是13秒市場資料缺口**。統計以>1000ms作描述性分段，每檔一段；這不證明真實session。第20節另外提出更嚴格的>200ms標籤分段，尚未實作。

| 前檔→後檔 | 檔間event差 ms | 重疊 |
| --- | --- | --- |
| test→session1 | 1222700 | False |
| session1→session2 | 226700 | False |
| session2→session3 | 25173000 | False |
| session3→obi_market_data | 3423803799 | False |

跨檔最大差3,423,803,799ms是獨立Session間未涵蓋期間，不是檔內缺失列，禁止跨越建label。完整證據：[timestamp_gap_analysis.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_gap_analysis.json)。

## 12. 現存原始碼時間戳位置（只靜態讀取）

| 證據 | 檔案 | 函式 | 行號 |
| --- | --- | --- | --- |
| logger_schema | [csv_logger.h](/home/jason/hft-realtime-codex/src/csv_logger.h:89) | AsyncCsvLogger::AsyncCsvLogger | 89–116 |
| logger_write | [csv_logger.h](/home/jason/hft-realtime-codex/src/csv_logger.h:42) | AsyncCsvLogger::writerLoop | 42–84 |
| logger_queue | [csv_logger.h](/home/jason/hft-realtime-codex/src/csv_logger.h:135) | AsyncCsvLogger::push | 135–143 |
| row_fields | [csv_logger.h](/home/jason/hft-realtime-codex/src/csv_logger.h:13) | MarketSnapshot | 13–27 |
| event_parse | [orderbook_csv.cpp](/home/jason/hft-realtime-codex/src/orderbook_csv.cpp:399) | parseDepthEvent | 399–412 |
| base_websocket | [orderbook_csv.cpp](/home/jason/hft-realtime-codex/src/orderbook_csv.cpp:587) | websocketReader | 587–600 |
| base_dequeue | [orderbook_csv.cpp](/home/jason/hft-realtime-codex/src/orderbook_csv.cpp:783) | main | 783–786 |
| base_timestamp | [orderbook_csv.cpp](/home/jason/hft-realtime-codex/src/orderbook_csv.cpp:814) | main | 814–862 |
| base_depthevent | [orderbook_csv.cpp](/home/jason/hft-realtime-codex/src/orderbook_csv.cpp:52) | DepthEvent | 52–60 |
| baseline_receive_like_enqueue | [live_baseline_cpu19_50000.cpp](/home/jason/hft-realtime-codex/src/live_baseline_cpu19_50000.cpp:707) | websocketReader | 707–722 |
| baseline_book_obi | [live_baseline_cpu19_50000.cpp](/home/jason/hft-realtime-codex/src/live_baseline_cpu19_50000.cpp:979) | main | 979–1008 |
| baseline_strategy | [live_baseline_cpu19_50000.cpp](/home/jason/hft-realtime-codex/src/live_baseline_cpu19_50000.cpp:1018) | main | 1018–1036 |
| baseline_csv_timestamp | [live_baseline_cpu19_50000.cpp](/home/jason/hft-realtime-codex/src/live_baseline_cpu19_50000.cpp:1142) | main | 1142–1189 |
| realtime_receive | [realtime_latency_benchmark.cpp](/home/jason/hft-realtime-codex/src/realtime_latency_benchmark.cpp:711) | websocketReader | 711–736 |
| realtime_event_fields | [realtime_latency_benchmark.cpp](/home/jason/hft-realtime-codex/src/realtime_latency_benchmark.cpp:65) | DepthEvent | 65–75 |
| realtime_optional_order_before_csv | [realtime_latency_benchmark.cpp](/home/jason/hft-realtime-codex/src/realtime_latency_benchmark.cpp:1533) | main | 1533–1557 |
| realtime_receive_durations | [realtime_latency_benchmark.cpp](/home/jason/hft-realtime-codex/src/realtime_latency_benchmark.cpp:1596) | main | 1596–1623 |
| realtime_csv_timestamp | [realtime_latency_benchmark.cpp](/home/jason/hft-realtime-codex/src/realtime_latency_benchmark.cpp:2026) | main | 2026–2073 |

orderbook_csv：ws.read(591)→parse(597)→入列(600)→出列(785–786)→applyEvent(814)→system_clock取時(819–826)→best price/OBI(828–847)→MarketSnapshot/logger.push(849–862)。基本版本取時在Book更新後、OBI前。

live_baseline等候選版本取時更晚，在OBI/Strategy後；realtime_latency_benchmark存在條件式sendTickOrder/ACK先於CSV取時的路徑。僅靜態控制流程，不證明歷史執行交易或CSV來自該分支。

23條producer的SHA、main取時、snapshot參數及原文行號全部保存於[source_timestamp_semantics.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/source_timestamp_semantics.json)。

## 13. 欄位真正語義與UNKNOWN

event_time_ms：現存parseDepthEvent把JSON E存入DepthEvent::eventTime，傳MarketSnapshot第二欄，schema標ms。local_timestamp_us：現存23條路徑在Book更新後取system_clock::now().time_since_epoch()並duration_cast<microseconds>。logger.push只入列，writerLoop原值寫出、不重取timestamp；也不是落盤時間。

realtime來源雖於ws.read後取得localReceiveTimeMs/localReceiveSteady，這十欄CSV沒有保存它們。歷史五檔缺生成時binary/source hash及session metadata，exact producer=UNKNOWN；歷史欄位只能回答「真實receive time未證實，不得當作使用」。現存23條source則已確認不是receive。

E與本機system_clock是不同clock source；相同量級與正確單位不表示同步。當前路徑沒有explicit timezone轉換或epoch位移，C++17的system_clock型別亦不保證任意平台epoch。無單位錯配正面證據；system_clock有受校時影響可能，但歷史Windows/WSL、NTP、system_clock調整是否發生皆UNKNOWN。

舊[Phase 1 v2報告](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:137)第137行使用local_receive−exchange_event字樣，超出receive語義證據。本次更正解讀為local_timestamp_us−event_time_ms×1000；舊報告未修改。

## 14. 逐檔警告原因分類

| 檔案 | 主分類 | 條件式次分類 | 證據限制 |
| --- | --- | --- | --- |
| session1 | INSUFFICIENT_EVIDENCE | LOCAL_TIMESTAMP_NOT_RECEIVE_TIME（限現存source；歷史producer未證） | 缺歷史producer hash、clock sync紀錄及成對receive/monotonic欄，不能辨認clock offset、校時、queue或歷史版本。 |
| session2 | INSUFFICIENT_EVIDENCE | LOCAL_TIMESTAMP_NOT_RECEIVE_TIME（限現存source；歷史producer未證） | 缺歷史producer hash、clock sync紀錄及成對receive/monotonic欄，不能辨認clock offset、校時、queue或歷史版本。 |
| session3 | INSUFFICIENT_EVIDENCE | LOCAL_TIMESTAMP_NOT_RECEIVE_TIME（限現存source；歷史producer未證） | 缺歷史producer hash、clock sync紀錄及成對receive/monotonic欄，不能辨認clock offset、校時、queue或歷史版本。 |
| test | INSUFFICIENT_EVIDENCE | LOCAL_TIMESTAMP_NOT_RECEIVE_TIME（限現存source；歷史producer未證） | 缺歷史producer hash、clock sync紀錄及成對receive/monotonic欄，不能辨認clock offset、校時、queue或歷史版本。 |
| obi_market_data | INSUFFICIENT_EVIDENCE | LOCAL_TIMESTAMP_NOT_RECEIVE_TIME（限現存source；歷史producer未證） | 缺歷史producer hash、clock sync紀錄及成對receive/monotonic欄，不能辨認clock offset、校時、queue或歷史版本。 |

主分類回答負差根因，不是否定公式/計數。沒有足夠證據稱offset為EXPECTED或確認SYSTEM_CLOCK_NOT_SYNCHRONIZED。event/local倒退皆0；少量gap不解釋全檔負差；單位換算無錯配正面證據；不能只因負號判資料損壞。

[warning_cause_classification.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/warning_cause_classification.json)。

## 15. event_time_ms使用範圍

| 用途 | 狀態 | 原因／限制 |
| --- | --- | --- |
| 時間排序 | ALLOWED_WITH_RESTRICTIONS | 各檔/segment內依event與原始row排序；五檔嚴格遞增。不得以排序掩蓋新資料倒退。 |
| Session 切分 | ALLOWED_WITH_RESTRICTIONS | 以來源檔案及event gap建研究segment；真實collector session_id未保存，不能單靠時間復原。 |
| 100ms 標籤 | ALLOWED_WITH_RESTRICTIONS | 只配對同檔同segment第一筆event>=t+h；error<=25ms，保存actual horizon；缺口/尾端/價格無效即invalid。 |
| 200ms 標籤 | ALLOWED_WITH_RESTRICTIONS | 只配對同檔同segment第一筆event>=t+h；error<=25ms，保存actual horizon；缺口/尾端/價格無效即invalid。 |
| 500ms 標籤 | ALLOWED_WITH_RESTRICTIONS | 只配對同檔同segment第一筆event>=t+h；error<=25ms，保存actual horizon；缺口/尾端/價格無效即invalid。 |
| 1000ms 標籤 | ALLOWED_WITH_RESTRICTIONS | 只配對同檔同segment第一筆event>=t+h；error<=25ms，保存actual horizon；缺口/尾端/價格無效即invalid。 |
| Walk-forward 時間切分 | ALLOWED_WITH_RESTRICTIONS | event切分、training-only fit，依實際label終點purge；Final Holdout不參與搜尋。 |
| Replay 順序 | ALLOWED_WITH_RESTRICTIONS | 只支持既存CSV快照的離線順序，不代表完整Diff Depth/Order Book重建或真實receive排程；本次不執行Replay。 |
| 網路延遲 | NOT_ALLOWED | event單獨不足；缺經驗證receive欄與時鐘同步/不確定度證據。 |

[field_usage_matrix.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/field_usage_matrix.json)附檔案與函式證據。

## 16. local_timestamp_us使用範圍

| 用途 | 狀態 | 原因／限制 |
| --- | --- | --- |
| 時間排序 | ALLOWED_WITH_RESTRICTIONS | 僅診斷顯示，原始row打破重複local值；禁止作Phase 2主排序或重排event。 |
| Session 切分 | ALLOWED_WITH_RESTRICTIONS | 僅異常提示且須event與來源檔案佐證；不能由local長間隔判真實session或市場缺口。 |
| 模型特徵 | NOT_ALLOWED | 可能含clock、queue、consumer與session偏差，本階段提出禁止使用。 |
| 未來報酬標籤 | NOT_ALLOWED | 存在重複與本機進度異常且不是已證實receive；只准event標籤。 |
| 本機處理時間 | NOT_AVAILABLE | 單一wall-clock點沒有同一事件起訖monotonic pair；相鄰列間隔不是處理耗時。 |
| Local Receive Time | NOT_ALLOWED | 歷史producer未知；現存23條路徑均Book更新後重新取時，不能視為receive。 |
| 網路延遲 | NOT_ALLOWED | 差值混合clock offset與處理/排隊，缺receive與sync量測。 |
| Tick-to-Trade 延遲 | NOT_AVAILABLE | CSV缺可驗證receive、decision、send/ack時間對。 |

NOT_AVAILABLE表示缺必要測量端點；NOT_ALLOWED表示禁止賦予現有欄位該語義。診斷使用不等於允許模型時間軸。

## 17. 是否阻擋離線Phase 2

**PASS_WITH_RESTRICTIONS**。五檔event嚴格遞增、timestamp零缺失/非法、最大檔內gap241ms，且有既存mid_price；無時間證據需要BLOCK_PHASE2。負差根因未知與event離線排序可用是不同問題，不能為進Phase 2而假定clock同步。

| 活動 | 結論 |
| --- | --- |
| 離線特徵與標籤資料集 | 時間軸不阻擋，僅用event並遵守資料品質/分段規則，仍待人工批准。 |
| 100/200/500/1000ms未來標籤 | 只允許符合actual horizon及error的配對；尚未建標籤或計算留存率。 |
| Quantum Kernel離線研究 | 此時間審查不阻擋，不代表樣本量、模型效果、量子優勢或策略收益已證實。 |
| Live Paper Trading | 本次不批准啟動；需未來Recorder、獨立功能/風控驗證及人工批准。 |

本次只有5檔且test僅951列、跨日期長空白；市場代表性未證實。決策不是本次執行Phase 2的授權。

## 18. 是否阻擋延遲研究

**阻擋用這五CSV量測真實network、receive、processing或Tick-to-Trade latency。** 不可取負差絕對值、加常數或扣median後當延遲，也不可因local非遞減就稱同步。現在只可描述跨clock差與相鄰採樣間隔。缺正確receive/stage monotonic端點及clock同步誤差證據。

## 19. 未來Recorder需求（不實作）

| 欄位 | 邊界 | clock source | 單位 |
| --- | --- | --- | --- |
| exchange_event_time | Binance E | exchange wall clock | Unix ms |
| local_receive_time | ws.read完成後、parse前 | local UTC wall clock + paired monotonic clock | Unix us + monotonic ns |
| parse_complete_time | parse完成 | same local monotonic clock | ns |
| book_update_complete_time | 有效Book更新完成 | same local monotonic clock | ns |
| decision_complete_time | strategy決策完成 | same local monotonic clock | ns |

另保存session、source/binary hash、clock來源/epoch/unit、同步offset與不確定度、update ID及gap/resync。ws.read後是應用層完整訊息receive，不是NIC hardware ingress。stage耗時採同一monotonic clock；one-way network仍需同步證據，Tick-to-Trade另需send/ACK端點。此處沒有修改Recorder。

## 20. Phase 2時間規則（只提案）

1. event為唯一標籤及主要排序時間，local不得作模型特徵、label、receive或network latency。
2. 各檔獨立研究Session，event相鄰gap>200ms分segment；不可跨檔/Session/segment建立標籤。
3. h=100/200/500/1000ms，配對第一筆event>=source+h；不以固定列偏移或插值替代。
4. actual_horizon=target−source，match_error=actual−requested，提案只准0≤error≤25ms。200ms是約100ms cadence兩倍，25ms是四分之一；這是待審核且研究前凍結的保守政策，未實測最佳化或標籤留存率。
5. 保存requested_horizon_ms、actual_horizon_ms、target_event_time_ms、match_error_ms、valid_label、invalid_reason，以及source/target row、檔案SHA與session/segment。
6. gap、跨Session、尾端不足、時間/價格無效或error超標均invalid，保留原因；沒有target時actual/target/error為null，不補值偽造有效。
7. split依event，Scaler及其他轉換只Training fit；依實際label終點purge跨split重疊，並處理feature lookback。
8. Final Holdout不參與策略搜尋、threshold/hyperparameter或缺口/match-error門檻選擇。
9. Recorder未來需依第19節補欄，這次不實作、不產label、不建立模型。

[phase2_time_rules.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/phase2_time_rules.json)。

## 21. 所有實際執行命令

本次shell命令33筆（含目前finalizer）；完整命令見下方與[command_history.txt](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/command_history.txt)。結果保存在[root_commands.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/root_commands.json), [definition_commands.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/definition_commands.json), [source_commands.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/source_commands.json), [stats_commands.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/stats_commands.json)。工具回傳若為合併stdout/stderr便如實記錄；截斷後改讀精簡欄位。一次python不存在(exit127)後改python3，未安裝套件；一次編排JavaScript語法錯誤沒有執行shell或寫檔。Add File工具操作記於ledger，不偽稱shell。

finalizer在報告前後核對原968及全既存葉節點；完成結果另存finalization_execution.json。沒有執行既有audit、C++、build或測試。

<details><summary>root #1（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os
p='/mnt/c/Users/jason/.codex/attachments/389d5d0c-5b5b-4724-aa76-b0345624a520/貼上的文字.txt'
with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8') as f:print(f.read())
PY
```

</details>

<details><summary>root #2（exit 0）</summary>

```bash
set -e
pwd
test "$(pwd)" = '/home/jason/hft-realtime-codex'
realpath .
test "$(realpath .)" = '/home/jason/hft-realtime-codex'
findmnt -T .
test "$(findmnt -n -o FSTYPE -T .)" = 'ext4'
python3 -B - <<'PY'
import os,pathlib,stat,hashlib,json,datetime,time
root=pathlib.Path.cwd();base=pathlib.Path('/home/jason/hft-new-copy-20261018T194544Z.sha256')
def raw(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME),'rb') as f:return f.read()
b=raw(base);entries={}
for line in b.decode().splitlines():
 h,sep,name=line.partition('  ');rel=name.removeprefix('./')
 assert sep and len(h)==64 and rel not in entries and not pathlib.PurePosixPath(rel).is_absolute() and '..' not in pathlib.PurePosixPath(rel).parts
 entries[rel]=h
assert len(entries)==968
start=time.monotonic();bad=[];count=0
for i,(rel,digest) in enumerate(entries.items(),1):
 try:
  p=root/rel
  for parent in p.parents:
   if parent==root:break
   if stat.S_ISLNK(os.lstat(parent).st_mode):raise RuntimeError('symlink ancestor')
  a=os.lstat(p)
  if not stat.S_ISREG(a.st_mode):raise RuntimeError('not regular; symlink not followed')
  h=hashlib.sha256()
  with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME),'rb') as f:
   for block in iter(lambda:f.read(1048576),b''):h.update(block)
  z=os.lstat(p)
  if h.hexdigest()!=digest or (a.st_size,a.st_mtime_ns,a.st_ino)!=(z.st_size,z.st_mtime_ns,z.st_ino):bad.append({'relative_path':rel,'expected':digest,'actual':h.hexdigest()})
  else:count+=1
 except Exception as e:bad.append({'relative_path':rel,'error':str(e)})
 if i%100==0 or i==968:
  elapsed=time.monotonic()-start;print(f'PRECHECK {i}/968 {i/968*100:.1f}% elapsed={elapsed:.2f}s ETA={elapsed*(968-i)/i:.2f}s',flush=True)
id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
paths=[root/'artifacts/phase1_timestamp_review'/id,root/'docs'/('PHASE1_V2_TIMESTAMP_REVIEW_'+id+'.md')]
collisions=[str(p) for p in paths if os.path.lexists(p)]
result={'status':'PASS' if count==968 and not bad and not collisions else 'FAIL','run_id':id,'root':str(root),'realpath':str(root.resolve()),'filesystem':'ext4','baseline':str(base),'baseline_sha256':hashlib.sha256(b).hexdigest(),'manifest_entries':968,'matching_files':count,'differences':bad,'output_collisions':collisions,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-start,'writes_performed':False}
print('PRECHECK_JSON='+json.dumps(result,ensure_ascii=False))
if result['status']!='PASS':raise SystemExit(1)
PY
```

</details>

<details><summary>root #3（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,pathlib,stat,hashlib,json
root=pathlib.Path.cwd();run=root/'artifacts/phase1_timestamp_review/20261018T212122Z';report=root/'docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md'
assert not os.path.lexists(run) and not os.path.lexists(report)
records=[]
def walk(folder):
 with os.scandir(folder) as it:
  for entry in sorted(it,key=lambda e:e.name):
   p=pathlib.Path(entry.path);s=os.lstat(p)
   if stat.S_ISDIR(s.st_mode):walk(p);continue
   item={'relative_path':p.relative_to(root).as_posix(),'mode':stat.S_IMODE(s.st_mode),'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
   if stat.S_ISREG(s.st_mode):
    h=hashlib.sha256()
    with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME|os.O_NOFOLLOW),'rb') as f:
     for b in iter(lambda:f.read(1048576),b''):h.update(b)
    item.update(file_type='regular',sha256=h.hexdigest())
   elif stat.S_ISLNK(s.st_mode):item.update(file_type='symlink',symlink_target=os.readlink(p))
   else:item['file_type']='special'
   records.append(item)
walk(root)
for p in [root/'artifacts',root/'docs']:
 assert stat.S_ISDIR(os.lstat(p).st_mode)
if os.path.lexists(run.parent):assert stat.S_ISDIR(os.lstat(run.parent).st_mode)
else:run.parent.mkdir()
run.mkdir()
with (run/'initial_integrity_check.json').open('x',encoding='utf-8') as f:json.dump(json.loads("{\"status\":\"PASS\",\"run_id\":\"20261018T212122Z\",\"root\":\"/home/jason/hft-realtime-codex\",\"realpath\":\"/home/jason/hft-realtime-codex\",\"filesystem\":\"ext4\",\"baseline\":\"/home/jason/hft-new-copy-20261018T194544Z.sha256\",\"baseline_sha256\":\"ec4fe4b9bc6dfabac42deabf65e2b19d08a503686e019a68524e3303b263cfe8\",\"manifest_entries\":968,\"matching_files\":968,\"differences\":[],\"output_collisions\":[],\"finished_utc\":\"2026-10-18T21:21:22.957039+00:00\",\"elapsed_seconds\":0.22384510800111457,\"writes_performed\":false}"),f,ensure_ascii=False,indent=2)
with (run/'preexisting_inventory.json').open('x',encoding='utf-8') as f:json.dump({'run_id':'20261018T212122Z','captured_before_run_creation':True,'entries':records,'no_symlink_follow':True},f,ensure_ascii=False,indent=2)
print(json.dumps({'run_id':'20261018T212122Z','run_directory':str(run),'preexisting_entries':len(records),'regular':sum(x['file_type']=='regular' for x in records),'symlink':sum(x['file_type']=='symlink' for x in records),'special':sum(x['file_type']=='special' for x in records)},ensure_ascii=False))

PY
```

</details>

<details><summary>root #4（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json
from pathlib import Path
r=Path('/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z')
for p in sorted(r.iterdir()):
 print(p.name,p.stat().st_size)
for name in ['csv_timestamp_summary.json','clock_delta_statistics.json','timestamp_gap_analysis.json','warning_definition.json','source_timestamp_semantics.json','preexisting_inventory.json','initial_integrity_check.json']:
 p=r/name
 if p.is_file():
  with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f: d=json.load(f)
  print('SCHEMA',name,[(k,type(v).__name__,len(v) if isinstance(v,(dict,list)) else str(v)[:120]) for k,v in d.items()])
  if name in ['csv_timestamp_summary.json','clock_delta_statistics.json','timestamp_gap_analysis.json']:
   print(json.dumps(d,ensure_ascii=False))
PY
```

</details>

<details><summary>root #5（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json
from pathlib import Path
r=Path('/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z')
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:return f.read()
def j(n):return json.loads(read(r/n))
print('AGENTS',read(Path('AGENTS.md')))
for n in ['clock_delta_statistics.json','timestamp_gap_analysis.json']:
 d=j(n);print(n,'KEYS',list(d))
 for f in d['files']:
  print('FILE',f['relative_path'],'KEYS',list(f))
  if n.startswith('clock'):
   print(json.dumps({k:f[k] for k in ['distribution','max_positive_adjacent_delta_jump','max_negative_adjacent_delta_jump']},ensure_ascii=False))
   for k in ['blocks','block_median_changes','negative_runs','positive_runs']:
    a=f.get(k,[]);print(k, 'COUNT',len(a),'FIRST',a[:1],'LAST',a[-1:])
  else:
   print(json.dumps({k:{a:b for a,b in f[k].items() if not a.endswith('_exact') and a!='most_common_intervals'} for k in ['event_intervals','local_intervals']},ensure_ascii=False))
for n in ['preexisting_inventory.json','source_commands.json','definition_commands.json','stats_commands.json','timestamp_anomaly_examples.json']:
 d=j(n)
 print(n,'KEYS',list(d))
 if n.startswith('preexisting'):print(d['entries'][:2])
 if n.startswith('timestamp_anomaly'):print(str(d)[:2500])
d=j('source_timestamp_semantics.json')
for k in ['current_source_confirmed','historical_csv_provenance','cause_assessment']:print(k,json.dumps(d[k],ensure_ascii=False))
print('EVIDENCE_KEYS',list(d['evidence']))
print('GENERATOR_FIRST',json.dumps(d['source_generators'][0],ensure_ascii=False))
d=j('warning_definition.json')
print('DEFINITION',json.dumps(d['definition'],ensure_ascii=False))
print('WARNFILES_SCHEMA',list(d['files'][0]))
PY
```

</details>

<details><summary>root #6（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json
from pathlib import Path
r=Path('artifacts/phase1_timestamp_review/20261018T212122Z')
def j(n):
 with os.fdopen(os.open(r/n,os.O_RDONLY|os.O_NOATIME),'r') as f:return json.load(f)
for n in ['source_commands.json','definition_commands.json','stats_commands.json']:
 d=j(n);a=d.get('commands',d.get('records'))
 print(n,'entry count',len(a),'entry0 keys',list(a[0]),'entry0',str(a[0])[:650])
d=j('preexisting_inventory.json')
for typ in ['symlink','special']:
 print('INVENTORY',typ,next(e for e in d['entries'] if e['file_type']==typ))
d=j('source_timestamp_semantics.json')
for k,v in d['evidence'].items():
 print('SOURCE',k,v['path'],v.get('function'),v.get('line_start'),v.get('line_end'))
d=j('timestamp_gap_analysis.json')
for f in d['files']:
 print('GAP',Path(f['relative_path']).name, {k:{x:f[k][x] for x in ['min','max','mean','median','zero_count','negative_count','greater_than_100ms_count','greater_than_200ms_count','greater_than_500ms_count','greater_than_1000ms_count','exactly_100ms_count']} for k in ['event_intervals','local_intervals']})
d=j('clock_delta_statistics.json')
for f in d['files']:
 print('DELTA',Path(f['relative_path']).name, {k:f['distribution'][k] for k in ['min','max','mean','median','p1','p5','p25','p50','p75','p95','p99']})
d=j('timestamp_anomaly_examples.json')
for k in ['session2_tail_compression','session3_positive_run','trend_summary','causal_classification']:print('ANOMALY',k,d[k])
with os.fdopen(os.open('/home/jason/hft-new-copy-20261018T194544Z.sha256',os.O_RDONLY|os.O_NOATIME),'r') as f:
 print('MANIFEST_FIRST',f.readline().rstrip())
PY
```

</details>

<details><summary>root #7（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os
p='artifacts/phase1_timestamp_review/20261018T212122Z/finalize_timestamp_review.py'
with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f: source=f.read()
compile(source,p,'exec')
print('SYNTAX PASS; no bytecode written')
PY
```

</details>

<details><summary>definition_commands.json #1（exit 127）</summary>

```bash
python -B - <<'PY'
from pathlib import Path
p=Path('/mnt/c/Users/jason/.codex/attachments/389d5d0c-5b5b-4724-aa76-b0345624a520/貼上的文字.txt')
print(p.read_text())
PY
```

</details>

<details><summary>definition_commands.json #2（exit 0）</summary>

```bash
python3 -B - <<'PY'
from pathlib import Path
p=Path('/mnt/c/Users/jason/.codex/attachments/389d5d0c-5b5b-4724-aa76-b0345624a520/貼上的文字.txt')
print(p.read_text())
PY
```

</details>

<details><summary>definition_commands.json #3（exit 0）</summary>

```bash
rg -n 'local_timestamp_us|event_time_ms|negative|clock|Decimal|def ' tools/dataset_audit.py
```

</details>

<details><summary>definition_commands.json #4（exit 0）</summary>

```bash
rg --files artifacts/phase1_v2/20261018T210029Z | rg 'audit|errors|report'
```

</details>

<details><summary>definition_commands.json #5（exit 0）</summary>

```bash
rg -n '269.?284|Dataset|obi_market_data|clock' docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md
```

</details>

<details><summary>definition_commands.json #6（exit 0）</summary>

```bash
python3 -B - <<'PY'
from pathlib import Path
import os,json,csv
root=Path.cwd()
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:return f.read()
p=root/'tools/dataset_audit.py';lines=read(p).splitlines()
for a,b in [(20,48),(84,130),(194,245),(249,342),(615,645)]:
 print(f'FILE {p} LINES {a}-{b}')
 for n in range(a,b+1):print(f'{n}: {lines[n-1]}')
for stem in ['obi_market_data_20260827_session1','obi_market_data_20260827_session2','obi_market_data_20260827_session3','obi_market_data_test_20260827','obi_market_data']:
 csvpath=root/'results'/f'{stem}.csv'
 with os.fdopen(os.open(csvpath,os.O_RDONLY|os.O_NOATIME),'r',newline='') as f:
  reader=csv.reader(f);print('CSV',csvpath,'HEADER',next(reader),'SAMPLE',next(reader))
 auditdir=root/'artifacts/dataset_audit'/f'phase1v2_20261018T210029Z_{stem}'
 for name in ['audit_report.json','audit_report.md']:
  p=auditdir/name; print('FILE',p);print(read(p))
 p=auditdir/'errors.csv'
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',newline='') as f:
  reader=csv.reader(f);print('ERROR SAMPLE',p,next(reader),next(reader))
PY
```

</details>

<details><summary>definition_commands.json #7（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json,csv,hashlib,re
from pathlib import Path
from collections import Counter
from decimal import Decimal
root=Path.cwd();results=[]
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:return f.read()
for stem in ['obi_market_data_20260827_session1','obi_market_data_20260827_session2','obi_market_data_20260827_session3','obi_market_data_test_20260827','obi_market_data']:
 d=root/'artifacts/dataset_audit'/f'phase1v2_20261018T210029Z_{stem}'
 j=read(d/'audit_report.json'); report=json.loads(j); item=report['files'][0];md=read(d/'audit_report.md'); checks=item['checks'];counts=Counter();pathcounts=Counter();bad=[];rows=0;minrecord=None;maxrecord=None;minline=None;maxline=None;msgmin=None;msgmax=None
 p=d/'errors.csv'
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',newline='') as f:
  rd=csv.DictReader(f);header=rd.fieldnames
  for physical,row in enumerate(rd,2):
   rows+=1; counts[(row['check'],row['status'])]+=1;pathcounts[row['path']]+=1
   try:
    record=int(row['record']);line=int(row['line']);m=re.fullmatch(r'local minus event=(.+) ms; not a receive/network latency',row['message']);delta=Decimal(m[1])
    if not(delta.is_finite() and delta<0):bad.append({'line':physical,'reason':'message not finite negative'})
    if line!=record+1:bad.append({'line':physical,'reason':'record mapping'})
    minrecord=record if minrecord is None else min(minrecord,record);maxrecord=record if maxrecord is None else max(maxrecord,record);minline=line if minline is None else min(minline,line);maxline=line if maxline is None else max(maxline,line);msgmin=delta if msgmin is None else min(msgmin,delta);msgmax=delta if msgmax is None else max(msgmax,delta)
   except Exception as e:bad.append({'line':physical,'reason':type(e).__name__})
  counttable=[{'check':k[0],'status':k[1],'count':v} for k,v in sorted(counts.items())]
  mismatches=[]
  for name,check in checks.items():
   found=sum(n for (c,s),n in counts.items() if c==name)
   if found!=check['count']:mismatches.append({'check':name,'json':check['count'],'csv':found})
  for c,s in counts:
   if c not in checks:mismatches.append({'check':c,'reason':'unexpected in errors'})
  markdown_rows=[]
  for line_no,line in enumerate(md.splitlines(),1):
   if line.startswith('| local_event_clock_order |') or line.startswith('- CSV 本機時間'):
    markdown_rows.append({'line':line_no,'text':line})
  expected=f"| local_event_clock_order | WARNING | {checks['local_event_clock_order']['count']} | {checks['local_event_clock_order']['checked']} |"
  source=root/item['path']
  with os.fdopen(os.open(source,os.O_RDONLY|os.O_NOATIME),'r',newline='') as f:
   rd=csv.reader(f,strict=True);csvheader=next(rd);sample=next(rd)
  result={'path':item['path'],'input_sha256_from_audit':item['sha256'],'input_size_bytes':item['size_bytes'],'records':item['records'],'parse_errors':item['parse_errors'],'report_status':report['status'],'report_path':str(d/'audit_report.json'),'markdown_path':str(d/'audit_report.md'),'errors_path':str(p),'audit_report_sha256':hashlib.sha256(j.encode()).hexdigest(),'checks':{n:{k:v for k,v in c.items() if k!='samples'} for n,c in checks.items()},'metrics':item['metrics'],'csv_header':csvheader,'first_record_sample':sample,'errors_csv_header':header,'errors_csv_records':rows,'counts_by_check_status':counttable,'counts_by_input_path':dict(pathcounts),'error_message_validation_failures':bad,'errors_count_mismatches':mismatches,'markdown_warning_row_matches_json':expected in md,'markdown_evidence':markdown_rows,'errors_record_first':minrecord,'errors_record_last':maxrecord,'errors_source_line_first':minline,'errors_source_line_last':maxline,'errors_negative_offset_ms_min':str(msgmin),'errors_negative_offset_ms_max':str(msgmax),'json_warning_key_line':next(n for n,line in enumerate(j.splitlines(),1) if line.strip()=='"local_event_clock_order": {')}
  results.append(result)
print(json.dumps({'files':results,'total_records':sum(x['records'] for x in results),'total_errors_csv_records':sum(x['errors_csv_records'] for x in results),'total_local_event_clock_order_warning':sum(x['checks']['local_event_clock_order']['count'] for x in results),'all_counts_match':all(not x['errors_count_mismatches'] and not x['error_message_validation_failures'] and x['markdown_warning_row_matches_json'] for x in results)},ensure_ascii=False,indent=2))
PY
```

</details>

<details><summary>definition_commands.json #8（exit 0）</summary>

```bash
python3 -B - <<'PY'
from pathlib import Path
import os,json,csv
root=Path.cwd()
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:return f.read()
p=root/'tools/dataset_audit.py';lines=read(p).splitlines()
for a,b in [(20,48),(84,130),(194,245),(249,342),(615,645)]:
 print(f'FILE {p} LINES {a}-{b}')
 for n in range(a,b+1):print(f'{n}: {lines[n-1]}')
for stem in ['obi_market_data_20260827_session1','obi_market_data_20260827_session2','obi_market_data_20260827_session3','obi_market_data_test_20260827','obi_market_data']:
 csvpath=root/'results'/f'{stem}.csv'
 with os.fdopen(os.open(csvpath,os.O_RDONLY|os.O_NOATIME),'r',newline='') as f:
  reader=csv.reader(f);print('CSV',csvpath,'HEADER',next(reader),'SAMPLE',next(reader))
 auditdir=root/'artifacts/dataset_audit'/f'phase1v2_20261018T210029Z_{stem}'
 for name in ['audit_report.json','audit_report.md']:
  p=auditdir/name; print('FILE',p);print(read(p))
 p=auditdir/'errors.csv'
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',newline='') as f:
  reader=csv.reader(f);print('ERROR SAMPLE',p,next(reader),next(reader))
PY
```

</details>

<details><summary>definition_commands.json #9（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os
from pathlib import Path
root=Path.cwd()
for rel,ranges in [('src/orderbook_csv.cpp',[(399,409),(586,603),(780,790),(810,863)]),('src/csv_logger.h',[(15,35),(60,80),(95,112),(130,143)]),('src/orderbook_realtime_latency_benchmark.cpp',[(715,724),(2030,2037),(2060,2073)])]:
 p=root/rel
 try:
  with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:lines=f.read().splitlines()
 except FileNotFoundError:
  print('NOT AVAILABLE exact source path',p);continue
 print('FILE',p)
 for a,b in ranges:
  for i in range(a,min(b,len(lines))+1):print(f'{i}: {lines[i-1]}')
PY
```

</details>

<details><summary>definition_commands.json #10（exit 0）</summary>

```bash
python3 -B - <<'PY'
import json
from pathlib import Path
run=Path('/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z')
assert not (run/'warning_definition.json').exists()
assert not (run/'definition_commands.json').exists()
data=json.loads(r'''{
  "schema_version": "1.0",
  "run_id": "20261018T212122Z",
  "status": "CONFIRMED",
  "review_scope": "僅讀取既有 Audit、五 CSV header/首筆與現有 C++ logger；不重跑 Audit、不修改市場資料。",
  "definition": {
    "check": "local_event_clock_order",
    "status_when_triggered": "WARNING",
    "local_field": "local_timestamp_us",
    "local_unit": "microseconds",
    "event_field": "event_time_ms",
    "event_unit": "milliseconds",
    "audit_expression": "offset = Decimal(local_time) / 1000 - timestamp",
    "audit_unit": "milliseconds",
    "audit_condition": "offset < 0",
    "equivalent_integer_expression": "delta_us = local_timestamp_us - event_time_ms * 1000",
    "equivalent_integer_condition": "delta_us < 0",
    "equivalent_integer_unit": "microseconds",
    "conversion": "Audit 將 local_timestamp_us 除以 1000 轉為 ms；本次統計等價地將 event_time_ms 乘以 1000 轉為 us。",
    "arithmetic": "時間欄位先以 integer() 驗證非負十進位整數。Audit 以 Decimal 計算 offset；已見五檔時間戳位數不造成此差值的浮點捨入。本次可用 Python 整數算 delta_us。",
    "zero_tolerance": "判斷直接 offset < 0，沒有 epsilon。1e-8 TOLERANCE 屬價格/OBI 一致性檢查，並非時鐘警告容忍誤差。",
    "eligibility": "該列 CSV 可解析且欄數正確，兩時間欄位存在、非空、均通過 integer()。missing/invalid timestamp 另由 schema/missing checks 記錄；不能把未參與比較的列視作非負。",
    "does_not_mean": "不是 network latency、receive latency、處理耗時、時鐘同步誤差的直接量測，也不直接證明資料毀損。",
    "code_evidence": [
      {
        "path": "/home/jason/hft-realtime-codex/tools/dataset_audit.py",
        "function": "audit_csv",
        "lines": [
          329,
          336
        ],
        "supports": "offset 公式、ms 單位、負數判定、WARNING 訊息"
      },
      {
        "path": "/home/jason/hft-realtime-codex/tools/dataset_audit.py",
        "function": "integer",
        "lines": [
          206,
          217
        ],
        "supports": "非負十進位整數規則"
      },
      {
        "path": "/home/jason/hft-realtime-codex/tools/dataset_audit.py",
        "function": "time_value",
        "lines": [
          220,
          226
        ],
        "supports": "event timestamp schema"
      },
      {
        "path": "/home/jason/hft-realtime-codex/tools/dataset_audit.py",
        "function": "audit_csv",
        "lines": [
          249,
          329
        ],
        "supports": "CSV schema、解析、欄位與 eligibility"
      },
      {
        "path": "/home/jason/hft-realtime-codex/tools/dataset_audit.py",
        "function": "FileAudit.issue",
        "lines": [
          111,
          126
        ],
        "supports": "每次異常寫入 errors.csv，JSON樣本上限20"
      },
      {
        "path": "/home/jason/hft-realtime-codex/tools/dataset_audit.py",
        "function": "write_markdown",
        "lines": [
          638,
          643
        ],
        "supports": "不可解讀為負網路延遲"
      },
      {
        "path": "/home/jason/hft-realtime-codex/tools/dataset_audit.py",
        "function": "module constants REQUIRED_CSV / CSV_CHECKS / ERROR_FIELDS / TOLERANCE",
        "lines": [
          25,
          47
        ],
        "supports": "欄位與 check 名稱"
      }
    ]
  },
  "schema_gate": {
    "status": "CONFIRMED_FOR_ARITHMETIC",
    "exact_columns": [
      "local_timestamp_us",
      "event_time_ms",
      "update_id",
      "best_bid",
      "best_ask",
      "mid_price",
      "spread",
      "bid_volume_5",
      "ask_volume_5",
      "obi_5"
    ],
    "five_headers_identical": true,
    "csv_header_line": 1,
    "sampled_record_line": 2,
    "historical_audit_all_timestamp_schema_pass": true,
    "historical_audit_all_required_columns_pass": true,
    "current_logger_evidence": [
      {
        "path": "/home/jason/hft-realtime-codex/src/csv_logger.h",
        "function": "MarketSnapshot",
        "lines": [
          15,
          16
        ],
        "supports": "localTimestampUs、eventTimeMs 欄位"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/csv_logger.h",
        "function": "AsyncCsvLogger::AsyncCsvLogger",
        "lines": [
          99,
          109
        ],
        "supports": "十欄 header 與單位命名"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/csv_logger.h",
        "function": "AsyncCsvLogger::writerLoop",
        "lines": [
          65,
          79
        ],
        "supports": "原整數時間戳直接寫出，無單位或時區轉換"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/orderbook_csv.cpp",
        "function": "parseDepthEvent",
        "lines": [
          399,
          406
        ],
        "supports": "event.eventTime 取 JSON E"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/orderbook_csv.cpp",
        "function": "main",
        "lines": [
          814,
          826
        ],
        "supports": "OrderBook applyEvent 後 system_clock epoch duration_cast<microseconds>"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/orderbook_csv.cpp",
        "function": "main",
        "lines": [
          849,
          862
        ],
        "supports": "localTimestampUs、event.eventTime 原值傳 MarketSnapshot/CSV logger"
      }
    ],
    "unit_schema_mismatch": "未發現 header、logger field、Audit 換算彼此不一致。",
    "historical_producer_provenance": "UNKNOWN：共同 logger 被多個現有來源使用；僅有 header/數值與現有碼不能逐一證明五個歷史 CSV 的確切 source/binary 與生成命令。",
    "receive_time_semantics": "不得把 local_timestamp_us 改稱 Local Receive Time。可靜態確認的 orderbook_csv.cpp 路徑在 ws.read、parse、queue、book update 後才取得它；歷史 producer 未被唯一識別。",
    "source_order_evidence": [
      {
        "path": "/home/jason/hft-realtime-codex/src/orderbook_csv.cpp",
        "function": "wsReader",
        "lines": [
          591,
          600
        ],
        "supports": "ws.read → parseDepthEvent → queue.push"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/orderbook_csv.cpp",
        "function": "main",
        "lines": [
          785,
          826
        ],
        "supports": "queue.waitAndPop → book.applyEvent →取localTimestampUs"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/orderbook_csv.cpp",
        "function": "main",
        "lines": [
          828,
          862
        ],
        "supports": "其後價格/OBI計算、組snapshot、logger.push"
      },
      {
        "path": "/home/jason/hft-realtime-codex/src/csv_logger.h",
        "function": "AsyncCsvLogger::push",
        "lines": [
          135,
          142
        ],
        "supports": "CSV queue入列；並未重新取timestamp"
      }
    ]
  },
  "warning_total": {
    "value": 269284,
    "interpretation": "五個檔案合計，全部為同一 local_event_clock_order WARNING；不是單一檔案，也不是多種警告總和。",
    "total_eligible_records": 269416,
    "other_warning_or_fail_occurrences": 0,
    "errors_csv_stream_verified": true,
    "all_json_check_counts_match_errors_csv": true,
    "all_markdown_warning_counts_match_json": true,
    "unwarned_records": 132,
    "unwarned_note": "132 為 session3 未觸發該警告的列；正/零細分由本次串流統計另行提供。"
  },
  "files": [
    {
      "path": "results/obi_market_data_20260827_session1.csv",
      "input_sha256_from_audit": "9931b0d9ef9be5dba36ea26cdd4d6d7fd1552a195af53460c59ffe415ceea8d3",
      "input_size_bytes": 8019032,
      "records": 60558,
      "parse_errors": 0,
      "report_status": "WARNING",
      "report_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.json",
      "markdown_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.md",
      "errors_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/errors.csv",
      "audit_report_sha256": "51ae4e4b83c6ac1680de2fc8d0e2ba38daf9e13f4f802eac93a2d9b87cd0d263",
      "checks": {
        "required_columns": {
          "status": "PASS",
          "count": 0,
          "checked": 1,
          "detail": "No violations among eligible observations."
        },
        "parse_errors": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "missing_values": {
          "status": "PASS",
          "count": 0,
          "checked": 605580,
          "detail": "No violations among eligible observations."
        },
        "non_finite_values": {
          "status": "PASS",
          "count": 0,
          "checked": 605580,
          "detail": "No violations among eligible observations."
        },
        "invalid_numeric_values": {
          "status": "PASS",
          "count": 0,
          "checked": 605580,
          "detail": "No violations among eligible observations."
        },
        "timestamp_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 121116,
          "detail": "No violations among eligible observations."
        },
        "update_id_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "event_time_monotonic": {
          "status": "PASS",
          "count": 0,
          "checked": 60557,
          "detail": "No violations among eligible observations."
        },
        "duplicate_timestamps": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "bid_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "ask_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "uncrossed_book": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "spread_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "mid_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "spread_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "volume_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 121116,
          "detail": "No violations among eligible observations."
        },
        "obi_range": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "obi_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 60558,
          "detail": "No violations among eligible observations."
        },
        "local_event_clock_order": {
          "status": "WARNING",
          "count": 60558,
          "checked": 60558,
          "detail": "See errors.csv for every occurrence; samples are capped at 20."
        }
      },
      "metrics": {
        "first_event_time_ms": 1787767099114,
        "last_event_time_ms": 1787773157814,
        "columns": [
          "local_timestamp_us",
          "event_time_ms",
          "update_id",
          "best_bid",
          "best_ask",
          "mid_price",
          "spread",
          "bid_volume_5",
          "ask_volume_5",
          "obi_5"
        ],
        "min_event_time_ms": 1787767099114,
        "max_event_time_ms": 1787773157814,
        "local_minus_event_ms_min": "-155.713",
        "local_minus_event_ms_max": "-31.951",
        "max_obi_absolute_difference": "4.9997951743066650281E-9",
        "physical_lines": 60559,
        "unique_timestamps": 60558,
        "duplicate_timestamps": 0
      },
      "csv_header": [
        "local_timestamp_us",
        "event_time_ms",
        "update_id",
        "best_bid",
        "best_ask",
        "mid_price",
        "spread",
        "bid_volume_5",
        "ask_volume_5",
        "obi_5"
      ],
      "first_record_sample": [
        "1787767099004356",
        "1787767099114",
        "99216300424",
        "78453.84000000",
        "78453.85000000",
        "78453.84500000",
        "0.01000000",
        "0.21099000",
        "4.80616000",
        "-0.91589249"
      ],
      "errors_csv_header": [
        "path",
        "kind",
        "line",
        "record",
        "check",
        "status",
        "message"
      ],
      "errors_csv_records": 60558,
      "counts_by_check_status": [
        {
          "check": "local_event_clock_order",
          "status": "WARNING",
          "count": 60558
        }
      ],
      "counts_by_input_path": {
        "results/obi_market_data_20260827_session1.csv": 60558
      },
      "error_message_validation_failures": [],
      "errors_count_mismatches": [],
      "markdown_warning_row_matches_json": true,
      "markdown_evidence": [
        {
          "line": 39,
          "text": "| local_event_clock_order | WARNING | 60558 | 60558 |"
        },
        {
          "line": 76,
          "text": "- CSV 本機時間尚未證明為 WebSocket 接收時間。local−event 為負記為 WARNING，不能解讀為負的網路延遲。"
        }
      ],
      "errors_record_first": 1,
      "errors_record_last": 60558,
      "errors_source_line_first": 2,
      "errors_source_line_last": 60559,
      "errors_negative_offset_ms_min": "-155.713",
      "errors_negative_offset_ms_max": "-31.951",
      "json_warning_key_line": 170,
      "absolute_path": "/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session1.csv",
      "audit_json_pointer": "/files/0/checks/local_event_clock_order",
      "evidence_positions": {
        "csv_header_line": 1,
        "csv_first_sample_line": 2,
        "audit_warning_key_line": 170,
        "markdown_warning_line": 39,
        "markdown_receive_limitation_line": 76,
        "errors_csv_header_line": 1,
        "errors_csv_data_lines": [
          2,
          60559
        ]
      }
    },
    {
      "path": "results/obi_market_data_20260827_session2.csv",
      "input_sha256_from_audit": "363e81f86de61a3acc697216082770f11a7158935c8745e172235ee6f9e1fd7c",
      "input_size_bytes": 13226704,
      "records": 99871,
      "parse_errors": 0,
      "report_status": "WARNING",
      "report_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.json",
      "markdown_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.md",
      "errors_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/errors.csv",
      "audit_report_sha256": "e422d50ae77e06cabbb4843171604de9b1723ff47dae76a3a08c1987bb20d3fc",
      "checks": {
        "required_columns": {
          "status": "PASS",
          "count": 0,
          "checked": 1,
          "detail": "No violations among eligible observations."
        },
        "parse_errors": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "missing_values": {
          "status": "PASS",
          "count": 0,
          "checked": 998710,
          "detail": "No violations among eligible observations."
        },
        "non_finite_values": {
          "status": "PASS",
          "count": 0,
          "checked": 998710,
          "detail": "No violations among eligible observations."
        },
        "invalid_numeric_values": {
          "status": "PASS",
          "count": 0,
          "checked": 998710,
          "detail": "No violations among eligible observations."
        },
        "timestamp_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 199742,
          "detail": "No violations among eligible observations."
        },
        "update_id_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "event_time_monotonic": {
          "status": "PASS",
          "count": 0,
          "checked": 99870,
          "detail": "No violations among eligible observations."
        },
        "duplicate_timestamps": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "bid_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "ask_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "uncrossed_book": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "spread_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "mid_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "spread_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "volume_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 199742,
          "detail": "No violations among eligible observations."
        },
        "obi_range": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "obi_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 99871,
          "detail": "No violations among eligible observations."
        },
        "local_event_clock_order": {
          "status": "WARNING",
          "count": 99871,
          "checked": 99871,
          "detail": "See errors.csv for every occurrence; samples are capped at 20."
        }
      },
      "metrics": {
        "first_event_time_ms": 1787773384514,
        "last_event_time_ms": 1787783377014,
        "columns": [
          "local_timestamp_us",
          "event_time_ms",
          "update_id",
          "best_bid",
          "best_ask",
          "mid_price",
          "spread",
          "bid_volume_5",
          "ask_volume_5",
          "obi_5"
        ],
        "min_event_time_ms": 1787773384514,
        "max_event_time_ms": 1787783377014,
        "local_minus_event_ms_min": "-4541.681",
        "local_minus_event_ms_max": "-47.57",
        "max_obi_absolute_difference": "5E-9",
        "physical_lines": 99872,
        "unique_timestamps": 99871,
        "duplicate_timestamps": 0
      },
      "csv_header": [
        "local_timestamp_us",
        "event_time_ms",
        "update_id",
        "best_bid",
        "best_ask",
        "mid_price",
        "spread",
        "bid_volume_5",
        "ask_volume_5",
        "obi_5"
      ],
      "first_record_sample": [
        "1787773384358777",
        "1787773384514",
        "99219576465",
        "78411.07000000",
        "78411.08000000",
        "78411.07500000",
        "0.01000000",
        "2.78833000",
        "1.19946000",
        "0.39843372"
      ],
      "errors_csv_header": [
        "path",
        "kind",
        "line",
        "record",
        "check",
        "status",
        "message"
      ],
      "errors_csv_records": 99871,
      "counts_by_check_status": [
        {
          "check": "local_event_clock_order",
          "status": "WARNING",
          "count": 99871
        }
      ],
      "counts_by_input_path": {
        "results/obi_market_data_20260827_session2.csv": 99871
      },
      "error_message_validation_failures": [],
      "errors_count_mismatches": [],
      "markdown_warning_row_matches_json": true,
      "markdown_evidence": [
        {
          "line": 39,
          "text": "| local_event_clock_order | WARNING | 99871 | 99871 |"
        },
        {
          "line": 76,
          "text": "- CSV 本機時間尚未證明為 WebSocket 接收時間。local−event 為負記為 WARNING，不能解讀為負的網路延遲。"
        }
      ],
      "errors_record_first": 1,
      "errors_record_last": 99871,
      "errors_source_line_first": 2,
      "errors_source_line_last": 99872,
      "errors_negative_offset_ms_min": "-4541.681",
      "errors_negative_offset_ms_max": "-47.57",
      "json_warning_key_line": 170,
      "absolute_path": "/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session2.csv",
      "audit_json_pointer": "/files/0/checks/local_event_clock_order",
      "evidence_positions": {
        "csv_header_line": 1,
        "csv_first_sample_line": 2,
        "audit_warning_key_line": 170,
        "markdown_warning_line": 39,
        "markdown_receive_limitation_line": 76,
        "errors_csv_header_line": 1,
        "errors_csv_data_lines": [
          2,
          99872
        ]
      }
    },
    {
      "path": "results/obi_market_data_20260827_session3.csv",
      "input_sha256_from_audit": "72decc3d89cf833f6327bb11dfe66f3a9371fb932df290b54f7b5250d1a4e1b4",
      "input_size_bytes": 7691375,
      "records": 58037,
      "parse_errors": 0,
      "report_status": "WARNING",
      "report_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.json",
      "markdown_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.md",
      "errors_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/errors.csv",
      "audit_report_sha256": "3bce21bc147b82a55ab67dcab58e6cbcfff8ca2ae78f793d3ae4bba938fbcf1b",
      "checks": {
        "required_columns": {
          "status": "PASS",
          "count": 0,
          "checked": 1,
          "detail": "No violations among eligible observations."
        },
        "parse_errors": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "missing_values": {
          "status": "PASS",
          "count": 0,
          "checked": 580370,
          "detail": "No violations among eligible observations."
        },
        "non_finite_values": {
          "status": "PASS",
          "count": 0,
          "checked": 580370,
          "detail": "No violations among eligible observations."
        },
        "invalid_numeric_values": {
          "status": "PASS",
          "count": 0,
          "checked": 580370,
          "detail": "No violations among eligible observations."
        },
        "timestamp_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 116074,
          "detail": "No violations among eligible observations."
        },
        "update_id_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "event_time_monotonic": {
          "status": "PASS",
          "count": 0,
          "checked": 58036,
          "detail": "No violations among eligible observations."
        },
        "duplicate_timestamps": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "bid_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "ask_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "uncrossed_book": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "spread_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "mid_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "spread_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "volume_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 116074,
          "detail": "No violations among eligible observations."
        },
        "obi_range": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "obi_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 58037,
          "detail": "No violations among eligible observations."
        },
        "local_event_clock_order": {
          "status": "WARNING",
          "count": 57905,
          "checked": 58037,
          "detail": "See errors.csv for every occurrence; samples are capped at 20."
        }
      },
      "metrics": {
        "first_event_time_ms": 1787808550014,
        "last_event_time_ms": 1787814356615,
        "columns": [
          "local_timestamp_us",
          "event_time_ms",
          "update_id",
          "best_bid",
          "best_ask",
          "mid_price",
          "spread",
          "bid_volume_5",
          "ask_volume_5",
          "obi_5"
        ],
        "min_event_time_ms": 1787808550014,
        "max_event_time_ms": 1787814356615,
        "local_minus_event_ms_min": "-337.505",
        "local_minus_event_ms_max": "12901.877",
        "max_obi_absolute_difference": "4.99992539651750943734E-9",
        "physical_lines": 58038,
        "unique_timestamps": 58037,
        "duplicate_timestamps": 0
      },
      "csv_header": [
        "local_timestamp_us",
        "event_time_ms",
        "update_id",
        "best_bid",
        "best_ask",
        "mid_price",
        "spread",
        "bid_volume_5",
        "ask_volume_5",
        "obi_5"
      ],
      "first_record_sample": [
        "1787808549721624",
        "1787808550014",
        "99237908070",
        "78667.87000000",
        "78667.88000000",
        "78667.87500000",
        "0.01000000",
        "0.31365000",
        "3.40041000",
        "-0.83110127"
      ],
      "errors_csv_header": [
        "path",
        "kind",
        "line",
        "record",
        "check",
        "status",
        "message"
      ],
      "errors_csv_records": 57905,
      "counts_by_check_status": [
        {
          "check": "local_event_clock_order",
          "status": "WARNING",
          "count": 57905
        }
      ],
      "counts_by_input_path": {
        "results/obi_market_data_20260827_session3.csv": 57905
      },
      "error_message_validation_failures": [],
      "errors_count_mismatches": [],
      "markdown_warning_row_matches_json": true,
      "markdown_evidence": [
        {
          "line": 39,
          "text": "| local_event_clock_order | WARNING | 57905 | 58037 |"
        },
        {
          "line": 76,
          "text": "- CSV 本機時間尚未證明為 WebSocket 接收時間。local−event 為負記為 WARNING，不能解讀為負的網路延遲。"
        }
      ],
      "errors_record_first": 1,
      "errors_record_last": 58037,
      "errors_source_line_first": 2,
      "errors_source_line_last": 58038,
      "errors_negative_offset_ms_min": "-337.505",
      "errors_negative_offset_ms_max": "-75.797",
      "json_warning_key_line": 170,
      "absolute_path": "/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session3.csv",
      "audit_json_pointer": "/files/0/checks/local_event_clock_order",
      "evidence_positions": {
        "csv_header_line": 1,
        "csv_first_sample_line": 2,
        "audit_warning_key_line": 170,
        "markdown_warning_line": 39,
        "markdown_receive_limitation_line": 76,
        "errors_csv_header_line": 1,
        "errors_csv_data_lines": [
          2,
          57906
        ]
      }
    },
    {
      "path": "results/obi_market_data_test_20260827.csv",
      "input_sha256_from_audit": "aa9bb47e598aaa024640c079654ed17da1e70552ed06632361dc4cb607b8171f",
      "input_size_bytes": 126181,
      "records": 951,
      "parse_errors": 0,
      "report_status": "WARNING",
      "report_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.json",
      "markdown_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.md",
      "errors_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/errors.csv",
      "audit_report_sha256": "6b22f7a8e2560f9a0504a25faed472cf35066e6e1e58366931ab0168b21b45c6",
      "checks": {
        "required_columns": {
          "status": "PASS",
          "count": 0,
          "checked": 1,
          "detail": "No violations among eligible observations."
        },
        "parse_errors": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "missing_values": {
          "status": "PASS",
          "count": 0,
          "checked": 9510,
          "detail": "No violations among eligible observations."
        },
        "non_finite_values": {
          "status": "PASS",
          "count": 0,
          "checked": 9510,
          "detail": "No violations among eligible observations."
        },
        "invalid_numeric_values": {
          "status": "PASS",
          "count": 0,
          "checked": 9510,
          "detail": "No violations among eligible observations."
        },
        "timestamp_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 1902,
          "detail": "No violations among eligible observations."
        },
        "update_id_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "event_time_monotonic": {
          "status": "PASS",
          "count": 0,
          "checked": 950,
          "detail": "No violations among eligible observations."
        },
        "duplicate_timestamps": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "bid_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "ask_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "uncrossed_book": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "spread_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "mid_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "spread_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "volume_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 1902,
          "detail": "No violations among eligible observations."
        },
        "obi_range": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "obi_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 951,
          "detail": "No violations among eligible observations."
        },
        "local_event_clock_order": {
          "status": "WARNING",
          "count": 951,
          "checked": 951,
          "detail": "See errors.csv for every occurrence; samples are capped at 20."
        }
      },
      "metrics": {
        "first_event_time_ms": 1787765781314,
        "last_event_time_ms": 1787765876414,
        "columns": [
          "local_timestamp_us",
          "event_time_ms",
          "update_id",
          "best_bid",
          "best_ask",
          "mid_price",
          "spread",
          "bid_volume_5",
          "ask_volume_5",
          "obi_5"
        ],
        "min_event_time_ms": 1787765781314,
        "max_event_time_ms": 1787765876414,
        "local_minus_event_ms_min": "-102.803",
        "local_minus_event_ms_max": "-53.977",
        "max_obi_absolute_difference": "4.9966214887003765116E-9",
        "physical_lines": 952,
        "unique_timestamps": 951,
        "duplicate_timestamps": 0
      },
      "csv_header": [
        "local_timestamp_us",
        "event_time_ms",
        "update_id",
        "best_bid",
        "best_ask",
        "mid_price",
        "spread",
        "bid_volume_5",
        "ask_volume_5",
        "obi_5"
      ],
      "first_record_sample": [
        "1787765781213756",
        "1787765781314",
        "99215515389",
        "78538.39000000",
        "78538.40000000",
        "78538.39500000",
        "0.01000000",
        "3.95875000",
        "0.20714000",
        "0.90055426"
      ],
      "errors_csv_header": [
        "path",
        "kind",
        "line",
        "record",
        "check",
        "status",
        "message"
      ],
      "errors_csv_records": 951,
      "counts_by_check_status": [
        {
          "check": "local_event_clock_order",
          "status": "WARNING",
          "count": 951
        }
      ],
      "counts_by_input_path": {
        "results/obi_market_data_test_20260827.csv": 951
      },
      "error_message_validation_failures": [],
      "errors_count_mismatches": [],
      "markdown_warning_row_matches_json": true,
      "markdown_evidence": [
        {
          "line": 39,
          "text": "| local_event_clock_order | WARNING | 951 | 951 |"
        },
        {
          "line": 76,
          "text": "- CSV 本機時間尚未證明為 WebSocket 接收時間。local−event 為負記為 WARNING，不能解讀為負的網路延遲。"
        }
      ],
      "errors_record_first": 1,
      "errors_record_last": 951,
      "errors_source_line_first": 2,
      "errors_source_line_last": 952,
      "errors_negative_offset_ms_min": "-102.803",
      "errors_negative_offset_ms_max": "-53.977",
      "json_warning_key_line": 170,
      "absolute_path": "/home/jason/hft-realtime-codex/results/obi_market_data_test_20260827.csv",
      "audit_json_pointer": "/files/0/checks/local_event_clock_order",
      "evidence_positions": {
        "csv_header_line": 1,
        "csv_first_sample_line": 2,
        "audit_warning_key_line": 170,
        "markdown_warning_line": 39,
        "markdown_receive_limitation_line": 76,
        "errors_csv_header_line": 1,
        "errors_csv_data_lines": [
          2,
          952
        ]
      }
    },
    {
      "path": "results/obi_market_data.csv",
      "input_sha256_from_audit": "e71676d8d2d6c04e6cf9b4f80ef3eb113de78a92eff8a280fd633541ac8231e7",
      "input_size_bytes": 6683124,
      "records": 49999,
      "parse_errors": 0,
      "report_status": "WARNING",
      "report_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.json",
      "markdown_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.md",
      "errors_path": "/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/errors.csv",
      "audit_report_sha256": "0cd167eabf120387a7770132cf9d4580438ff8c35c0a17f21d9e76ebb752c9e6",
      "checks": {
        "required_columns": {
          "status": "PASS",
          "count": 0,
          "checked": 1,
          "detail": "No violations among eligible observations."
        },
        "parse_errors": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "missing_values": {
          "status": "PASS",
          "count": 0,
          "checked": 499990,
          "detail": "No violations among eligible observations."
        },
        "non_finite_values": {
          "status": "PASS",
          "count": 0,
          "checked": 499990,
          "detail": "No violations among eligible observations."
        },
        "invalid_numeric_values": {
          "status": "PASS",
          "count": 0,
          "checked": 499990,
          "detail": "No violations among eligible observations."
        },
        "timestamp_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 99998,
          "detail": "No violations among eligible observations."
        },
        "update_id_schema": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "event_time_monotonic": {
          "status": "PASS",
          "count": 0,
          "checked": 49998,
          "detail": "No violations among eligible observations."
        },
        "duplicate_timestamps": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "bid_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "ask_positive": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "uncrossed_book": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "spread_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "mid_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "spread_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "volume_nonnegative": {
          "status": "PASS",
          "count": 0,
          "checked": 99998,
          "detail": "No violations among eligible observations."
        },
        "obi_range": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "obi_consistency": {
          "status": "PASS",
          "count": 0,
          "checked": 49999,
          "detail": "No violations among eligible observations."
        },
        "local_event_clock_order": {
          "status": "WARNING",
          "count": 49999,
          "checked": 49999,
          "detail": "See errors.csv for every occurrence; samples are capped at 20."
        }
      },
      "metrics": {
        "first_event_time_ms": 1791238160414,
        "last_event_time_ms": 1791243186114,
        "columns": [
          "local_timestamp_us",
          "event_time_ms",
          "update_id",
          "best_bid",
          "best_ask",
          "mid_price",
          "spread",
          "bid_volume_5",
          "ask_volume_5",
          "obi_5"
        ],
        "min_event_time_ms": 1791238160414,
        "max_event_time_ms": 1791243186114,
        "local_minus_event_ms_min": "-375.662",
        "local_minus_event_ms_max": "-304.107",
        "max_obi_absolute_difference": "4.9999575165897716942E-9",
        "physical_lines": 50000,
        "unique_timestamps": 49999,
        "duplicate_timestamps": 0
      },
      "csv_header": [
        "local_timestamp_us",
        "event_time_ms",
        "update_id",
        "best_bid",
        "best_ask",
        "mid_price",
        "spread",
        "bid_volume_5",
        "ask_volume_5",
        "obi_5"
      ],
      "first_record_sample": [
        "1791238160061328",
        "1791238160414",
        "101078562473",
        "85865.17000000",
        "85865.18000000",
        "85865.17500000",
        "0.01000000",
        "1.52473000",
        "6.19305000",
        "-0.60487860"
      ],
      "errors_csv_header": [
        "path",
        "kind",
        "line",
        "record",
        "check",
        "status",
        "message"
      ],
      "errors_csv_records": 49999,
      "counts_by_check_status": [
        {
          "check": "local_event_clock_order",
          "status": "WARNING",
          "count": 49999
        }
      ],
      "counts_by_input_path": {
        "results/obi_market_data.csv": 49999
      },
      "error_message_validation_failures": [],
      "errors_count_mismatches": [],
      "markdown_warning_row_matches_json": true,
      "markdown_evidence": [
        {
          "line": 39,
          "text": "| local_event_clock_order | WARNING | 49999 | 49999 |"
        },
        {
          "line": 76,
          "text": "- CSV 本機時間尚未證明為 WebSocket 接收時間。local−event 為負記為 WARNING，不能解讀為負的網路延遲。"
        }
      ],
      "errors_record_first": 1,
      "errors_record_last": 49999,
      "errors_source_line_first": 2,
      "errors_source_line_last": 50000,
      "errors_negative_offset_ms_min": "-375.662",
      "errors_negative_offset_ms_max": "-304.107",
      "json_warning_key_line": 170,
      "absolute_path": "/home/jason/hft-realtime-codex/results/obi_market_data.csv",
      "audit_json_pointer": "/files/0/checks/local_event_clock_order",
      "evidence_positions": {
        "csv_header_line": 1,
        "csv_first_sample_line": 2,
        "audit_warning_key_line": 170,
        "markdown_warning_line": 39,
        "markdown_receive_limitation_line": 76,
        "errors_csv_header_line": 1,
        "errors_csv_data_lines": [
          2,
          50000
        ]
      }
    }
  ],
  "prior_report_wording_correction": {
    "path": "/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md",
    "line": 137,
    "prior_wording": "local_receive−exchange_event負差",
    "finding": "該 local_receive 稱呼超過既有證據；精確名稱應為 local_timestamp_us/1000 − event_time_ms。Audit Markdown 自身已限定尚未證明為 WebSocket receive time。本次僅在新報告更正解讀，舊報告保持不變。"
  },
  "methodology": {
    "errors_csv": "使用 Python 標準 csv.DictReader 串流全數 errors.csv；各 check/status 分組計數，逐一與 JSON 所有19 checks 的 count 比對，並驗證 warning message 的 Decimal 值有限且負、record/line 位置。未執行 tools/dataset_audit.py。",
    "csv_inputs": "本 agent 僅讀五 CSV header 與首筆；完整資料串流統計由 timestamp_stats agent 另行完成。",
    "read_mode": "主要 Python 內容讀取以 O_RDONLY|O_NOATIME；rg 搜尋為唯讀。",
    "parseability": "五份 Audit JSON 可完整解析；五份 errors.csv 可串流解析且列對應檢查無異常。歷史五 CSV Audit parse_errors 均0；本 agent 未重做所有市場欄位檢查。",
    "decimal_semantics": "所有 errors.csv message 對應有限負數，clock comparison 不採價格/OBI TOLERANCE。",
    "network_used": false,
    "cpp_executed": false,
    "tests_executed": false,
    "benchmark_executed": false,
    "existing_files_written": false
  },
  "limitations": [
    "Audit 證據足以確認警告公式/計數；無法單獨決定負值的根本物理原因。",
    "Windows/WSL、NTP、server/client clock offset、網路/queue delay 或調時等原因不得只由負值斷言。",
    "現在的 source 與歷史 CSV 精確 producer 關係尚無唯一 provenance；採樣位置需在整份 source_semantics 報告中區分候選路徑。",
    "首次大型證據輸出曾被工具截斷，已以相同唯讀命令重讀並在本次命令紀錄保留完整回傳；第一次嘗試和截斷狀態亦保留。",
    "exec_command 輸出為工具合併 stdout/stderr 串流，歷史讀取命令未分管道擷取；不虛構獨立 stderr。"
  ]
}''')
assert data['warning_total']['value']==sum(f['errors_csv_records'] for f in data['files'])
assert data['warning_total']['all_json_check_counts_match_errors_csv']
p=run/'warning_definition.json'
with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'created':str(p),'warning_total':data['warning_total']['value'],'file_warning_counts':[f['errors_csv_records'] for f in data['files']]},ensure_ascii=False))
PY
```

</details>

<details><summary>source_commands.json #1（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os
p='/mnt/c/Users/jason/.codex/attachments/389d5d0c-5b5b-4724-aa76-b0345624a520/貼上的文字.txt'
f=os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8')
print(f.read())
PY
```

</details>

<details><summary>source_commands.json #2（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,re
from pathlib import Path
root=Path('.')
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8',errors='replace') as f:return f.read()
print('AGENTS.md\n'+read('AGENTS.md'))
print('SOURCE MATCHES')
pat=re.compile(r'local_timestamp_us|event_time_ms|obi_market_data|CSVLogger|CsvLogger|csv_logger')
for p in sorted(Path('src').rglob('*')):
 if p.is_file() and p.suffix in ('.cpp','.h','.hpp'):
  s=read(p)
  hits=[f'{i}: {line}' for i,line in enumerate(s.splitlines(),1) if pat.search(line)]
  if hits:print(str(p)+'\n'+'\n'.join(hits))
PY
```

</details>

<details><summary>source_commands.json #3（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,re
from pathlib import Path
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8',errors='replace') as f:return f.read()
for path in ['src/csv_logger.h','src/orderbook_csv.cpp']:
 s=read(path); lines=s.splitlines(); print('\nFILE '+path)
 ranges=[(1,len(lines))] if path.endswith('.h') else [(1,220),(500,810)]
 for a,b in ranges:
  for i in range(a,min(b,len(lines))+1):print(f'{i}: {lines[i-1]}')
print('\nRELATED DOCS MATCHES')
pat=re.compile(r'obi_market_data|local_timestamp_us|event_time_ms|orderbook_csv|269.?284')
for p in sorted(Path('docs').glob('*.md')):
 s=read(p);hits=[f'{i}: {line}' for i,line in enumerate(s.splitlines(),1) if pat.search(line)]
 if hits:print(str(p)+'\n'+'\n'.join(hits))
PY
```

</details>

<details><summary>source_commands.json #4（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,re,json
from pathlib import Path
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8',errors='replace') as f:return f.read()
print('EXACT CORE RANGES')
s=read('src/orderbook_csv.cpp').splitlines()
for a,b in [(390,440),(810,910)]:
 for i in range(a,min(b,len(s))+1):print(f'src/orderbook_csv.cpp:{i}: {s[i-1]}')
print('LOGGER CALLSITE VARIANTS')
pat=re.compile(r'localTimestampUs|logger.push|eventTimeMs|system_clock::now|receiveTimestamp|recvTimestamp|recvTime|receiveTime|t_recv')
for p in sorted(Path('src').glob('*.cpp')):
 s=read(p);lines=s.splitlines()
 if 'AsyncCsvLogger logger' not in s:continue
 hits=[f'{i}: {line}' for i,line in enumerate(lines,1) if pat.search(line)]
 print(str(p)+'\n'+'\n'.join(hits))
print('DOC SHORT PROVENANCE MATCHES')
pat=re.compile(r'obi_market_data|local_timestamp_us|event_time_ms|orderbook_csv')
for p in sorted(Path('docs').glob('*.md')):
 hits=[]
 for i,line in enumerate(read(p).splitlines(),1):
  if len(line)<1300 and pat.search(line) and not line.lstrip().startswith(('"','- [','const ','import ','from ','|')):hits.append(f'{i}: {line}')
 if hits:print(str(p)+'\n'+'\n'.join(hits[:15]))
PY
```

</details>

<details><summary>source_commands.json #5（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,re
from pathlib import Path
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8',errors='replace') as f:return f.read()
for path,ranges in {
'src/live_baseline_cpu19_50000.cpp':[(45,82),(560,590),(695,735),(1010,1192)],
'src/fixed_batch_benchmark.cpp':[(1110,1208)],
'src/realtime_latency_benchmark.cpp':[(45,96),(700,732),(860,906),(995,1040),(1795,1815),(1950,2080)],
'src/batch_replay_capture_50000.cpp':[(1080,1100),(1150,1240)]}.items():
 lines=read(path).splitlines();print('\n'+path)
 for a,b in ranges:
  for i in range(a,min(b,len(lines))+1):print(f'{i}: {lines[i-1]}')
print('GENERATOR CLOCK/RECEIVE FIELD LOCATIONS')
pat=re.compile(r'event.eventTime|data.at\("E"\)|recv|receive|steady_clock|high_resolution_clock|Strategy|strategy|evaluate|sendOrder|sendTestnet')
for path in ['src/live_baseline_cpu19_50000.cpp','src/realtime_latency_benchmark.cpp','src/batch_replay_capture_50000.cpp']:
 print(path)
 for i,line in enumerate(read(path).splitlines(),1):
  if pat.search(line):print(f'{i}: {line}')
PY
```

</details>

<details><summary>source_commands.json #6（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,re
from pathlib import Path
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8',errors='replace') as f:return f.read()
for path,ranges in {'src/realtime_latency_benchmark.cpp':[(730,742),(1360,1403),(1426,1483),(1530,1558),(1588,1629)],'src/live_baseline_cpu19_50000.cpp':[(936,1009)],'src/fixed_batch_benchmark.cpp':[(1010,1060)]}.items():
 lines=read(path).splitlines();print('\n'+path)
 for a,b in ranges:
  for i in range(a,min(b,len(lines))+1):print(f'{i}: {lines[i-1]}')
print('BOUNDED HISTORICAL REPORT SEARCH')
for p in sorted(Path('docs').glob('*.md')):
 if p.name.startswith(('PHASE1_RECOVERY','PHASE1_V2_REPRODUCIBILITY')):continue
 hits=[]
 for i,line in enumerate(read(p).splitlines(),1):
  if len(line)<2000 and re.search(r'obi_market_data|local_timestamp_us|event_time_ms|orderbook_csv|provenance|來源版本',line):hits.append(f'{i}: {line}')
 if hits: print(str(p)+'\n'+'\n'.join(hits[:30]))
print('GENERATOR TIMESTAMP COUNTS')
for p in sorted(Path('src').glob('*.cpp')):
 s=read(p)
 if 'AsyncCsvLogger logger' in s:
  lines=s.splitlines(); ts=next((i for i,line in enumerate(lines,1) if 'long long localTimestampUs' in line),None)
  prior=[(i,line.strip()) for i,line in enumerate(lines,1) if ts and i<ts and any(x in line for x in ['orderBook.applyEvent','benchmarkObi =','generateSignal(benchmarkObi)','sendTickOrder','MarketSnapshot','ws.read(buffer)','data.at("E")'])]
  print(str(p),ts,prior)
PY
```

</details>

<details><summary>source_commands.json #7（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json,hashlib,re,datetime
from pathlib import Path
root=Path('/home/jason/hft-realtime-codex')
run=root/'artifacts/phase1_timestamp_review/20261018T212122Z'
def read(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8',errors='strict') as f:return f.read()
def evidence(rel,func,a,b):
 p=root/rel;s=read(p);lines=s.splitlines()
 return {'path':str(p),'function':func,'line_start':a,'line_end':b,'quoted_lines':[{'line':i,'text':lines[i-1]} for i in range(a,b+1)],'source_sha256':hashlib.sha256(s.encode()).hexdigest()}
generators=[]
for p in sorted((root/'src').glob('*.cpp')):
 s=read(p)
 if 'AsyncCsvLogger logger' not in s:continue
 lines=s.splitlines();ti=next(i for i,l in enumerate(lines,1) if 'long long localTimestampUs' in l);pi=next(i for i,l in enumerate(lines,1) if 'logger.push(snapshot)' in l);si=next(i for i,l in enumerate(lines,1) if 'MarketSnapshot snapshot{' in l)
 before='\n'.join(lines[:ti]);after_strategy='generateSignal(benchmarkObi)' in before;before_obi=not after_strategy
 hits=[{'line':i,'text':l} for i,l in enumerate(lines,1) if any(t in l for t in ['data.at("E")','ws.read(buffer)','event.localReceiveTimeMs =','event.localReceiveSteady =','event.enqueueTime =','orderBook.applyEvent','generateSignal(benchmarkObi)','logger.push(snapshot)'])]
 generators.append({'path':str(p),'sha256':hashlib.sha256(s.encode()).hexdigest(),'function':'main / parseDepthEvent / websocketReader','timestamp_evidence':evidence(str(p.relative_to(root)),'main',ti-3,ti+4),'snapshot_evidence':evidence(str(p.relative_to(root)),'main',si,pi),'supporting_lines':hits,'clock':'std::chrono::system_clock','unit':'microseconds since system_clock epoch','sampling_stage':'ORDER_BOOK_UPDATE_AFTER_OBI_BEFORE' if before_obi else 'ORDER_BOOK_OBI_STRATEGY_AFTER','possible_order_branch_before_csv':'sendTickOrder(' in before,'receive_value_used_as_csv_local':False,'claim_scope':'僅限本次讀取的現存source版本；不代表已證明任何指定歷史CSV的producer。'})
refs={
'logger_schema':evidence('src/csv_logger.h','AsyncCsvLogger::AsyncCsvLogger',89,116),
'logger_write':evidence('src/csv_logger.h','AsyncCsvLogger::writerLoop',42,84),
'logger_queue':evidence('src/csv_logger.h','AsyncCsvLogger::push',135,143),
'row_fields':evidence('src/csv_logger.h','MarketSnapshot',13,27),
'event_parse':evidence('src/orderbook_csv.cpp','parseDepthEvent',399,412),
'base_websocket':evidence('src/orderbook_csv.cpp','websocketReader',587,600),
'base_dequeue':evidence('src/orderbook_csv.cpp','main',783,786),
'base_timestamp':evidence('src/orderbook_csv.cpp','main',814,862),
'base_depthevent':evidence('src/orderbook_csv.cpp','DepthEvent',52,60),
'baseline_receive_like_enqueue':evidence('src/live_baseline_cpu19_50000.cpp','websocketReader',707,722),
'baseline_book_obi':evidence('src/live_baseline_cpu19_50000.cpp','main',979,1008),
'baseline_strategy':evidence('src/live_baseline_cpu19_50000.cpp','main',1018,1036),
'baseline_csv_timestamp':evidence('src/live_baseline_cpu19_50000.cpp','main',1142,1189),
'realtime_receive':evidence('src/realtime_latency_benchmark.cpp','websocketReader',711,736),
'realtime_event_fields':evidence('src/realtime_latency_benchmark.cpp','DepthEvent',65,75),
'realtime_optional_order_before_csv':evidence('src/realtime_latency_benchmark.cpp','main',1533,1557),
'realtime_receive_durations':evidence('src/realtime_latency_benchmark.cpp','main',1596,1623),
'realtime_csv_timestamp':evidence('src/realtime_latency_benchmark.cpp','main',2026,2073)
}
files=['results/obi_market_data_20260827_session1.csv','results/obi_market_data_20260827_session2.csv','results/obi_market_data_20260827_session3.csv','results/obi_market_data_test_20260827.csv','results/obi_market_data.csv']
obj={
'schema_version':1,'run_id':'20261018T212122Z','generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'working_directory':str(root),'analysis_kind':'READ_ONLY_STATIC_SOURCE_SEMANTICS','source_generator_count':len(generators),
'summary_zh':'目前讀到的23個AsyncCsvLogger產生路徑，其CSV local_timestamp_us均是在消費端Order Book更新後重新讀system_clock並轉microseconds，非WebSocket讀取完成時的receive timestamp。base orderbook_csv在OBI前取時，多數benchmark來源在OBI/Strategy後取時，部分realtime來源更可能在下單/ACK條件分支後取時。五個歷史CSV沒有足夠exact producer/source/binary版本關聯證據，因此不能將現在source的採樣點無條件套用到歷史檔案。',
'current_source_confirmed':{
'event_time_ms':{'status':'CONFIRMED','origin':'Binance depth JSON欄位 E 經parseDepthEvent存入DepthEvent::eventTime，MarketSnapshot的第二欄直接接收event.eventTime，writerLoop原值寫出event_time_ms。','references':['event_parse','base_timestamp','logger_write','logger_schema'],'conversion':'現存來源沒有對E做時區轉換或倍率調整；eventTimeMs/CSV schema將它標成毫秒。'},
'local_timestamp_us':{'status':'CONFIRMED','clock':'std::chrono::system_clock','unit':'microseconds','expression':'duration_cast<microseconds>(system_clock::now().time_since_epoch()).count()','references':['base_timestamp','baseline_csv_timestamp','realtime_csv_timestamp'],'base_order':['ws.read完成','JSON parse','EventQueue入列','主執行緒出列','Order Book更新','取得system_clock時間','最佳價/mid/spread/五檔總量/OBI','MarketSnapshot建構','logger.push入CSV queue','writerLoop非同步原值輸出'],'is_receive_time':False,'is_csv_write_time':False,'is_processing_duration':False,'is_tick_to_trade_duration':False},
'logger_timestamp_handling':{'status':'CONFIRMED','text':'logger.push只複製MarketSnapshot到queue；writerLoop不呼叫clock、不重新取timestamp，保存producer傳入之數值。非同步落盤可能晚於localTimestampUs。','references':['logger_queue','logger_write']},
'receive_timestamp_persistence':{'status':'NOT_IN_THIS_CSV_SCHEMA','text':'所有23個已檢查AsyncCsvLogger路徑，MarketSnapshot只使用重新取得的localTimestampUs與event.eventTime。realtime_latency_benchmark等有ws.read後的localReceiveTimeMs與localReceiveSteady，但不把這兩欄放入MarketSnapshot，故這個十欄CSV無法還原真實receive時間。此結論不否定其他console或不同資料格式可能含衍生延遲。','references':['row_fields','realtime_receive','realtime_csv_timestamp','realtime_receive_durations']},
'clock_domains':{'status':'CONFIRMED_SEPARATE_SOURCES','event':'交易所訊息內E','local':'本機system_clock','text':'相同epoch/單位可比較不表示同一實體時鐘或同步。以exchange E與local wall clock相減，結果混合clock offset、資料傳遞及logger採樣前處理/排隊等待。這不是單獨可識別的網路延遲。','references':['event_parse','base_timestamp','realtime_receive']}
},
'historical_csv_provenance':{'status':'UNKNOWN','inspected_evidence_scope':'現存src內包含csv_logger.h或相關欄位的來源、既有docs內相關timestamp/CSV敘述；另引用本輪稽核子任務所驗證的五個同十欄schema。未發現能把五個CSV逐一綁定到生成時binary hash、source hash與session metadata的證據。此為所查範圍的缺口，非宣稱不存在任何外部證據。','why_ambiguous':'23個來源共用AsyncCsvLogger及results/obi_market_data.csv；四個session/test檔名未由所見CSV logger硬編碼產生。檔名、欄位相同或49999列等相似性不能證明exact producer版本。','is_true_receive_time':'UNPROVEN_DO_NOT_USE_AS_RECEIVE','correct_answer_zh':'五個歷史CSV的local_timestamp_us是否為真實receive time：未證實，必須禁止當作receive使用。現存23個候選產生路徑的該欄則已確認不是receive time。','requires_future_evidence':['歷史生成命令與session清單','每session產生binary/source hash或commit','clock同步/offset量測紀錄','獨立持久化ws.read後receive timestamp']},
'cause_assessment':[
{'factor':'Windows／WSL clock offset','status':'UNKNOWN','text':'目前位於Linux/WSL不能證明歷史錄製執行環境或當時host/guest clock offset；負差不是確認證據。'},
{'factor':'NTP同步','status':'UNKNOWN','text':'沒有歷史NTP/PTP/chrony/時鐘校正紀錄，不能將逐步漂移或跳變直接歸因NTP。'},
{'factor':'system_clock調整','susceptibility':'POSSIBLE_BY_CLOCK_CHOICE','historical_occurrence':'UNKNOWN','text':'當前source選system_clock而非steady_clock；沒有獨立同時取得的monotonic值或clock調整紀錄，單靠兩欄不能分離wall-clock調整、排隊與錄製中斷。'},
{'factor':'時區轉換','current_source_status':'NO_EXPLICIT_CONVERSION_IN_CHECKED_PATH','historical_cause':'UNKNOWN','text':'time_since_epoch整數輸出路徑沒有localtime/gmtime/tz位移。不得把UTC與本地顯示時區混為此負差原因；歷史producer不同版本仍未確證。'},
{'factor':'不同epoch','current_source_status':'EXCHANGE_E_VS_IMPLEMENTATION_SYSTEM_CLOCK_EPOCH','historical_cause':'UNKNOWN','text':'source使用system_clock::time_since_epoch，未手動加減epoch偏移；C++程式本身未保存clock epoch規格/歷史runtime。資料單位與量級檢核可支持一致性，不能僅憑C++17型別宣稱任何平台epoch必然相同。'},
{'factor':'不同單位','current_source_status':'EXPLICIT_LOCAL_US_AND_SCHEMA_EVENT_MS','historical_cause':'NO_POSITIVE_EVIDENCE_OF_UNIT_MISMATCH','text':'local明確duration_cast<microseconds>，eventTimeMs與CSV event_time_ms皆標毫秒。兩欄直接相減必須將ms乘1000或us除1000；警告Audit已作等價轉換，不能把存在單位差異本身判為schema錯誤。'},
{'factor':'local取時晚於receive','current_source_status':'CONFIRMED','negative_delta_causal_status':'DOES_NOT_BY_ITSELF_EXPLAIN_NEGATIVE_SIGN','text':'取樣更晚一般增加local−event；它能證明延遲解釋錯誤，不能單獨解釋負值成因。'},
{'factor':'資料損壞','status':'NOT_PROVEN_BY_NEGATIVE_DELTA','text':'不得只因delta<0標記POSSIBLE_DATA_CORRUPTION；資料解析/單調/缺口結果由本輪其他輸出提供。'}],
'per_csv_classification_candidates':[{'relative_path':p,'principal':'INSUFFICIENT_EVIDENCE','principal_reason':'負clock delta根因及此歷史CSV的exact producer/clock同步狀態未確證；不把已確認的負值現象當成已確認clock offset來源。','secondary':[{'classification':'LOCAL_TIMESTAMP_NOT_RECEIVE_TIME','applicability':'CONDITIONAL_ON_MATCHING_CURRENT_GENERATOR','reason':'本次讀取的23個候選產生路徑均不是receive timestamp；歷史producer版本尚未確證。'}],'other_classifications':'DATA_GAP、EVENT_TIME_NON_MONOTONIC、LOCAL_TIME_NON_MONOTONIC應依本輪逐檔串流結果決定，不由靜態source推定。'} for p in files],
'field_use_constraints_zh':['event time的離線排序/標籤可用性須以本輪逐檔單調性、缺口、schema及價格資料檢核決定；source不能單獨作PASS。','local_timestamp_us不得作Local Receive Time、網路延遲、本機處理時間或Tick-to-Trade延遲；兩種時鐘來源且缺少持久化階段邊界。','本輪未建立field_usage_matrix或phase2_time_rules，交由主代理依所有證據決定。'],
'future_recorder_recommendation_only_zh':'未來經批准後另存exchange_event_time、ws.read完成後local_receive_time、parse_complete_time、book_update_complete_time、decision_complete_time，並為每個欄位記錄clock source、epoch與單位；本機duration另用同一steady_clock域。歷史五CSV不可事後重建缺失receive timestamp。',
'evidence':refs,'source_generators':generators,
'safety':{'cpp_executed':False,'network':False,'benchmark':False,'testnet':False,'trading':False,'existing_file_modified':False,'package_install':False,'scope':'僅唯讀來源與相關既有文件，新增本run JSON證據。'}
}
out=run/'source_timestamp_semantics.json'
with out.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(out),'source_generators':len(generators),'bytes':out.stat().st_size,'historical_provenance':'UNKNOWN','principal_candidate':'INSUFFICIENT_EVIDENCE'},ensure_ascii=False))
PY
```

</details>

<details><summary>stats_commands.json #1（exit 0）</summary>

```bash
cat /mnt/c/Users/jason/.codex/attachments/389d5d0c-5b5b-4724-aa76-b0345624a520/貼上的文字.txt
```

</details>

<details><summary>stats_commands.json #2（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json
root='/home/jason/hft-realtime-codex'
paths=['results/obi_market_data_20260827_session1.csv','results/obi_market_data_20260827_session2.csv','results/obi_market_data_20260827_session3.csv','results/obi_market_data_test_20260827.csv','results/obi_market_data.csv']
for rel in paths:
 fd=os.open(root+'/'+rel,os.O_RDONLY|os.O_NOATIME)
 with os.fdopen(fd,'r') as f: print(json.dumps({'path':rel,'size':os.stat(root+'/'+rel).st_size,'header':f.readline().strip(),'sample':f.readline().strip()}))
for path,dirs,files in os.walk(root+'/artifacts/phase1_v2/20261018T210029Z'):
 for f in files:
  if f in ('report.json','audit_report.json') or 'audit' in f:print(os.path.relpath(path+'/'+f,root))
PY
```

</details>

<details><summary>stats_commands.json #3（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json
root='/home/jason/hft-realtime-codex'
for stem in ['obi_market_data_20260827_session1','obi_market_data_20260827_session2','obi_market_data_20260827_session3','obi_market_data_test_20260827','obi_market_data']:
 p=root+'/artifacts/dataset_audit/phase1v2_20261018T210029Z_'+stem+'/audit_report.json'
 fd=os.open(p,os.O_RDONLY|os.O_NOATIME)
 with os.fdopen(fd) as f: d=json.load(f)
 print(json.dumps({'report':p,'data':d},ensure_ascii=False))
PY
```

</details>

<details><summary>stats_commands.json #4（exit 0）</summary>

```bash
python3 -B - <<'PY'
from pathlib import Path
p=Path('/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_statistics.py')
source="#!/usr/bin/env python3\n\"\"\"唯讀 CSV 串流時間審查；輸出只可獨占建立在指定的新 run 內。\"\"\"\nimport csv, datetime as dt, hashlib, json, os, re, sys, time\nfrom collections import Counter\nfrom decimal import Decimal, InvalidOperation\nfrom fractions import Fraction\nfrom pathlib import Path\n\nROOT = Path('/home/jason/hft-realtime-codex')\nRUN = ROOT / 'artifacts/phase1_timestamp_review/20261018T212122Z'\nRUN_ID = RUN.name\nSTEMS = ['obi_market_data_20260827_session1','obi_market_data_20260827_session2','obi_market_data_20260827_session3','obi_market_data_test_20260827','obi_market_data']\nHEADER = ['local_timestamp_us','event_time_ms','update_id','best_bid','best_ask','mid_price','spread','bid_volume_5','ask_volume_5','obi_5']\nINTEGER = re.compile(r'[0-9]+\\Z')\nEPOCH = dt.datetime(1970,1,1,tzinfo=dt.timezone.utc)\nSTART = time.perf_counter()\nQUANTILE_METHOD = '精確 Type 7：h=(n-1)*p，排序後線性插值；索引與插值使用 Fraction。僅最終 JSON 的 *_value 欄轉為 float，*_exact 保留有理數，未對 epoch 作 float 相減。'\nMETHOD = {\n 'input_method':'以 csv.reader(strict=True) 逐筆讀取；只保留 timestamp/delta 整數陣列、unique timestamp sets、統計及異常定位，沒有載入完整 CSV table。',\n 'formula_gate':'已由 definition agent 確認 tools/dataset_audit.py audit_csv() L329–336 與五檔 schema：Decimal(local_timestamp_us)/1000-event_time_ms <0，單位 ms；整數等價式 delta_us=local_timestamp_us-event_time_ms*1000。',\n 'quantile_method':QUANTILE_METHOD,\n 'row_number':'record 是自 1 起算的資料列，不含 header；physical_line 為 csv.reader.line_num，以 1 起算、含 header。',\n 'parseable_record':'10 欄；前三欄非負十進位整數；後七欄 Decimal 有限數；這是讀取/數值語法檢查，不重跑全部市場業務規則。',\n 'timestamp_invalid':'非空但非非負十進位整數；missing 與 invalid 互斥。row counts 與 cell counts 分開。',\n 'duplicates':'重複次數=非首次出現的 timestamp 數；adjacent_zero_count 另算真正相鄰紀錄。',\n 'interval_adjacency':'只算相鄰原始資料列皆有效的欄位；無效列不橋接。全部有效時共 N-1 個間隔。',\n 'offset_blocks':'固定1000個原始 record 一個區塊，逐塊 delta median；最後區塊可不足1000。未藉此推定 NTP。',\n 'segment_rule':'僅以 event interval>1000ms 或 event 倒退建立候選研究分段；這是分析規則，非已證明的 collector Session 邊界。',\n 'clock_causality':'delta 跳變及 local 長間隔是觀測事實；沒有 OS 時鐘同步日誌、原生 receive time 或 monotonic counter，不等同證明 system_clock 調整。'\n}\ndef open_ro(path, binary=False):\n    fd = os.open(path, os.O_RDONLY | getattr(os,'O_NOATIME',0))\n    return os.fdopen(fd, 'rb' if binary else 'r', **({} if binary else {'encoding':'utf-8','newline':''}))\ndef read_json(path):\n    with open_ro(path) as f:return json.load(f)\ndef sha(path):\n    h=hashlib.sha256()\n    with open_ro(path,True) as f:\n        for chunk in iter(lambda:f.read(1024*1024), b''):h.update(chunk)\n    return h.hexdigest()\ndef num(value):\n    q=Fraction(value)\n    return q.numerator if q.denominator==1 else float(q)\ndef exact(value):\n    q=Fraction(value)\n    return {'numerator':q.numerator,'denominator':q.denominator}\ndef quantile_sorted(values, pct):\n    if not values:return None\n    h=Fraction((len(values)-1)*pct,100)\n    i=h.numerator//h.denominator\n    return Fraction(values[i]) if i==len(values)-1 else Fraction(values[i])+(h-i)*(values[i+1]-values[i])\ndef distribution(values,unit):\n    if not values:return {'count':0,'unit':unit}\n    v=sorted(values);mean=Fraction(sum(v),len(v))\n    out={'count':len(v),'unit':unit,'min':v[0],'max':v[-1],'mean':num(mean),'mean_exact':exact(mean)}\n    for p in [1,5,25,50,75,95,99]:\n        q=quantile_sorted(v,p);out['p'+str(p)]=num(q);out['p'+str(p)+'_exact']=exact(q)\n    out['median']=out['p50']\n    return out\ndef interval_dist(values,unit):\n    out=distribution(values,unit);factor=1 if unit=='ms' else 1000\n    out.update({'zero_count':sum(x==0 for x in values),'negative_count':sum(x<0 for x in values),\n      **{'greater_than_'+str(t)+'ms_count':sum(x>t*factor for x in values) for t in [100,200,500,1000]},\n      'exactly_100ms_count':sum(x==100*factor for x in values),\n      'within_95_to_105ms_inclusive_count':sum(95*factor<=x<=105*factor for x in values),\n      'within_90_to_110ms_inclusive_count':sum(90*factor<=x<=110*factor for x in values),\n      'most_common_intervals':[{'value':x,'count':n} for x,n in Counter(values).most_common(20)]})\n    return out\ndef utc(v,unit):\n    if v is None:return None\n    micro=v*1000 if unit=='ms' else v\n    return (EPOCH+dt.timedelta(microseconds=micro)).isoformat(timespec='microseconds').replace('+00:00','Z')\ndef location(record,line,event,local,delta=None):\n    r={'record':record,'physical_line':line,'event_time_ms':event,'local_timestamp_us':local}\n    if delta is not None:r['delta_us']=delta\n    return r\ndef transition(prev,cur):\n    e=cur['event_time_ms']-prev['event_time_ms'] if None not in (cur['event_time_ms'],prev['event_time_ms']) else None\n    l=cur['local_timestamp_us']-prev['local_timestamp_us'] if None not in (cur['local_timestamp_us'],prev['local_timestamp_us']) else None\n    d=cur.get('delta_us',None)-prev.get('delta_us',None) if cur.get('delta_us') is not None and prev.get('delta_us') is not None else None\n    return {'before':prev,'after':cur,'event_interval_ms':e,'local_interval_us':l,'delta_jump_us':d}\ndef write_json(name,data):\n    with (RUN/name).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\\n')\ndef progress(stem,n,total):\n    elapsed=time.perf_counter()-START\n    print(json.dumps({'progress_file':stem,'records':n,'expected_records_from_v2_audit':total,'percent':round(n*100/total,2) if total else None,'elapsed_s':round(elapsed,3),'estimated_file_remaining_s':round((total-n)/max(n,1)*(time.perf_counter()-file_start),3)},ensure_ascii=False),flush=True)\n\nassert Path.cwd()==ROOT\nfor output in ['csv_timestamp_summary.json','csv_timestamp_summary.csv','clock_delta_statistics.json','timestamp_gap_analysis.json']:\n    if (RUN/output).exists():raise SystemExit('STOP output exists: '+output)\nsummaries=[]; clocks=[]; gaps=[]\nfor stem in STEMS:\n    file_start=time.perf_counter()\n    rel='results/'+stem+'.csv';path=ROOT/rel\n    report=ROOT/'artifacts/dataset_audit'/('phase1v2_20261018T210029Z_'+stem)/'audit_report.json'\n    audited=read_json(report)['files'][0]\n    digest=sha(path)\n    if digest!=audited['sha256']:raise SystemExit('STOP hash mismatches Phase1v2: '+rel)\n    event_values=[];local_values=[];delta_values=[];event_intervals=[];local_intervals=[]\n    event_seen=set();local_seen=set()\n    counts=Counter();missing=Counter();invalid=Counter();negative_runs=[];negative_run=None\n    first=None;last=None;first_negative=None;last_negative=None\n    previous=None;max_e=None;max_l=None;max_dplus=None;max_dminus=None\n    large_events=[];large_locals=[];large_delta_jumps=[];backwards_event=[];backwards_local=[];parse_samples=[]\n    segments=[];segment=None;blocks=[];block_deltas=[];block_start=None;block_last=None\n    sums=Counter();x0=None\n    with open_ro(path) as f:\n        reader=csv.reader(f,strict=True)\n        header=next(reader)\n        if header!=HEADER:raise SystemExit('STOP schema mismatch: '+rel)\n        for record,row in enumerate(reader,1):\n            counts['total_rows']+=1;line=reader.line_num\n            row_errors=[];event=None;local=None\n            if len(row)!=len(HEADER):row_errors.append('column_count')\n            rowmap=dict(zip(HEADER,row))\n            row_missing=False;row_invalid=False\n            for field in ['event_time_ms','local_timestamp_us']:\n                value=rowmap.get(field,'').strip()\n                if not value:missing[field]+=1;row_missing=True;row_errors.append(field+'_missing')\n                elif not INTEGER.fullmatch(value):invalid[field]+=1;row_invalid=True;row_errors.append(field+'_invalid')\n                elif field=='event_time_ms':event=int(value)\n                else:local=int(value)\n            counts['rows_missing_timestamp']+=int(row_missing)\n            counts['rows_invalid_timestamp']+=int(row_invalid)\n            u=rowmap.get('update_id','').strip()\n            if not INTEGER.fullmatch(u):row_errors.append('update_id_invalid')\n            for field in HEADER[3:]:\n                try:\n                    val=Decimal(rowmap.get(field,'').strip())\n                    if not val.is_finite():row_errors.append(field+'_nonfinite')\n                except InvalidOperation:row_errors.append(field+'_invalid')\n            if row_errors:\n                counts['parse_errors']+=1\n                if len(parse_samples)<20:parse_samples.append({'record':record,'physical_line':line,'errors':row_errors})\n            else:counts['parseable_rows']+=1\n            delta=local-event*1000 if event is not None and local is not None else None\n            cur=location(record,line,event,local,delta)\n            if first is None:first=cur\n            last=cur\n            if event is not None:\n                counts['event_duplicate_nonfirst']+=int(event in event_seen);event_seen.add(event);event_values.append(event)\n            if local is not None:\n                counts['local_duplicate_nonfirst']+=int(local in local_seen);local_seen.add(local);local_values.append(local)\n            if delta is not None:\n                delta_values.append(delta)\n                counts['negative_delta']+=int(delta<0);counts['zero_delta']+=int(delta==0);counts['positive_delta']+=int(delta>0)\n                if x0 is None:x0=event\n                x=event-x0\n                sums['n']+=1;sums['x']+=x;sums['y']+=delta;sums['xx']+=x*x;sums['xy']+=x*delta\n                if block_start is None:block_start=cur\n                block_last=cur;block_deltas.append(delta)\n            if delta is not None and delta<0:\n                if first_negative is None:first_negative=cur\n                last_negative=cur\n                if negative_run is None:negative_run={'first':cur,'last':cur,'records':0,'min_delta_us':delta,'max_delta_us':delta}\n                negative_run['last']=cur;negative_run['records']+=1\n                negative_run['min_delta_us']=min(negative_run['min_delta_us'],delta);negative_run['max_delta_us']=max(negative_run['max_delta_us'],delta)\n            elif negative_run is not None:negative_runs.append(negative_run);negative_run=None\n            boundary=False\n            if previous is not None:\n                tr=transition(previous,cur);ei=tr['event_interval_ms'];li=tr['local_interval_us'];dj=tr['delta_jump_us']\n                if ei is not None:\n                    event_intervals.append(ei)\n                    if max_e is None or ei>max_e['event_interval_ms']:max_e=tr\n                    if ei<0:backwards_event.append(tr)\n                    if ei>1000:large_events.append(tr)\n                    boundary=ei<0 or ei>1000\n                else:counts['skipped_event_adjacent_pairs']+=1;boundary=True\n                if li is not None:\n                    local_intervals.append(li)\n                    if max_l is None or li>max_l['local_interval_us']:max_l=tr\n                    if li<0:backwards_local.append(tr)\n                    if li>1000000:large_locals.append(tr)\n                else:counts['skipped_local_adjacent_pairs']+=1\n                if dj is not None:\n                    if dj>0 and (max_dplus is None or dj>max_dplus['delta_jump_us']):max_dplus=tr\n                    if dj<0 and (max_dminus is None or dj<max_dminus['delta_jump_us']):max_dminus=tr\n                    if abs(dj)>100000:large_delta_jumps.append(tr)\n                else:counts['skipped_delta_adjacent_pairs']+=1\n            if segment is None or boundary:\n                if segment is not None:segments.append(segment)\n                segment={'first':cur,'last':cur,'records':1}\n            else:segment['last']=cur;segment['records']+=1\n            if record%1000==0:\n                if block_deltas:blocks.append({'first':block_start,'last':block_last,'distribution_us':distribution(block_deltas,'us'),'negative_count':sum(x<0 for x in block_deltas)})\n                block_deltas=[];block_start=None;block_last=None\n            previous=cur\n            if record%25000==0:progress(stem,record,audited['records'])\n        physical_lines=reader.line_num\n    if negative_run is not None:negative_runs.append(negative_run)\n    if segment is not None:segments.append(segment)\n    if block_deltas:blocks.append({'first':block_start,'last':block_last,'distribution_us':distribution(block_deltas,'us'),'negative_count':sum(x<0 for x in block_deltas)})\n    n=counts['total_rows']\n    if n!=audited['records'] or counts['negative_delta']!=audited['checks']['local_event_clock_order']['count']:raise SystemExit('STOP row/warning mismatch: '+rel)\n    summary={'relative_path':rel,'sha256':digest,'size_bytes':path.stat().st_size,'columns':header,\n      'total_rows':n,'parseable_rows':counts['parseable_rows'],'parse_errors':counts['parse_errors'],'parse_error_samples':parse_samples,'physical_lines':physical_lines,\n      'valid_event_timestamp_count':len(event_values),'valid_local_timestamp_count':len(local_values),'valid_delta_count':len(delta_values),\n      'first_record':first,'last_record':last,\n      'event_time_ms_first':event_values[0] if event_values else None,'event_time_ms_last':event_values[-1] if event_values else None,\n      'local_timestamp_us_first':local_values[0] if local_values else None,'local_timestamp_us_last':local_values[-1] if local_values else None,\n      'event_time_ms_monotonic_nondecreasing':not backwards_event and not counts['skipped_event_adjacent_pairs'],\n      'local_timestamp_us_monotonic_nondecreasing':not backwards_local and not counts['skipped_local_adjacent_pairs'],\n      'event_time_ms_backward_count':len(backwards_event),'local_timestamp_us_backward_count':len(backwards_local),\n      'event_time_ms_duplicate_nonfirst_count':counts['event_duplicate_nonfirst'],'local_timestamp_us_duplicate_nonfirst_count':counts['local_duplicate_nonfirst'],\n      'event_time_ms_adjacent_duplicate_count':sum(x==0 for x in event_intervals),'local_timestamp_us_adjacent_duplicate_count':sum(x==0 for x in local_intervals),\n      'missing_timestamp_cell_count':sum(missing.values()),'missing_timestamp_by_field':dict(missing),'missing_timestamp_row_count':counts['rows_missing_timestamp'],\n      'invalid_timestamp_cell_count':sum(invalid.values()),'invalid_timestamp_by_field':dict(invalid),'invalid_timestamp_row_count':counts['rows_invalid_timestamp'],\n      'negative_delta_count':counts['negative_delta'],'zero_delta_count':counts['zero_delta'],'positive_delta_count':counts['positive_delta'],\n      'negative_delta_ratio':num(Fraction(counts['negative_delta'],len(delta_values))) if delta_values else None,\n      'negative_delta_ratio_exact':exact(Fraction(counts['negative_delta'],len(delta_values))) if delta_values else None,\n      'event_time_utc_range':{'first':utc(event_values[0],'ms'),'last':utc(event_values[-1],'ms'),'min':utc(min(event_values),'ms'),'max':utc(max(event_values),'ms')},\n      'local_time_utc_range':{'first':utc(local_values[0],'us'),'last':utc(local_values[-1],'us'),'min':utc(min(local_values),'us'),'max':utc(max(local_values),'us')},\n      'v2_audit_path':str(report),'matches_v2_audit_sha256':digest==audited['sha256'],'matches_v2_audit_records':n==audited['records'],\n      'matches_v2_audit_negative_count':counts['negative_delta']==audited['checks']['local_event_clock_order']['count']}\n    ds=distribution(delta_values,'us')\n    denominator=sums['n']*sums['xx']-sums['x']**2\n    slope=Fraction(sums['n']*sums['xy']-sums['x']*sums['y'],denominator) if denominator else None\n    block_changes=[{'before_block':i,'after_block':i+1,'before_first_record':blocks[i-1]['first']['record'],'after_first_record':blocks[i]['first']['record'],\n      'median_delta_change_us':blocks[i]['distribution_us']['median']-blocks[i-1]['distribution_us']['median']} for i in range(1,len(blocks))]\n    clock={'relative_path':rel,'formula':'delta_us = local_timestamp_us - event_time_ms * 1000','unit':'us','distribution':ds,\n      'negative_count':counts['negative_delta'],'zero_count':counts['zero_delta'],'positive_count':counts['positive_delta'],'negative_ratio':summary['negative_delta_ratio'],\n      'first_negative':first_negative,'last_negative':last_negative,'max_positive_adjacent_delta_jump':max_dplus,'max_negative_adjacent_delta_jump':max_dminus,\n      'negative_run_count':len(negative_runs),'negative_runs':negative_runs,'first_delta_us':delta_values[0],'last_delta_us':delta_values[-1],\n      'first_to_last_delta_change_us':delta_values[-1]-delta_values[0],\n      'block_records':1000,'blocks':blocks,'block_median_changes':block_changes,\n      'largest_absolute_block_median_change':max(block_changes,key=lambda x:abs(x['median_delta_change_us'])) if block_changes else None,\n      'ols_delta_drift_us_per_exchange_second':num(slope*1000) if slope is not None else None,\n      'ols_delta_drift_exact_us_per_exchange_second':exact(slope*1000) if slope is not None else None,\n      'ols_warning':'描述性整體斜率，不可用於證明 clock drift 或 NTP；突變/佇列阻塞等亦可造成斜率。',\n      'adjacent_delta_jumps_abs_greater_than_100ms':large_delta_jumps,\n      'negative_pattern':'全檔負差' if counts['negative_delta']==len(delta_values) else '幾乎全檔負差，存在非負區段' if counts['negative_delta']/len(delta_values)>0.95 else '混合區段，見 negative_runs',\n      'system_clock_adjustment_cause':'UNKNOWN'}\n    gap={'relative_path':rel,'event_intervals':interval_dist(event_intervals,'ms'),'local_intervals':interval_dist(local_intervals,'us'),\n      'max_event_gap':max_e,'max_local_gap':max_l,'event_gaps_greater_than_1000ms':large_events,'local_gaps_greater_than_1000ms':large_locals,\n      'event_backward_transitions':backwards_event,'local_backward_transitions':backwards_local,\n      'event_time_residue_mod_100ms_counts':{str(k):v for k,v in sorted(Counter(x%100 for x in event_values).items())},\n      'candidate_segments_event_gap_gt_1000ms_or_backward':segments,'candidate_segment_count':len(segments),\n      'cross_session_inside_file':'UNKNOWN；CSV 沒有持久化 session_id，缺口不單獨證明跨 Session。',\n      'skipped_invalid_adjacent_pairs':{'event':counts['skipped_event_adjacent_pairs'],'local':counts['skipped_local_adjacent_pairs'],'delta':counts['skipped_delta_adjacent_pairs']}}\n    summaries.append(summary);clocks.append(clock);gaps.append(gap)\n    progress(stem,n,audited['records'])\nranges=sorted(summaries,key=lambda f:f['event_time_ms_first'])\ncross=[]\nfor a,b in zip(ranges,ranges[1:]):\n    cross.append({'before_file':a['relative_path'],'after_file':b['relative_path'],'before_last_event_ms':a['event_time_ms_last'],'after_first_event_ms':b['event_time_ms_first'],\n     'between_file_event_gap_ms':b['event_time_ms_first']-a['event_time_ms_last'],'overlap':b['event_time_ms_first']<=a['event_time_ms_last'],\n     'cross_file_labels':'NOT_ALLOWED；各檔案視為獨立 Session；時間差不是檔內缺失資料列。'})\nbase={'schema_version':'1.0','run_id':RUN_ID,'created_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'method':METHOD}\nwrite_json('csv_timestamp_summary.json',{**base,'files':summaries,'total_rows':sum(x['total_rows'] for x in summaries),'total_negative_delta_count':sum(x['negative_delta_count'] for x in summaries),'all_matches_v2_audit':all(x['matches_v2_audit_sha256'] and x['matches_v2_audit_records'] and x['matches_v2_audit_negative_count'] for x in summaries)})\nwrite_json('clock_delta_statistics.json',{**base,'files':clocks})\nwrite_json('timestamp_gap_analysis.json',{**base,'files':gaps,'sessions_in_event_time_order':[{k:s[k] for k in ['relative_path','event_time_utc_range','local_time_utc_range']} for s in ranges],'between_file_session_gaps':cross,'maximum_within_file_event_gap':max(({'relative_path':g['relative_path'],**g['max_event_gap']} for g in gaps),key=lambda x:x['event_interval_ms'])})\nflat=[]\nfor s,c,g in zip(summaries,clocks,gaps):\n    row={k:v for k,v in s.items() if not isinstance(v,(dict,list))}\n    row['columns']='|'.join(s['columns'])\n    row.update({'delta_'+k:v for k,v in c['distribution'].items() if not isinstance(v,dict)})\n    row.update({'first_negative_record':c['first_negative']['record'] if c['first_negative'] else None,'first_negative_physical_line':c['first_negative']['physical_line'] if c['first_negative'] else None,\n      'last_negative_record':c['last_negative']['record'] if c['last_negative'] else None,'last_negative_physical_line':c['last_negative']['physical_line'] if c['last_negative'] else None,\n      'max_positive_delta_jump_us':c['max_positive_adjacent_delta_jump']['delta_jump_us'] if c['max_positive_adjacent_delta_jump'] else None,\n      'max_negative_delta_jump_us':c['max_negative_adjacent_delta_jump']['delta_jump_us'] if c['max_negative_adjacent_delta_jump'] else None,\n      'max_event_gap_ms':g['max_event_gap']['event_interval_ms'],'max_local_gap_us':g['max_local_gap']['local_interval_us']})\n    for which in ['event','local']:\n        for key,value in g[which+'_intervals'].items():\n            if not isinstance(value,(dict,list)):row[which+'_interval_'+key]=value\n    flat.append(row)\nwith (RUN/'csv_timestamp_summary.csv').open('x',encoding='utf-8',newline='') as f:\n    writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)\nprint(json.dumps({'status':'COMPLETE','run_id':RUN_ID,'total_rows':sum(x['total_rows'] for x in summaries),'total_negative_delta_count':sum(x['negative_delta_count'] for x in summaries),'elapsed_s':time.perf_counter()-START,'outputs':['csv_timestamp_summary.json','csv_timestamp_summary.csv','clock_delta_statistics.json','timestamp_gap_analysis.json']},ensure_ascii=False),flush=True)\n"
compile(source,str(p),'exec')
with p.open('x',encoding='utf-8') as f:f.write(source)
print('CREATED AND SYNTAX PASS',p)
PY
```

</details>

<details><summary>stats_commands.json #5（exit 0）</summary>

```bash
python3 -B artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_statistics.py
```

</details>

<details><summary>stats_commands.json #6（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json
root='/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/'
def load(n):
 fd=os.open(root+n,os.O_RDONLY|os.O_NOATIME)
 with os.fdopen(fd) as f:return json.load(f)
s=load('csv_timestamp_summary.json');c=load('clock_delta_statistics.json');g=load('timestamp_gap_analysis.json')
for a,b,d in zip(s['files'],c['files'],g['files']):
 print(json.dumps({'summary':a,'delta':{k:v for k,v in b.items() if k not in ['blocks','block_median_changes','negative_runs','adjacent_delta_jumps_abs_greater_than_100ms']},'negative_runs':b['negative_runs'],'delta_large_jumps_count':len(b['adjacent_delta_jumps_abs_greater_than_100ms']),'gap':{k:v for k,v in d.items() if k not in ['candidate_segments_event_gap_gt_1000ms_or_backward','event_time_residue_mod_100ms_counts','local_gaps_greater_than_1000ms']}},ensure_ascii=False))
print(json.dumps({'between_file':g['between_file_session_gaps'],'maxgap':g['maximum_within_file_event_gap']},ensure_ascii=False))
PY
```

</details>

<details><summary>stats_commands.json #7（exit 0）</summary>

```bash
python3 -B - <<'PY'
import os,json
root='/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/'
def load(n):
 fd=os.open(root+n,os.O_RDONLY|os.O_NOATIME)
 with os.fdopen(fd) as f:return json.load(f)
s=load('csv_timestamp_summary.json');c=load('clock_delta_statistics.json');g=load('timestamp_gap_analysis.json')
for a,b,d in zip(s['files'],c['files'],g['files']):
 print(json.dumps({'path':a['relative_path'],'n':a['total_rows'],'neg':b['negative_count'],'zero':b['zero_count'],'pos':b['positive_count'],'event_backward':a['event_time_ms_backward_count'],'local_backward':a['local_timestamp_us_backward_count'],'local_duplicate':a['local_timestamp_us_duplicate_nonfirst_count'],'delta_distribution':b['distribution'],'event_interval':{k:v for k,v in d['event_intervals'].items() if not isinstance(v,(list,dict))},'max_local':d['max_local_gap'],'delta_max_plus':b['max_positive_adjacent_delta_jump'],'delta_max_minus':b['max_negative_adjacent_delta_jump'],'first_block_median':b['blocks'][0]['distribution_us']['median'],'last_block_median':b['blocks'][-1]['distribution_us']['median'],'ols':b['ols_delta_drift_us_per_exchange_second'],'neg_runs':b['negative_runs'] if b['positive_count'] else len(b['negative_runs'])},ensure_ascii=False))
PY
```

</details>

<details><summary>stats_commands.json #8（exit 0）</summary>

```bash
python3 -B - <<'PY'
import csv,json,os
from pathlib import Path
root=Path('/home/jason/hft-realtime-codex');run=root/'artifacts/phase1_timestamp_review/20261018T212122Z'
def ro(p):
 fd=os.open(p,os.O_RDONLY|os.O_NOATIME)
 return os.fdopen(fd,'r',encoding='utf-8',newline='')
def load(n):
 with ro(run/n) as f:return json.load(f)
summary=load('csv_timestamp_summary.json');clock=load('clock_delta_statistics.json');gap=load('timestamp_gap_analysis.json')
checks=[]
for s,c,g in zip(summary['files'],clock['files'],gap['files']):
 assert s['total_rows']==s['parseable_rows']+s['parse_errors']
 assert c['negative_count']+c['zero_count']+c['positive_count']==s['valid_delta_count']
 assert sum(r['records'] for r in c['negative_runs'])==c['negative_count']
 assert g['event_intervals']['count']==s['total_rows']-1
 assert g['local_intervals']['count']==s['total_rows']-1
 for dist in [c['distribution'],g['event_intervals'],g['local_intervals']]:
  q=[dist['min']]+[dist['p'+str(p)] for p in [1,5,25,50,75,95,99]]+[dist['max']]
  assert q==sorted(q)
 checks.append({'path':s['relative_path'],'partition_counts_quantile_order_interval_counts':'PASS'})
windows={
 'results/obi_market_data_20260827_session2.csv':[(99820,99825),(99837,99842),(99868,99871)],
 'results/obi_market_data_20260827_session3.csv':[(45029,45038),(45160,45170)]
}
captured={}
for rel,ranges in windows.items():
 selected=[]
 with ro(root/rel) as f:
  reader=csv.DictReader(f)
  for i,row in enumerate(reader,1):
   if i>max(b for a,b in ranges):break
   if any(a<=i<=b for a,b in ranges):
    event=int(row['event_time_ms']);local=int(row['local_timestamp_us'])
    selected.append({'record':i,'physical_line':reader.line_num,'event_time_ms':event,'local_timestamp_us':local,'delta_us':local-1000*event,'update_id':int(row['update_id']),'mid_price':row['mid_price']})
 captured[rel]={'requested_record_windows':ranges,'rows':selected}
rows2={r['record']:r for r in captured['results/obi_market_data_20260827_session2.csv']['rows']}
rows3={r['record']:r for r in captured['results/obi_market_data_20260827_session3.csv']['rows']}
assert rows3[45032]['delta_us']<0 and rows3[45033]['delta_us']>0 and rows3[45164]['delta_us']>0 and rows3[45165]['delta_us']<0
out={
 'run_id':run.name,'scope':'新補充分析；既有統計輸出與五個CSV皆未修改。以串流只保存兩個指定CSV的異常最小視窗，未重新計算全檔統計。',
 'verification':checks,'windows':captured,
 'session2_tail_compression':{'first':rows2[99839],'last':rows2[99871],'event_elapsed_ms':rows2[99871]['event_time_ms']-rows2[99839]['event_time_ms'],'local_elapsed_us':rows2[99871]['local_timestamp_us']-rows2[99839]['local_timestamp_us'],'interpretation':'event前進3200ms，而local只前進291us；兩時鐘欄位進度不同。現存消費端timestamp及queue程式允許快速清理佇列，但歷史具體原因UNKNOWN。'},
 'session3_positive_run':{'first':rows3[45033],'last':rows3[45164],'record_count_from_full_scan':132,'preceding_negative':rows3[45032],'following_negative':rows3[45165],'local_gap_us':rows3[45033]['local_timestamp_us']-rows3[45032]['local_timestamp_us'],'event_gap_ms':rows3[45033]['event_time_ms']-rows3[45032]['event_time_ms'],'delta_jump_us':rows3[45033]['delta_us']-rows3[45032]['delta_us'],'interpretation':'local出現13.327507秒間隔，但exchange event只相隔100ms；之後132筆delta正值再回到負值。這是本機採樣/處理排程或時鐘的候選現象，不是13.3秒exchange資料缺口，也無證據證實NTP或系統鐘跳。'},
 'trend_summary':[{'relative_path':c['relative_path'],'first_block_median_us':c['blocks'][0]['distribution_us']['median'],'last_block_median_us':c['blocks'][-1]['distribution_us']['median'],'first_to_last_delta_change_us':c['first_to_last_delta_change_us'],'ols_delta_us_per_exchange_second':c['ols_delta_drift_us_per_exchange_second'],'warning':'分段median與全體OLS只是描述；session3短暫正差可令整體OLS斜率為正，而首尾block median仍下降。'} for c in clock['files']],
 'mechanism_evidence':{'file':'src/orderbook_csv.cpp','functions':['EventQueue::push','EventQueue::waitAndPop','main'],'source_agent_finding':'現存CSV generator於消費端Order Book更新後才重新讀system_clock，queue保留event資料而非持久化local receive timestamp。','causal_limit':'這只證明排隊/暫停後追趕在程式結構上可行；沒有producer identity、同時期OS sync及receive紀錄，不能認定歷史原因。'},
 'causal_classification':'INSUFFICIENT_EVIDENCE 對具體系統時鐘/NTP原因；不影響原始數字與LOCAL_TIMESTAMP_NOT_RECEIVE_TIME的static證據。'
}
p=run/'timestamp_anomaly_examples.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'created':str(p),'verification_pass_files':len(checks),'captured_rows':{p:len(v['rows']) for p,v in captured.items()},'session2_event_ms':out['session2_tail_compression']['event_elapsed_ms'],'session2_local_us':out['session2_tail_compression']['local_elapsed_us'],'session3_positive_range':[45033,45164],'session3_previous_local_gap_us':out['session3_positive_run']['local_gap_us']},ensure_ascii=False))
PY
```

</details>

<details><summary>root finalizer（本次執行）</summary>

```bash
python3 -B artifacts/phase1_timestamp_review/20261018T212122Z/finalize_timestamp_review.py
```

</details>


## 22. PASS、WARNING、FAIL、NOT AVAILABLE與完整性

| 項目 | 狀態 | 理由/證據 |
| --- | --- | --- |
| 工作目錄、原968開始前 | PASS | initial_integrity_check.json |
| 五檔SHA/列數/269284核對 | PASS | 與Phase 1 v2一致 |
| event單調、timestamp解析 | PASS | 倒退/缺失/非法全0 |
| local負差/重複/異常區段 | WARNING | 禁止receive/network latency解讀 |
| 歷史clock/producer根因 | NOT AVAILABLE | UNKNOWN / INSUFFICIENT_EVIDENCE |
| 資料損壞 | 未證實 | 負差不能單獨證明 |
| 模型/回測/Paper Trading | NOT AVAILABLE | 未執行，無結果 |
| 完成後完整性 | 以最終JSON實際結果為準 | 任何差異必須FAIL |

報告建立前再次核對968/968與1522既存葉節點一致、無未授權新增，PASS。報告完成後最後實際核對記在[final_integrity_check.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/final_integrity_check.json)，此JSON在本報告後建立，不以預填PASS代替驗證；若其status不是PASS，本次總結果FAIL並停止。

manifest SHA-256：ec4fe4b9bc6dfabac42deabf65e2b19d08a503686e019a68524e3303b263cfe8。比對內容、size/mode/mtime/ctime/link target；不比較目錄metadata/atime。

## 23. 原始CSV未修改聲明

僅串流唯讀五CSV，未修改、刪除、搬移、改名或覆寫。五SHA與Phase 1 v2一致，完成後再以原manifest及全既存葉節點核對。既有src、工具、tests、artifacts、docs、ELF、Benchmark數據與壓縮檔也未修改。

## 24. 沒有網路、Benchmark、Testnet與交易執行

未執行C++ binary、Benchmark、Offline Replay、Live Collector、Capture、Testnet或交易，未連Binance REST/WebSocket，未用API/Secret、curl/wget或安裝套件。未build、建立quantum-hft/模型、回測或Paper Trading。僅新建標準函式庫唯讀分析與報告整合。未進Phase 2。

## 25. 未虛構結果及停止點

數字來自五CSV串流、既有Audit核對與靜態來源；因果UNKNOWN、缺測量NOT AVAILABLE、規則PROPOSAL_ONLY均明列。沒有推定歷史producer、NTP原因、真實network latency、模型結果或未執行測試。完成後停止，等待人工審核。

必要輸出：

- [warning_definition.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/warning_definition.json)
- [csv_timestamp_summary.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/csv_timestamp_summary.json)
- [csv_timestamp_summary.csv](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/csv_timestamp_summary.csv)
- [clock_delta_statistics.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/clock_delta_statistics.json)
- [timestamp_gap_analysis.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_gap_analysis.json)
- [field_usage_matrix.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/field_usage_matrix.json)
- [phase2_time_rules.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/phase2_time_rules.json)
- [command_history.txt](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/command_history.txt)
- [final_integrity_check.json](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/final_integrity_check.json)
