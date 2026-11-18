# Phase 4B-2A Contract Migration Gate
狀態：PHASE 4B-2A CONTRACT MIGRATION GATE PASS。run_id：20261030T104828Z。

## 最小版本化升級
原UNAPPROVED_RUN_ROOT是Recovery3 launch_contract.py:13僅接受Recovery正式root的政策結果，不是資料或labels錯誤。本輪建立phase4b2a_contract_v1，未修改Recovery3或任何歷史封存。
共享--run-dir明確CLI；硬編碼phase-to-root映射分開recovery3、phase4b2a、phase4b2a_contract，以及development root。AUTH phase必須與鎖定run_configuration一致、符合固定root及execution_kind；任意phase字串、錯root、空值、歷史封存、symlink、..、重複啟動安全拒絕。Supervisor/Child/worker同契約，shell=False。
原Recovery3程式原SHA保留；新版本保留其適用root但不授予單檔Train值解析權。新正式LabelAudit根僅phase4b2a可匹配，Migration Gate根僅phase4b2a_contract。沒有放行整個artifacts。

## 單檔Train比較能力
由封存Dataset manifest、train/manifest.json、dataset_schema.json、frozen_split_policy.json唯一確認：
canonical path：/home/jason/quantum-hft/artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z/1000ms/train.csv
SHA256：8628e45fe52bc1f0ef3cda20a9c31f9c72d8e4f01d1cd4f80103d624a455fd1d；size=65902450；rows=150912。
split=Train、aggregate_core_v1、1000ms；無class_label欄位，只有continuous return及label metadata。
原3份HFT CSV白名單完全不變。DatasetTrainLoader是獨立能力，production constructor沒有path/SQL/glob參數，只能存取上述檔案；非unit且phase4b2a/label_audit、authority manifests SHA與精確Stage1 receipt都符合後才可開啟。原MarketLoader仍只接受3CSV。
只回傳schema列出的必要欄位，禁止local_timestamp_us等未核准欄位；每列header、source/session、時間範圍、matched endpoint、view與horizon檢查，混合split／來源／horizon安全失敗，不默默丟列。
本輪Migration Gate僅以人工CSV/label/manifest驗證新增reader；實際Train values解析0。file checksum通過不會自動授予market值讀取能力。

## 測試及預檢
正式/當前測試79既有regression+25安全+13原launch contract+24migration，共141項PASS，0failure/error/import error/skip，沒有成功越界寫入。
開發由真正Supervisor -> phase root -> Child CLI -> privateTMP -> tests -> isolated worker -> trace/ready ->本封存程序，包含正常、缺參數、空值、歷史、symlink、重複啟動、啟動失敗、非零exit、測試失敗、Stage1人工中斷、manifest SHA mismatch等。
所有舊assertions保留；新增測試不執行任何正式Label比較。TMPDIR/TEMP/TMP在新程序前設定、tmp0700、umask077、UNIT_WRITE_SCOPE與原/dev/null dill限制例外持續有效，排他建立、禁止覆寫。

## Stage1與歷史保存
{"AGENTS": {"content_opened": true, "path": "/home/jason/hft-realtime-codex/AGENTS.md", "sha256": "805979a28b954763144046eddce9682b4ed7a83f20d02532966b0ba8e25f5343", "size_bytes": 2371, "status": "PASS"}, "Dataset_Frozen_venv": "PASS_FRESH_SHA_EXCEPT_HOLDOUT_STAT_SEALED_SHA", "Final_Holdout": "LOCKED32_PACKAGE_CSV_STAT_ONLY", "Test": "OPAQUE_SHA_ONLY_NOT_EVALUATED", "all_historical_BLOCKED_and_Recovery3": "UNCHANGED", "env_directories": 1927, "opaque_file_stat_records": 20393, "protected_baseline_count": 3919, "source_CSVs": [{"content_opened": true, "path": "/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session1.csv", "sha256": "9931b0d9ef9be5dba36ea26cdd4d6d7fd1552a195af53460c59ffe415ceea8d3", "size_bytes": 8019032, "status": "PASS"}, {"content_opened": true, "path": "/home/jason/hft-realtime-codex/results/obi_market_data_20260827_session2.csv", "sha256": "363e81f86de61a3acc697216082770f11a7158935c8745e172235ee6f9e1fd7c", "size_bytes": 13226704, "status": "PASS"}, {"content_opened": true, "path": "/home/jason/hft-realtime-codex/results/obi_market_data_test_20260827.csv", "sha256": "aa9bb47e598aaa024640c079654ed17da1e70552ed06632361dc4cb607b8171f", "size_bytes": 126181, "status": "PASS"}], "status": "PASS", "symlinks": 18}
正式Stage1只串流核對明列檔案／stat：Dataset/Frozen、兩venv、原始CSV、所有歷史BLOCKED與Recovery3 PASS。Holdout32封裝CSV僅metadata與既有sealedSHA，Test僅延續既有opaque完整性SHA；不解析其特徵、價格、labels。
Integrity worker維持獨立程序，只輸出hash/status/size metadata；沒有內容API，不能把其讀取能力傳給market程序。Market程序禁止AGENTS解析與subprocess。

## 安全、限制與後續
正式Label驗證0筆、模型fit/predict0、正式QuantumKernel0、QPU/Binance/網路/QAOA/QUBO/交易/回測/PaperTrading/新資料蒐集/套件變更0。原始Dataset、Frozen、FoldIDs、HFT、venv及歷史成果未修改。
Python程序與audit hooks是應用層能力分離，並非新增OS強制隔離；不宣稱抵抗任意native惡意碼、所有競態或全機流量。
本輪只驗收契約先決條件；下一輪仍需編寫、測試並鎖定獨立LabelReference與audit_child.py，走相同runner的已鎖定Audit slot。此slot本輪未執行，不能把Gate成功當成labels正確或來源已獨立重建。
完成後停止，等待人工審核；不自動啟動1440IDs/150912Train/9203排除分析，也不進4B2B。
