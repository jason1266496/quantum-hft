# Phase 2A-R1 修復報告 — 20261018T222815Z

**PHASE 2A PASS。** 修復已證實的 Replay schema 契約錯配，targeted77與完整164項人工測試通過，新的正式 run `20261018T223410Z` 九來源 SHA／大小／有限範圍 schema 全部通過。舊 `20261018T215940Z` 保持 FAIL，不覆寫歷史。

## 1. 原失敗 run

`20261018T215940Z`；原報告 [docs/PHASE2A_REPORT_20261018T215940Z.md](/home/jason/quantum-hft/docs/PHASE2A_REPORT_20261018T215940Z.md) 與原 artifacts 全部保留。舊結果6 PASS／1 FAIL／2未檢查不變。

## 2. Repair run 與工作目錄

repair run_id=`20261018T222815Z`；正式新 run_id=`20261018T223410Z`。開始前 pwd、realpath 均完全等於 `/home/jason/quantum-hft`，findmnt 為 Linux ext4（/dev/sdd），不是 /tmp／WindowsApps。[integrity_before.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/integrity_before.json) 在修復前保存133個既有檔案與三個HFT根metadata；nanosecond以十進位字串保存，避免前次JavaScript Number精度問題。

## 3. 原失敗來源

`/home/jason/hft-realtime-codex/results/replay_events_1000.jsonl`，record_index=1、physical_line=1、bids[0]。本次先讀原報告、原run檔案、stdout/stderr/execution/source_validation、舊Adapter與測試，再讀兩Replay的前100筆與末筆，沒有依檔名猜測。

## 4. 原始例外與重現

```text
/home/jason/hft-realtime-codex/results/replay_events_1000.jsonl: record 1, physical line 1: bids[0] must be a price/quantity pair
```

以實際首筆 bids 呼叫舊 `ReplayAdapter._levels()` 重現同一 DataFormatError。該診斷只為重現schema，不是重新做整份市場hash驗證。結果與直接證據於 [replay_schema_evidence.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/replay_schema_evidence.json)、修改前已建立的 [root_cause_analysis.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/root_cause_analysis.json)。

## 5. 實際 Replay schema

唯一支援 `capture_object_price_quantity_v1`。頂層為精確五個欄位 `eventTime`、`firstUpdateId`、`finalUpdateId`、`bids`、`asks`；前三者為非負 JSON integer，拒絕 bool、浮點與字串，且 firstUpdateId ≤ finalUpdateId。兩側必須為 list，每筆 update 為精確包含 `price`、`quantity` 的 object，值為 JSON number；price > 0，quantity ≥ 0，零數量只保留成刪除價位語義，未套用 Book。

兩檔前100筆及額外末筆 schema 一致：首筆已包含在前100筆；末筆以最多65536-byte tail window seek取得，僅解析最後一筆。每檔合計101筆被診斷，不是抽樣101筆；其中一般串流抽樣最多100筆，另有使用者明准的末筆。

| 診斷來源 | 前綴記錄 | 前綴bytes | bid updates | ask updates | 價量型別 | 末筆 |
|---|---:|---:|---:|---:|---|---|
| Replay1000 | 100 | 116563 | 1394 | 1559 | 全JSON decimal number | 同schema |
| Replay50000 | 100 | 119110 | 1595 | 1429 | 全JSON decimal number | 同schema |

未觀察到 string、二元素array或第二種schema，故未新增無證據的variant。診斷artifact只存keys／型別／計數／錯誤摘要，未保存市場事件或價量副本。

## 6. Capture 原始碼格式

唯讀證據來自 [batch_replay_capture.cpp](/home/jason/hft-realtime-codex/src/batch_replay_capture.cpp) 與 [batch_replay_capture_50000.cpp](/home/jason/hft-realtime-codex/src/batch_replay_capture_50000.cpp:560) 的 `depthEventToReplayJson()`，兩者560–589行。bids物件於572–575、asks物件於582–585行。

`PriceLevel` 的 price／quantity 是 C++ double（53–56行），`DepthEvent` 三個ID／時間為 long long（59–66行）；函式把每個level輸出為 price/quantity物件，值為JSON number。輸出路徑966–969行、呼叫988–990行，50000另見1123–1125。未執行或修改 capture binary／原始碼。

## 7. 資料損壞證據

`data_corruption_evidence=NOT_FOUND`，限定於上述樣本／末筆結構與本輪九檔SHA相符的證據。這不是全量Replay每筆語義或交易所真實性保證；未檢查記錄的schema有效性仍未由本次取樣確立。沒有將Adapter拒絕正確capture格式解讀成資料損壞。

## 8. 根因與修復設計

`adapter_bug_confirmed=true`；分類 `ADAPTER_SCHEMA_CONTRACT_MISMATCH_WITH_MIRRORED_TEST_FIXTURE`。舊 `_levels()` 將每update視為二元素list，舊人工fixture複製同一假設，導致測試通過而正式來源失敗。

[data_pipeline/adapters/replay_adapter.py](/home/jason/quantum-hft/data_pipeline/adapters/replay_adapter.py) 現在只接受已證實object/JSON number schema。`json.loads(parse_float=Decimal)` 直接解析數字token，無float中轉；`stream_records()` 輸出精確Decimal價量tuple並保留來源與Session。數值與小數精度無損；不保證原JSON空白／指數拼字，也不能恢復capture先前double已捨入的精度。

`_error()`／`_safe_summary()` 附source_id、record_index、side、update_index、safe_summary；index為0起算，無法定位的side/update_index明列NOT_AVAILABLE。摘要有界、跳脫控制字元，duplicate-key錯誤不傾印不可信key。

另一已診斷問題是 inspector 全域fail-fast。[tools/inspect_data_sources.py](/home/jason/quantum-hft/tools/inspect_data_sources.py) 的 `inspect_sources()` 改為每來源獨立記錄，包含constructor/close失敗；來源hash驗證失敗只停止該來源解析，其他來源照常檢查，最後整體FAIL且保留所有errors。這遵循本輪使用者明確要求，優先於AGENTS舊全域停止規則。Base無需修改。

## 9. 修改檔案與版本

僅四檔，完整diff及函式/測試索引見 [code_changes.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/code_changes.json)：

| 檔案 | 修改前SHA-256 | 修改後SHA-256 |
|---|---|---|
| [data_pipeline/adapters/replay_adapter.py](/home/jason/quantum-hft/data_pipeline/adapters/replay_adapter.py) | `6fac6b37485f3d4f12247b3560ec8e180941c18c02a57f96bc4e849d8a13d519` | `a9384629a3671c23d94b582b0fe83a7c9a71027620a2d298ce6456f05cdceab2` |
| [tools/inspect_data_sources.py](/home/jason/quantum-hft/tools/inspect_data_sources.py) | `204e43140eb5ee0045a55bd42b9c75a8300e15630a91f9c0379ce93ae709eb0d` | `b05cd9a9a5b0793fce5056624df0181028935a8d6122f61913257af92192b829` |
| [tests/test_replay_adapter.py](/home/jason/quantum-hft/tests/test_replay_adapter.py) | `3bad76858510573d4acce194670cee42261568a891fc8d5d2188e12dd5999031` | `3dd7c46b7c9da18ec330c8e10c02fb5acf8622c4e828369a8a18ba4cd5ec3a36` |
| [tests/test_inspect_data_sources.py](/home/jason/quantum-hft/tests/test_inspect_data_sources.py) | `d0d03238d6005ebca0f594f8b62c0d8ad5b9bdbb2bad0ba054afebc79986f72e` | `6e7aa6f58e09ca812b7405f6f531430810d1290c86773a5e8612a35ed104bea0` |

## 10. 新增及修正回歸測試

Replay由23增至49、Inspector由19增至28，合計新增35個TestCase方法，舊錯誤fixture與fail-fast期望已修正。人工JSON literal使用自訂數字，不複製正式市場記錄；兩組fixture是不同內容、同一schema。本次未新增獨立fixtures檔案，測試資料嵌入兩個獲准測試模組並在tests/人工暫存目錄執行。

25項需求映射如下；同一方法中的subTest不重複計入unittest TestCase數量，機器可讀版本為 [regression_coverage.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/regression_coverage.json)。

| 要求 | 覆蓋內容 | 測試方法 |
|---:|---|---|
| 1 | Replay1000等價人工schema | `tests/test_replay_adapter.py::test_artificial_replay_1000_equivalent_schema` |
| 2 | Replay50000同schema不同人工內容 | `tests/test_replay_adapter.py::test_artificial_replay_50000_equivalent_same_schema` |
| 3 | 正確bids | `tests/test_replay_adapter.py::test_normal_event_exact_decimal_and_update_counts` |
| 4 | 正確asks | `tests/test_replay_adapter.py::test_correct_asks_are_preserved` |
| 5 | quantity=0有效 | `tests/test_replay_adapter.py::test_zero_quantity_on_asks_is_preserved` |
| 6 | 負quantity拒絕 | `tests/test_replay_adapter.py::test_negative_quantity_fails` |
| 7 | price=0拒絕 | `tests/test_replay_adapter.py::test_zero_price_fails` |
| 8 | 負price拒絕 | `tests/test_replay_adapter.py::test_negative_price_fails` |
| 9 | 無法解析price拒絕 | `tests/test_replay_adapter.py::test_unparseable_price_fails` |
| 10 | 無法解析quantity拒絕 | `tests/test_replay_adapter.py::test_unparseable_quantity_fails` |
| 11 | update欄位數錯誤 | `tests/test_replay_adapter.py::test_update_object_length_missing_or_extra_fields_fails` |
| 12 | update型別及舊pair拒絕 | `tests/test_replay_adapter.py::test_update_type_and_legacy_pair_variant_are_rejected` |
| 13 | bids非list拒絕 | `tests/test_replay_adapter.py::test_bids_non_list_fails` |
| 14 | asks非list拒絕 | `tests/test_replay_adapter.py::test_asks_non_list_fails` |
| 15 | 缺eventTime（subTest） | `tests/test_replay_adapter.py::test_required_ids_and_event_time` |
| 16 | 缺firstUpdateId（subTest） | `tests/test_replay_adapter.py::test_required_ids_and_event_time` |
| 17 | 缺finalUpdateId（subTest） | `tests/test_replay_adapter.py::test_required_ids_and_event_time` |
| 18 | 損壞JSON | `tests/test_replay_adapter.py::test_json_damage_has_record_location` |
| 19 | 錯誤包含記錄位置 | `tests/test_replay_adapter.py::test_error_has_side_update_index_and_safe_original_value` |
| 20 | 串流有界讀取 | `tests/test_replay_adapter.py::test_stream_only_reads_one_bounded_line_before_first_yield` |
| 21 | 輸入內容/metadata不變 | `tests/test_replay_adapter.py::test_input_file_and_directory_remain_unchanged` |
| 22 | Session隔離 | `tests/test_replay_adapter.py::test_sessions_stay_separate` |
| 23 | inspector處理Replay1000人工等價schema | `tests/test_inspect_data_sources.py::test_inspector_handles_artificial_replay_1000_schema` |
| 24 | inspector處理Replay50000同schema | `tests/test_inspect_data_sources.py::test_inspector_handles_artificial_replay_50000_same_schema` |
| 25 | 錯誤schema令來源FAIL | `tests/test_inspect_data_sources.py::test_wrong_replay_schema_fails_with_structured_location` |

另有高精度numeric token、科學記號、過大exponent、UTF-8、重複key、安全摘要、constructor/close、多來源多失敗及第7來源錯誤後第8/9仍驗證的回歸。

## 11. 修復後測試與正式重驗

| 執行 | 測試數 | PASS | FAIL | ERROR | skipped | exit code | wrapper秒 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Replay＋Inspector targeted | 77 | 77 | 0 | 0 | 0 | 0 | 0.247250 |
| 完整Phase2A | 164 | 164 | 0 | 0 | 0 | 0 | 0.371470 |

完整組分布為 Registry/Base33、CSV25、Snapshot29、Replay49、Inspector28。unittest 自報測試時間分別0.176s、0.293s，wrapper時間包含程序啟動。證據：[targeted_unittest.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/targeted_unittest.json)、[full_unittest.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/full_unittest.json)及同名前綴的 stdout／stderr 檔。

targeted通過後才執行完整組，完整組通過後才建立新run實際驗九來源。[source_validation.json](/home/jason/quantum-hft/artifacts/phase2a/20261018T223410Z/source_validation.json) 顯示sources_attempted/checked/schema_checked均9、sources_passed=9、failures=[]、parse_errors=0，exit0。進度終點9/9、100%、ETA0。本次 SHA-256 串流讀取九個來源全部位元組；有限樣本限制適用於記錄解析，不影響完整雜湊。每次 Base.validate_source() 重新計算，可能重讀同一檔，不將記錄或全檔載入記憶體。五 CSV 與兩 Replay 各解析前100筆。每份 Snapshot 串流遍歷完整 JSON 結構、統計 bids=5000／asks=5000，各側只檢查前100層數值與排序，各4900層仍 NOT_CHECKED。未執行全量值驗證、Book 重建、跨來源合併。

## 12. 安全限制與範圍

全部Python標準函式庫；沒有apt/pip/npm/curl/wget、套件安裝、API Key／Secret Key。沒有HFT binary、Replay binary、Benchmark、Recorder修改、交易、回測或Paper Trading。舊設定與manifest不變。未建立Order Book Rebuilder、特徵、標籤或Phase2B模組。

## 13. HFT 與舊檔案完整性

[integrity_after.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/integrity_after.json) 確認只修改四個獲准檔案，其餘129個既有檔案內容 SHA／metadata 未變；其中舊 FAIL run 的22檔與舊正式報告合計23檔全部保留，舊 source_validation.status 仍為 FAIL。Base、CSV、Snapshot、Registry、AGENTS、設定檔、HANDOFF_MANIFEST 與舊報告沒有修改。

三個 HFT 根目錄的前後 metadata 摘要也相符：hft-realtime 1385項、hft-realtime-codex 2538項、鑑識保留副本1302項。本次計數包含目錄及檔案／symlink，故與舊報告只計leaf不同。比較 mode/size/mtime/ctime/link，排除 atime；沒有把 metadata 比對誇稱為整個 HFT 樹的內容雜湊。九個登錄市場檔另有完整 SHA-256 驗證。最後收尾結果見 [closeout_verification.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/closeout_verification.json)。

## 14. 網路

未發生本專題REST、WebSocket、Testnet或其他專題網路連線。此結論基於本輪工具命令及程式行為，不是整台主機其他程序的封包稽核。

## 15. 模型

沒有Classical ML、Quantum Kernel、QSVC、QUBO、QAOA，沒有訓練任何模型。沒有回測或Paper Trading。

## 16. 全部執行命令與證據索引

所有 shell 均使用 cwd=`/home/jason/quantum-hft`、login=false。主要命令依序為：

```bash
pwd
realpath .
findmnt -T .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_replay_adapter.py tests/test_inspect_data_sources.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_registry.py tests/test_csv_adapter.py tests/test_snapshot_adapter.py tests/test_replay_adapter.py tests/test_inspect_data_sources.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/inspect_data_sources.py --config configs/data_sources.json --output artifacts/phase2a/20261018T223410Z --sample-records 100
python3 -B artifacts/phase2a_repair/20261018T222815Z/finalize_r1.py
```

環境變數由 subprocess env 設定；沒有修改設定檔。兩輪測試與正式重驗均各執行一次，不使用 `--full-scan`。其他實際唯讀診斷、capture 查找、完整性比對及報告證據寫入的**完整命令與腳本正文**保存於 [root_commands.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/root_commands.json)、[evidence_commands.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/evidence_commands.json)、[replay_fix_commands.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/replay_fix_commands.json)、[inspector_commands.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/inspector_commands.json)、[final_review.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/final_review.json)，由 [command_index.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/command_index.json) 索引；本文將這些檔案列為正式報告附件，未以摘要代替原始紀錄。

正式測試／重驗逐次保存 stdout、stderr、exit code；exec 工具較早的直接讀取只提供合併 output，ledger 明示此限制，不虛構分流。開發證據保存曾遇命令過長、過大 stdin 的自動審核拒絕及未寫檔 writer 中止，原結果保留，後以已授權的新檔 Add File 保存；沒有擴張寫入範圍。這些屬證據保存程序結果，不改寫成測試 FAIL 或資料損壞。

## 17. 舊 FAIL 完整保留與新增輸出

舊run與舊報告沒有修改、刪除、搬移或重新命名，FAIL沒有改成PASS。新成功結果只屬於 `20261018T223410Z`。所有新增證據都在本repair run、新Phase2A run及兩份新報告中；完整新增檔案清單與report SHA見 [closeout_verification.json](/home/jason/quantum-hft/artifacts/phase2a_repair/20261018T222815Z/closeout_verification.json)，新run的 [repair_evidence_reference.json](/home/jason/quantum-hft/artifacts/phase2a/20261018T223410Z/repair_evidence_reference.json) 連到本次共同命令/測試證據。

保留WARNING：五CSV既有timestamp限制、取樣範圍、歷史capture身分與Snapshot事件時間缺失、capture double歷史精度不可復原。沒有把這些限制抹除。

## 18. 誠信與停止

沒有虛構測試、九來源檢查、Book重建、模型、量子電路或交易結果；所有PASS對應實際執行證據，沒有用本次PASS覆蓋舊FAIL。修復與重新驗證完成後停止，等待人工審核。建議人工核准後再開始Phase2B；本次未進入。
