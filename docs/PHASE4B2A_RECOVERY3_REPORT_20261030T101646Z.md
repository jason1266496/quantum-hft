# Phase 4B-2A Recovery-3
狀態：PHASE 4B-2A RECOVERY GATE PASS。run_id：20261030T101646Z。

## 啟動契約與原錯誤
原092223Z為opaque SHA與市場讀取護欄衝突；093251Z缺明確importlib.util；095905Z父程序supervisor.py:97漏傳RUN，child run_tests.py:5直接sys.argv[1]導致IndexError。
開發原先直接呼叫Child傳了位置RUN，正式Supervisor卻沒傳，故先前開發沒有覆蓋真實啟動鏈。本輪共用launch_contract.py，以argparse --run-dir <absolute>為必要參數，無位置參數fallback、猜測或舊run預設。
Supervisor實際child command=[python,-I,-B,entry,--run-dir,run]，shell=False。Child先檢查真實路徑、UTC命名、current launch authorization、mode/root對應與TMP環境；歷史completion/failure、symlink、..、空值、錯誤cwd等安全拒絕。首次啟動標記禁止重複啟動／覆寫。

## 開發與正式執行
開發使用真正Supervisor -> Child -> 25安全+13新契約+79既有regression -> 獨立worker人工smoke -> ready及封存流程，並驗證13組正常/缺失/空值/格式/歷史/symlink/相對/逃逸/重複啟動/child啟動失敗/nonzero/測試失敗情境。
預期negativeケース有非零exit與完整trace，沒有fake成功標記；這些不是被隱藏的正式Gate失敗。開發及正式使用相同鎖定程式和--run-dir介面；差異只限事先規定的mode、run/tmp/輸出位置與人工/核准manifest輸入。
本輪執行79/79 regression、25/25安全、13/13契約，總117項unittest，0fail/error/import error/skip。既有tests未刪除、未改assertions；Qiskit/dill只import，無fit/predict/evaluate。舊79包含人工數學reference，不是正式Train Label Audit。
TMPDIR/TEMP/TMP在child啟動前設定；tmp非symlink、0700、umask077確保暫存檔0600，保留既有精確/dev/null dill例外，未開放/tmp或其他/dev。

## 完整性與權限
Stage1狀態：PASS。{"AGENTS": {"content_opened": true, "path": "/home/jason/hft-realtime-codex/AGENTS.md", "sha256": "805979a28b954763144046eddce9682b4ed7a83f20d02532966b0ba8e25f5343", "size_bytes": 2371, "status": "PASS"}, "Dataset_Frozen_venv": "PASS_FRESH_SHA_EXCEPT_HOLDOUT_STAT_SEALED_SHA", "Final_Holdout": "LOCKED32_PACKAGE_CSV_STAT_ONLY", "Test": "OPAQUE_SHA_ONLY_NOT_EVALUATED", "all_three_BLOCKED": "UNCHANGED", "env_directories": 1927, "opaque_file_stat_records": 20320, "protected_baseline_count": 3919, "source_CSVs": [{"content_opened": true, "path": "/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session1.csv", "sha256": "9931b0d9ef9be5dba36ea26cdd4d6d7fd1552a195af53460c59ffe415ceea8d3", "size_bytes": 8019032, "status": "PASS"}, {"content_opened": true, "path": "/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session2.csv", "sha256": "363e81f86de61a3acc697216082770f11a7158935c8745e172235ee6f9e1fd7c", "size_bytes": 13226704, "status": "PASS"}, {"content_opened": true, "path": "/home/jason/hft-realtime-codex/results/obi_market_data_test_20260827.csv", "sha256": "aa9bb47e598aaa024640c079654ed17da1e70552ed06632361dc4cb607b8171f", "size_bytes": 126181, "status": "PASS"}], "status": "PASS", "symlinks": 15}
Integrity worker與Market Loader分開程序，worker僅串流已封存manifest明列內容並回傳path/status/size/SHA，Holdout32封裝CSV僅stat與先前封存SHA；不提供原始內容API。市場程序沒有opaque呼叫堆疊例外，禁止AGENTS解析、Test/Holdout與其他來源，禁止subprocess。
三個核准CSV白名單未擴大。本輪未解析正式CSV值；Test只延續核准opaque hash，FinalHoldout內容未開啟。既有baseline3919、Frozen/Dataset、ML7610/QML10505 entries與三次BLOCKED的30/27/25 artifacts及report/seal在正式Stage1皆由明列核對。
一般Python subprocess+audit hook是應用層能力分離，並未取得新的OS級權限隔離。O_NOFOLLOW與路徑/identity檢查降低替換風險，但不宣稱能抵禦任意native惡意程式、所有並行競態或全機流量。

## 安全與結論
正式Label驗證0筆、150912逐列重建0、9203排除分析0、模型fit/predict0、正式QuantumKernel0、QPU/Binance/QAOA/QUBO/交易/回測/PaperTrading/網路/安裝套件0。
歷史FAIL/BLOCKED未改成PASS。本輪封存程式SHA及source/config保持不變，正式Gate僅執行一次；完成後停止，不直接執行完整Phase4B2A或4B2B。
Recovery PASS只解決工程契約與完整性Gate；同日資料、capture/producer UNKNOWN、獨立標籤與原始訂單簿驗證尚未完成。若人工審核後恢復LabelAudit，須沿用精確Train讀取授權，不可由checksum成功擴大市場值權限。
