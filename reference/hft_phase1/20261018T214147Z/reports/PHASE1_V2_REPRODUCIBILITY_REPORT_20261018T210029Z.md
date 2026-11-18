# Phase 1 v2 可重現研究基線與資料稽核報告

PHASE 1 V2 PASS；資料品質警告保留。Run ID：20261018T210029Z

## 1. 人工批准方案B

本次依使用者附件批准保留獨立validation C++並將其納入新的正式受保護基線。批准來源與SHA-256、適用範圍保存在 [baseline/approval_context.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/approval_context.json>)。沒有隔離、刪除、修改或重新命名該C++。

## 2. 工作目錄

pwd與realpath均完全等於 /home/jason/hft-realtime-codex，findmnt確認Linux ext4。全部操作明確指定此workdir。保留來源/home/jason/hft-realtime及舊不完整副本沒有寫入。工作目錄不在/tmp或WindowsApps。

## 3. Phase1 v2 run_id

20261018T210029Z。所有本輪流程輸出以新路徑建立；遇已存在輸出拒絕覆寫。唯一安全CMake目錄見第11節。

## 4. Recovery run_id

20261018T202030Z。Recovery與全部先前Phase1證據保留，不變更其內容或結論。

## 5. 舊Phase1 FAIL保留聲明

本次 PHASE 1 V2 PASS 僅描述新Phase1 v2的執行。舊250檔初始Manifest、251檔最終Manifest、FAIL比較、Recovery報告及後續符號連結覆核全部保留。新基線不回溯替代舊基線，也不證明Phase0原始專題完全未受改動。954→968期間新增14檔保留且分類仍UNKNOWN。

## 6. 968檔開始前驗證

PASS：968/968相對路徑存在且SHA-256完全相同；基線 [/home/jason/hft-new-copy-20261018T194544Z.sha256](</home/jason/hft-new-copy-20261018T194544Z.sha256>) 的SHA-256為 ec4fe4b9bc6dfabac42deabf65e2b19d08a503686e019a68524e3303b263cfe8。使用lstat與O_NOFOLLOW，未將directory symlink展開。完成UTC 2026-10-18T21:00:29.920346+00:00。另外在任何本輪run寫入前保存993個既有regular檔與10個既有symlink，共1003項，供舊Recovery等新增歷史證據保護。證據：[baseline/original_968_precheck.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/original_968_precheck.json>)、[baseline/preexisting_workspace_inventory.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/preexisting_workspace_inventory.json>)。

## 7. 新的251檔正式受保護基線

正式基線：[baseline/protected_files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.json>)；SHA sidecar：[baseline/protected_files_manifest.sha256](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.sha256>)。開始時間 2026-10-18T21:07:08.826702Z，正好251個regular檔，251項birth time可取得，與舊最終251檔相對路徑集合相同。範圍僅src、analysis、scripts、results、根目錄ELF magic確認檔及兩壓縮檔。工具不展開symlink；真實目錄不列為檔案項目。

## 8. 批准保留的C++檔案

[/home/jason/hft-realtime-codex/src/orderbook_live_matched_validation_1000.cpp](</home/jason/hft-realtime-codex/src/orderbook_live_matched_validation_1000.cpp>)；SHA-256 221765f3390e74cf03f918248a253f1b425f6ddaf265d67eae5ac4d15f150fbf。來源分類維持CONFIRMED_CODEX_CREATED且user_authorized_intent=true。已納入本次baseline與final，未編譯或執行該Live validation程式。

## 9. Manifest v2工具與人工測試

[/home/jason/hft-realtime-codex/tools/protected_manifest_v2.py](</home/jason/hft-realtime-codex/tools/protected_manifest_v2.py>) 的build_manifest、compare_manifests、main支援create/compare/verify、JSON與差異CSV；使用lstat、不展開目錄symlink、只有regular檔SHA，mode列內容必要欄位，mtime/ctime等列metadata warning，generated_at不參與內容相等比較。Linux birth透過stdlib ctypes的statx，使用dir_fd與AT_SYMLINK_NOFOLLOW；不支援時明列unavailable。O_EXCL防覆寫，輸出祖先symlink拒絕。

人工測試 [/home/jason/hft-realtime-codex/tests/test_protected_manifest_v2.py](</home/jason/hft-realtime-codex/tests/test_protected_manifest_v2.py>)：最終28/28 PASS，FAIL/ERROR/skipped各0，0.174秒；已測工具hash與現檔一致。第一次24項中1項ctime fixture假設失敗，修正本輪新測試後24項PASS，再補4項後28項PASS；三輪均保留。
| attempt | 測試數 | 狀態 | FAIL | ERROR |
| --- | --- | --- | --- | --- |
| manifest_v2_unittest_attempt01.json | 24 | FAIL | 1 | 0 |
| manifest_v2_unittest_attempt02.json | 24 | PASS | 0 | 0 |
| manifest_v2_unittest_attempt03.json | 28 | PASS | 0 | 0 |

涵蓋15個要求與額外ELF/symlink/FIFO/birth/exclusive-create案例。人工FIFO只記metadata，不開啟。完整證據 [tests/manifest_v2_test_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_test_summary.json>)。

## 10. 執行環境

| 項目 | 實際觀察 |
| --- | --- |
| OS | PRETTY_NAME="Ubuntu 26.04 LTS"<br>NAME="Ubuntu"<br>VERSION_ID="26.04"<br>VERSION="26.04 (Resolute Raccoon)"<br>VERSION_CODENAME=resolute<br>ID=ubuntu<br>ID_LIKE=debian<br>HOME_URL="https://www.ubuntu.com/"<br>SUPPORT_URL="https://help.ubuntu.com/"<br>BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"<br>PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"<br>UBUNTU_CODENAME=resolute<br>LOGO=ubuntu-logo<br> |
| Kernel | 6.6.114.1-microsoft-standard-WSL2 |
| WSL | {"kernel_contains_microsoft": true, "WSL_DISTRO_NAME": "Ubuntu"} |
| CPU | Intel(R) Core(TM) Ultra 7 255HX |
| logical CPUs | 20 |
| RAM | MemTotal:        7849016 kB |
| g++ | 15.2.0 |
| CMake | 4.2.3 |
| Python | Python 3.14.4 |
| Boost | 1.90.0 |
| OpenSSL | 3.5.5 |
| nlohmann/json | 3.11.3 |
| Git | unavailable：非Git repository |
| Timezone | CST |
| 記錄UTC | 2026-10-18T21:03:57.203353+00:00 |
| Sandbox | workspace-write; 本次寫入由標準require_escalated審核執行 |
| CPU isolation | 未完整驗證；不宣稱已啟用 |

完整原始版本輸出、filesystem、sysfs觀察與環境見 [environment/environment.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/environment/environment.json>)。不使用隨機性，random seed不適用；未安裝套件。

## 11. CMake安全檢查

PASS：三項HFT_BUILD_LIVE_TOOLS／CAPTURE_TOOLS／TESTNET_TOOLS預設與preset均OFF；guard開啟時直接拒絕；沒有Live/Capture/Testnet executable target、沒有src glob、沒有run custom target或下載。reviewed source hash pins均一致。既有CMakeLists、CMakePresets與cmake檔案均未修改。

使用者列出的兩個來源basename對應既有target實名：
| 使用者指定來源 | 既有CMake target |
| --- | --- |
| offline_replay_smoke | hft_offline_replay_1000 |
| offline_replay_batch1_50000 | hft_offline_replay_50000 |

cmake/Phase1Guard.cmake強制binary directory在artifacts/build/<run_id>。依本次第十七節允許的安全CMake build目錄例外，使用 [/home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline>)；沒有修改guard或繞過其路徑檢查。建置log另存本run/build。靜態逐項證據：[build/cmake_static_safety.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/cmake_static_safety.json>)。

## 12. Configure結果

PASS，exit 0；透過未修改的tools/configure_offline.py保留新run並執行cmake --preset offline-safe。建置流程總耗時 24.007 秒。完整實際configure命令與輸出見 [build/captured_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_commands.json>)、[build/captured_configure.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_configure.log>)。

## 13. Offline target Build結果

兩個指定來源對應target均PASS，build exit 0；產生後只讀取ELF hash，不執行。
| target | bytes | SHA-256 |
| --- | --- | --- |
| hft_offline_replay_1000 | 770248 | d16f53c78290b10c047ba264bde4178040751125c561438ab313c0e3ed0b3c93 |
| hft_offline_replay_50000 | 770304 | e5ecd973b0084d61f13907008b633a909f3b6e2205317b39bb6b31d96738e96c |

compiler /usr/bin/g++；C++17、Release -O2 -DNDEBUG，警告旗標 MSVC: /W4; other: -Wall -Wextra -Wpedantic。精確compile/link命令保存於 [build/captured_compile_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_compile_commands.json>)、[build/captured_build.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_build.log>) 與build目錄link.txt。完整stdout/stderr位於build/driver_stdout.log與driver_stderr.log；既有wrapper將子程序stderr合併至其各命令log，內容皆保留。

configure/build log未檢出warning文字。

## 14. Dataset Audit單元測試

實際重跑 [/home/jason/hft-realtime-codex/tests/test_dataset_audit.py](</home/jason/hft-realtime-codex/tests/test_dataset_audit.py>)：43/43 PASS，FAIL=0、ERROR=0、skipped=0，耗時 2.16758 秒。不是沿用舊43數字。

既有setUpClass固定輸出artifacts/test_runs；本run/audits/dataset_orchestrator.py只在記憶體替換輸出配置，43個測試本體與helper原樣執行，fixtures與CLI輸出全在本run/tests。既有tools/dataset_audit.py與tests/test_dataset_audit.py前後hash相同。完整stdout/stderr與測試明細見 [audits/dataset_execution_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json>) 與 [tests/dataset_artificial_tests](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests>)。

## 15. 九個資料檔唯讀稽核摘要

每個資料檔使用獨立新輸出目錄；9檔SHA與新baseline及原968清單相同。輸入唯讀，所有實際命令exit0。4 PASS、5 WARNING、0 FAIL、0 NOT AVAILABLE。
| 輸入 | records | bytes | 解析錯誤 | 狀態 | 新報告 |
| --- | --- | --- | --- | --- | --- |
| results/obi_market_data_20260827_session1.csv | 60558 | 8019032 | 0 | WARNING | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.json>) |
| results/obi_market_data_20260827_session2.csv | 99871 | 13226704 | 0 | WARNING | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.json>) |
| results/obi_market_data_20260827_session3.csv | 58037 | 7691375 | 0 | WARNING | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.json>) |
| results/obi_market_data_test_20260827.csv | 951 | 126181 | 0 | WARNING | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.json>) |
| results/obi_market_data.csv | 49999 | 6683124 | 0 | WARNING | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.json>) |
| results/replay_snapshot_1000.json | 1 | 560071 | 0 | PASS | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.json>) |
| results/replay_events_1000.jsonl | 1000 | 1176899 | 0 | PASS | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json>) |
| results/replay_snapshot_50000.json | 1 | 560071 | 0 | PASS | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/audit_report.json>) |
| results/replay_events_50000.jsonl | 50000 | 99969619 | 0 | PASS | [audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.json>) |

每檔hash、schema、執行時間、命令與輸出路徑完整保存於 [audits/dataset_execution_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json>)；逐檔覆核 [audits/dataset_audit_verification.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/dataset_audit_verification.json>)。CSV與JSONL串流讀取；重複偵測集合隨唯一值增加，並非固定記憶體。Snapshot整份載入，每檔560,071 bytes；未假稱所有格式都串流。

## 16. 解析錯誤與Update ID問題

九檔解析錯誤合計 0。Replay正式稽核結果：
| 輸入 | records | gap | duplicate | backward | parse errors |
| --- | --- | --- | --- | --- | --- |
| results/replay_events_1000.jsonl | 1000 | 0 | 0 | 0 | 0 |
| results/replay_events_50000.jsonl | 50000 | 0 | 0 | 0 | 0 |

各資料缺欄位時工具會標NOT AVAILABLE；這9個實際輸入的checks沒有NOT AVAILABLE。數值與格式符合本次既有工具檢查，不代表未檢查的市場特性也已驗證。

## 17. CSV數值與時間問題

五個CSV共 269416 筆；唯一非PASS檢查為local_event_clock_order，共 269284 筆local_receive−exchange_event負差。
| CSV | 負差警告數 | 最小ms | 最大ms |
| --- | --- | --- | --- |
| results/obi_market_data_20260827_session1.csv | 60558 | -155.713 | -31.951 |
| results/obi_market_data_20260827_session2.csv | 99871 | -4541.681 | -47.57 |
| results/obi_market_data_20260827_session3.csv | 57905 | -337.505 | 12901.877 |
| results/obi_market_data_test_20260827.csv | 951 | -102.803 | -53.977 |
| results/obi_market_data.csv | 49999 | -375.662 | -304.107 |

缺值、非有限值、數字解析、bid/ask交叉、負spread、mid/spread一致性、volume非負、OBI範圍及公式等本工具檢查皆PASS。負時間差不能當成負網路延遲，仍需釐清時鐘對齊；本次未修改CSV或時間欄位。

## 18. Snapshot／Replay銜接結果

| snapshot | replay | snapshot lastUpdateId | 第一有效U | 第一有效u | 狀態 |
| --- | --- | --- | --- | --- | --- |
| results/replay_snapshot_1000.json | results/replay_events_1000.jsonl | 100405424366 | 100405424367 | 100405424375 | PASS |
| results/replay_snapshot_50000.json | results/replay_events_50000.jsonl | 100406184838 | 100406184839 | 100406184877 | PASS |

兩組payload有效、skipped=0，符合第一個u>snapshot ID事件的U≤snapshot ID+1≤u。這是離線資料稽核，不是執行Replay binary或回測。配對輸出位於本run/audits/snapshot_replay_pair_1000及50000。

## 19. baseline與final的251檔比較

PASS：251/251共同檔，新增0、缺少0、內容變更0、metadata-only變更0。relative_path、file_type、file_size_bytes、sha256、symlink_target、mode全部相同。證據：[final/protected_files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.json>)、[final/final_integrity_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/final_integrity_summary.json>)、[final/protected_file_diff.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/protected_file_diff.csv>)。

## 20. 原有968檔完成後驗證

報告前實際檢查結果：PASS，968/968 SHA相同，缺少0；全部993個既有regular檔與10個既有symlink亦保留，沒有未授權新增路徑。每個symlink以lstat與readlink比較本體，沒有將目錄目標列為新增。

本報告寫成後再作一次終端核對，結果保存於 [final/original_968_final_verification.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/original_968_final_verification.json>) 與 [final/preexisting_preservation_check.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/preexisting_preservation_check.json>)；最終狀態以 [summary/phase1_v2_result.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/phase1_v2_result.json>) 為準。本報告不覆寫先前任何FAIL證據。

## 21. metadata-only變動

本次251檔的mtime_ns、ctime_ns、uid/gid、birth_time等metadata差異為0；[final/metadata_diff.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/metadata_diff.csv>) 保留欄位，即使無差異仍輸出。工具人工測試確認mtime/ctime-only差異會列METADATA_ONLY_CHANGE且內容PASS，mode不同則內容FAIL。舊Phase1約100ns問題沒有被新政策回溯改判。

## 22. 本次專題網路活動

Phase 1 v2 本次執行沒有由專題命令或專題程式發起 Binance、Testnet 或真實交易連線。沒有以程式測試網路可用性，沒有curl/wget/套件管理器或下載。只執行人工測試、唯讀資料稽核及編譯流程。

## 23. 本次Testnet與真實交易

本次未建置或執行Live/Capture/Testnet target、未執行真實交易，未使用API Key或Secret Key，未呼叫/api/v3/order或/api/v3/order/test。兩個Offline binary也未執行。

## 24. 歷史否定主張仍為UNVERIFIED CLAIM

保留Recovery的歷史標記；不得由本次安全執行推論過去所有執行都沒有Binance、Testnet或真實交易。另一授權聊天的歷史行情連線證據不被本次結果抹去。

## 25. ExecutionPolicy狀態

舊Bypass命令已證明為process-level；歷史CurrentUser／LocalMachine持久變更仍UNKNOWN。本次只在WSL Linux執行，未修改PowerShell ExecutionPolicy，也未為確認歷史而探測或變更Windows政策。

## 26. 所有實際執行命令

完整原始命令、輸出與子命令索引整合於 [summary/command_history.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/command_history.txt>)；包含root命令、工具與測試開發、環境、baseline/final、build及Dataset測試/九檔/配對命令。下列每份原始ledger均為本報告的命令附件；負面人工測試的預期非零退出碼與真正失敗嘗試都保留。
| 命令附件 |
| --- |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/root_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/root_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/finalizer_recovery_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/finalizer_recovery_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/manifest_development_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/manifest_development_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/manifest_test_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/manifest_test_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_child_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_child_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/environment_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/environment_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/baseline_create_command.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/baseline_create_command.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/final_manifest_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/final_manifest_commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/commands.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/commands.json>) |
| [/home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/cli_commands.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/cli_commands.jsonl>) |

最後收尾自身命令為
````text
python3 -B /home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/finalize_phase1_v2_attempt02.py
````
Add File操作只新增本輪root命令紀錄、收尾程式、修正副本與失敗紀錄；沒有修改或覆寫先前產物。

## 27. 所有新增檔案

完整新增路徑清單如下；包括人工symlink與FIFO本體。完整lstat類型、大小、mode與regular SHA另存 [summary/new_files_inventory.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/new_files_inventory.json>)，不展開任何連結、不開啟FIFO。安全CMake目錄是第十七節明確例外，其產物亦逐一記錄。
<details>
<summary>全部新增路徑（含本收尾產物）</summary>

- [artifacts/build/phase1v2_20261018T210029Z_offline/.hft_build_request.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/.hft_build_request.json>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/.hft_configure_started](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/.hft_configure_started>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeCache.txt](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeCache.txt>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CMakeCXXCompiler.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CMakeCXXCompiler.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CMakeDetermineCompilerABI_CXX.bin](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CMakeDetermineCompilerABI_CXX.bin>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CMakeSystem.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CMakeSystem.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CompilerIdCXX/CMakeCXXCompilerId.cpp](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CompilerIdCXX/CMakeCXXCompilerId.cpp>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CompilerIdCXX/a.out](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/4.2.3/CompilerIdCXX/a.out>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/CMakeConfigureLog.yaml](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/CMakeConfigureLog.yaml>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/CMakeDirectoryInformation.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/CMakeDirectoryInformation.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/InstallScripts.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/InstallScripts.json>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/Makefile.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/Makefile.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/Makefile2](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/Makefile2>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/TargetDirectories.txt](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/TargetDirectories.txt>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/cmake.check_cache](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/cmake.check_cache>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/DependInfo.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/DependInfo.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/build.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/build.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/cmake_clean.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/cmake_clean.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/compiler_depend.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/compiler_depend.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/compiler_depend.ts](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/compiler_depend.ts>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/depend.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/depend.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/flags.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/flags.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/link.d](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/link.d>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/link.txt](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/link.txt>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/progress.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/progress.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/src/offline_replay_smoke.cpp.o](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/src/offline_replay_smoke.cpp.o>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/src/offline_replay_smoke.cpp.o.d](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_1000.dir/src/offline_replay_smoke.cpp.o.d>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/DependInfo.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/DependInfo.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/build.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/build.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/cmake_clean.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/cmake_clean.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/compiler_depend.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/compiler_depend.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/compiler_depend.ts](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/compiler_depend.ts>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/depend.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/depend.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/flags.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/flags.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/link.d](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/link.d>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/link.txt](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/link.txt>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/progress.make](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/progress.make>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/src/offline_replay_batch1_50000.cpp.o](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/src/offline_replay_batch1_50000.cpp.o>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/src/offline_replay_batch1_50000.cpp.o.d](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/hft_offline_replay_50000.dir/src/offline_replay_batch1_50000.cpp.o.d>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/progress.marks](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/CMakeFiles/progress.marks>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/Makefile](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/Makefile>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/bin/hft_offline_replay_1000](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/bin/hft_offline_replay_1000>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/bin/hft_offline_replay_50000](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/bin/hft_offline_replay_50000>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/build.log](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/build.log>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/build_run.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/build_run.json>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/cmake_install.cmake](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/cmake_install.cmake>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/cmake_version.log](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/cmake_version.log>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/commands.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/commands.json>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/compile_commands.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/compile_commands.json>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/compiler_version.log](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/compiler_version.log>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/configure.log](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/configure.log>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/git.log](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/git.log>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/hft_build_metadata.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/hft_build_metadata.json>)
- [artifacts/build/phase1v2_20261018T210029Z_offline/inputs_manifest.json](</home/jason/hft-realtime-codex/artifacts/build/phase1v2_20261018T210029Z_offline/inputs_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/files_manifest.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/audit_report.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/audit_report.json>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/audit_report.md](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/audit_report.md>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/errors.csv](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/errors.csv>)
- [artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/audits/dataset_audit_verification.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/dataset_audit_verification.json>)
- [artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json>)
- [artifacts/phase1_v2/20261018T210029Z/audits/dataset_orchestrator.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/dataset_orchestrator.py>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/baseline/approval_context.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/approval_context.json>)
- [artifacts/phase1_v2/20261018T210029Z/baseline/baseline_validation.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/baseline_validation.json>)
- [artifacts/phase1_v2/20261018T210029Z/baseline/original_968_precheck.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/original_968_precheck.json>)
- [artifacts/phase1_v2/20261018T210029Z/baseline/preexisting_workspace_inventory.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/preexisting_workspace_inventory.json>)
- [artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.sha256](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.sha256>)
- [artifacts/phase1_v2/20261018T210029Z/build/build_execution.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/build_execution.json>)
- [artifacts/phase1_v2/20261018T210029Z/build/captured_build.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_build.log>)
- [artifacts/phase1_v2/20261018T210029Z/build/captured_build_run.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_build_run.json>)
- [artifacts/phase1_v2/20261018T210029Z/build/captured_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/build/captured_compile_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_compile_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/build/captured_configure.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_configure.log>)
- [artifacts/phase1_v2/20261018T210029Z/build/captured_hft_build_metadata.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/captured_hft_build_metadata.json>)
- [artifacts/phase1_v2/20261018T210029Z/build/cmake_static_safety.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/cmake_static_safety.json>)
- [artifacts/phase1_v2/20261018T210029Z/build/driver_stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/driver_stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/build/driver_stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/build/driver_stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/environment/environment.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/environment/environment.json>)
- [artifacts/phase1_v2/20261018T210029Z/final/final_integrity_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/final_integrity_summary.json>)
- [artifacts/phase1_v2/20261018T210029Z/final/metadata_diff.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/metadata_diff.csv>)
- [artifacts/phase1_v2/20261018T210029Z/final/original_968_final_verification.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/original_968_final_verification.json>)
- [artifacts/phase1_v2/20261018T210029Z/final/preexisting_preservation_check.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/preexisting_preservation_check.json>)
- [artifacts/phase1_v2/20261018T210029Z/final/protected_file_diff.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/protected_file_diff.csv>)
- [artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.sha256](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.sha256>)
- [artifacts/phase1_v2/20261018T210029Z/logs/baseline_create_command.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/baseline_create_command.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_01_obi_market_data_20260827_session1.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_01_obi_market_data_20260827_session1.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_01_obi_market_data_20260827_session1.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_01_obi_market_data_20260827_session1.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_02_obi_market_data_20260827_session2.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_02_obi_market_data_20260827_session2.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_02_obi_market_data_20260827_session2.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_02_obi_market_data_20260827_session2.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_03_obi_market_data_20260827_session3.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_03_obi_market_data_20260827_session3.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_03_obi_market_data_20260827_session3.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_03_obi_market_data_20260827_session3.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_04_obi_market_data_test_20260827.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_04_obi_market_data_test_20260827.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_04_obi_market_data_test_20260827.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_04_obi_market_data_test_20260827.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_05_obi_market_data.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_05_obi_market_data.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_05_obi_market_data.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_05_obi_market_data.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_06_replay_snapshot_1000.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_06_replay_snapshot_1000.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_06_replay_snapshot_1000.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_06_replay_snapshot_1000.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_07_replay_events_1000.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_07_replay_events_1000.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_07_replay_events_1000.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_07_replay_events_1000.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_08_replay_snapshot_50000.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_08_replay_snapshot_50000.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_08_replay_snapshot_50000.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_08_replay_snapshot_50000.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_09_replay_events_50000.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_09_replay_events_50000.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_09_replay_events_50000.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_09_replay_events_50000.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_child_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_child_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_unittest.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_unittest.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/dataset_unittest.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/dataset_unittest.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/environment_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/environment_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/final_manifest_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/final_manifest_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/finalizer_recovery_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/finalizer_recovery_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/manifest_development_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/manifest_development_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/manifest_test_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/manifest_test_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/root_commands.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/root_commands.json>)
- [artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_1000.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_1000.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_1000.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_1000.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_50000.stderr.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_50000.stderr.log>)
- [artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_50000.stdout.log](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/logs/snapshot_replay_pair_50000.stdout.log>)
- [artifacts/phase1_v2/20261018T210029Z/summary/command_history.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/command_history.txt>)
- [artifacts/phase1_v2/20261018T210029Z/summary/finalize_phase1_v2.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/finalize_phase1_v2.py>)
- [artifacts/phase1_v2/20261018T210029Z/summary/finalize_phase1_v2_attempt02.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/finalize_phase1_v2_attempt02.py>)
- [artifacts/phase1_v2/20261018T210029Z/summary/new_files_inventory.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/new_files_inventory.json>)
- [artifacts/phase1_v2/20261018T210029Z/summary/phase1_v2_result.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/summary/phase1_v2_result.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_001/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_002/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_003/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_004/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_005/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_006/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_007/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_008/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_009/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_012/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_013/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_014/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_015/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_016/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_017/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_018/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_019/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_021/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_022/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_024/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_025/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_026/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_027/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_028/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_029/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_030/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_031/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_032/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_033/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_034/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_035/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_036/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_038/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_039/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_040/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/case_041/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/audit_report.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/audit_report.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/audit_report.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/audit_report.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/errors.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/errors.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/files_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/audit_outputs/no_overwrite/files_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/cli_commands.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/cli_commands.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/fake_repo/artifacts](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/fake_repo/artifacts>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_crossed_snapshot.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_crossed_snapshot.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_crossed_snapshot_cannot_pass_an_id_only_bridge.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_crossed_snapshot_cannot_pass_an_id_only_bridge.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_csv_duplicate_and_backward_timestamps.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_csv_duplicate_and_backward_timestamps.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_empty_replay_checks_are_not_available.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_empty_replay_checks_are_not_available.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_first_update_id_cannot_exceed_final.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_first_update_id_cannot_exceed_final.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_header_only_csv_checks_are_not_available.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_header_only_csv_checks_are_not_available.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_incomplete_snapshot_cannot_pass_an_id_only_bridge.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_incomplete_snapshot_cannot_pass_an_id_only_bridge.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_invalid_numeric_text.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_invalid_numeric_text.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_invalid_payload_cannot_be_a_valid_snapshot_bridge.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_invalid_payload_cannot_be_a_valid_snapshot_bridge.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_large_integer_ids_remain_exact.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_large_integer_ids_remain_exact.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_mid_and_spread_formula_mismatches.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_mid_and_spread_formula_mismatches.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_missing_numeric_value.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_missing_numeric_value.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_nan_and_infinity_csv_are_non_finite.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_nan_and_infinity_csv_are_non_finite.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_obi_formula_mismatch.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_obi_formula_mismatch.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_pair_without_remaining_event_is_not_available.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_pair_without_remaining_event_is_not_available.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_repeated_cli_input_options_and_pairs.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_repeated_cli_input_options_and_pairs.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_repeated_cli_input_options_and_pairs.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_repeated_cli_input_options_and_pairs.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_replay_negative_quantity.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_replay_negative_quantity.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_replay_non_finite_json_constant_rejected.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_replay_non_finite_json_constant_rejected.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_replay_schema_rejects_snapshot_level_shape.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_replay_schema_rejects_snapshot_level_shape.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_null_and_nonfinite_roots_are_invalid_NaN.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_null_and_nonfinite_roots_are_invalid_NaN.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_null_and_nonfinite_roots_are_invalid_null.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_null_and_nonfinite_roots_are_invalid_null.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_unsorted_bid_prices.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_unsorted_bid_prices.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_zero_quantity_is_invalid.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_snapshot_zero_quantity_is_invalid.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_update_id_schema_rejects_bool_float_and_string.jsonl](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_update_id_schema_rejects_bool_float_and_string.jsonl>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_zero_total_volume_obi_matches_existing_formula.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/inputs/test_zero_total_volume_obi_matches_existing_formula.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/linked_output](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/linked_output>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/run_symlink_parent/linked_run](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/run_symlink_parent/linked_run>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/test_run_manifest.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_artificial_tests/test_run_manifest.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/dataset_unit_test_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/dataset_unit_test_summary.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_01_regular_file_and_required_metadata/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_01_regular_file_and_required_metadata/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_02_different_sha256_same_size_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_02_different_sha256_same_size_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_02_different_sha256_same_size_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_02_different_sha256_same_size_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_03_different_size_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_03_different_size_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_03_different_size_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_03_different_size_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_04_added_file_fails/after/analysis/added.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_04_added_file_fails/after/analysis/added.py>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_04_added_file_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_04_added_file_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_04_added_file_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_04_added_file_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_05_missing_file_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_05_missing_file_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_05_missing_file_fails/before/scripts/missing.sh](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_05_missing_file_fails/before/scripts/missing.sh>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_05_missing_file_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_05_missing_file_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_06_mode_change_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_06_mode_change_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_06_mode_change_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_06_mode_change_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_07_mtime_change_preserves_content_pass/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_07_mtime_change_preserves_content_pass/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_08_symlink_records_link_not_target_bytes/outside_data](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_08_symlink_records_link_not_target_bytes/outside_data>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_08_symlink_records_link_not_target_bytes/project/src/symbolic.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_08_symlink_records_link_not_target_bytes/project/src/symbolic.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_09_directory_symlink_is_not_expanded/outside_directory/not_scanned.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_09_directory_symlink_is_not_expanded/outside_directory/not_scanned.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_09_directory_symlink_is_not_expanded/project/src/linked_directory](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_09_directory_symlink_is_not_expanded/project/src/linked_directory>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_10_broken_symlink_is_preserved/project/src/broken](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_10_broken_symlink_is_preserved/project/src/broken>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_11_root_elf_requires_magic_and_is_never_executed/project/ordinary_executable](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_11_root_elf_requires_magic_and_is_never_executed/project/ordinary_executable>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_11_root_elf_requires_magic_and_is_never_executed/project/synthetic_elf](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_11_root_elf_requires_magic_and_is_never_executed/project/synthetic_elf>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_12_json_existing_output_is_not_overwritten/existing.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_12_json_existing_output_is_not_overwritten/existing.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_13_same_input_same_content_fields/project/results/broken](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_13_same_input_same_content_fields/project/results/broken>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_13_same_input_same_content_fields/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_13_same_input_same_content_fields/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_14_mtime_difference_is_visible_metadata_only/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_14_mtime_difference_is_visible_metadata_only/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_15_changed_symlink_target_fails/after/src/link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_15_changed_symlink_target_fails/after/src/link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_15_changed_symlink_target_fails/before/src/link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_15_changed_symlink_target_fails/before/src/link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_16_file_type_change_fails/after/src/item](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_16_file_type_change_fails/after/src/item>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_16_file_type_change_fails/before/src/item](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_16_file_type_change_fails/before/src/item>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/artifacts/unprotected.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/artifacts/unprotected.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/docs/unprotected.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/docs/unprotected.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/tools/unprotected.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_17_unprotected_scope_is_not_scanned/project/tools/unprotected.py>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_18_archive_names_are_included/project/hft_results_latest.tar.gz](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_18_archive_names_are_included/project/hft_results_latest.tar.gz>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_18_archive_names_are_included/project/results.7z](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_18_archive_names_are_included/project/results.7z>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_19_csv_existing_output_is_not_overwritten/existing.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_19_csv_existing_output_is_not_overwritten/existing.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/baseline.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/baseline.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/differences.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/differences.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/metadata.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/metadata.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/verification.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_20_verify_cli_validates_current_files/verification.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_21_create_cli_preserves_preexisting_output/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_21_create_cli_preserves_preexisting_output/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_21_create_cli_preserves_preexisting_output/existing.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_21_create_cli_preserves_preexisting_output/existing.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_21_create_cli_preserves_preexisting_output/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_21_create_cli_preserves_preexisting_output/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_22_ctime_only_difference_is_metadata_warning/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_22_ctime_only_difference_is_metadata_warning/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_23_root_symlink_is_not_dereferenced_for_elf_magic/elf_outside](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_23_root_symlink_is_not_dereferenced_for_elf_magic/elf_outside>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_23_root_symlink_is_not_dereferenced_for_elf_magic/project/root_elf_link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_23_root_symlink_is_not_dereferenced_for_elf_magic/project/root_elf_link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/created.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/created.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/created.sha256](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/created.sha256>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_24_cli_create_produces_sha256_sidecar/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_environment.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210419630554Z_1d3ca594/test_environment.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_01_regular_file_and_required_metadata/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_01_regular_file_and_required_metadata/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_02_different_sha256_same_size_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_02_different_sha256_same_size_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_02_different_sha256_same_size_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_02_different_sha256_same_size_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_03_different_size_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_03_different_size_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_03_different_size_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_03_different_size_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_04_added_file_fails/after/analysis/added.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_04_added_file_fails/after/analysis/added.py>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_04_added_file_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_04_added_file_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_04_added_file_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_04_added_file_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_05_missing_file_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_05_missing_file_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_05_missing_file_fails/before/scripts/missing.sh](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_05_missing_file_fails/before/scripts/missing.sh>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_05_missing_file_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_05_missing_file_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_06_mode_change_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_06_mode_change_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_06_mode_change_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_06_mode_change_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_07_mtime_change_preserves_content_pass/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_07_mtime_change_preserves_content_pass/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_08_symlink_records_link_not_target_bytes/outside_data](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_08_symlink_records_link_not_target_bytes/outside_data>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_08_symlink_records_link_not_target_bytes/project/src/symbolic.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_08_symlink_records_link_not_target_bytes/project/src/symbolic.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_09_directory_symlink_is_not_expanded/outside_directory/not_scanned.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_09_directory_symlink_is_not_expanded/outside_directory/not_scanned.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_09_directory_symlink_is_not_expanded/project/src/linked_directory](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_09_directory_symlink_is_not_expanded/project/src/linked_directory>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_10_broken_symlink_is_preserved/project/src/broken](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_10_broken_symlink_is_preserved/project/src/broken>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_11_root_elf_requires_magic_and_is_never_executed/project/ordinary_executable](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_11_root_elf_requires_magic_and_is_never_executed/project/ordinary_executable>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_11_root_elf_requires_magic_and_is_never_executed/project/synthetic_elf](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_11_root_elf_requires_magic_and_is_never_executed/project/synthetic_elf>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_12_json_existing_output_is_not_overwritten/existing.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_12_json_existing_output_is_not_overwritten/existing.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_13_same_input_same_content_fields/project/results/broken](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_13_same_input_same_content_fields/project/results/broken>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_13_same_input_same_content_fields/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_13_same_input_same_content_fields/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_14_mtime_difference_is_visible_metadata_only/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_14_mtime_difference_is_visible_metadata_only/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_15_changed_symlink_target_fails/after/src/link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_15_changed_symlink_target_fails/after/src/link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_15_changed_symlink_target_fails/before/src/link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_15_changed_symlink_target_fails/before/src/link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_16_file_type_change_fails/after/src/item](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_16_file_type_change_fails/after/src/item>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_16_file_type_change_fails/before/src/item](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_16_file_type_change_fails/before/src/item>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/artifacts/unprotected.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/artifacts/unprotected.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/docs/unprotected.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/docs/unprotected.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/tools/unprotected.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_17_unprotected_scope_is_not_scanned/project/tools/unprotected.py>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_18_archive_names_are_included/project/hft_results_latest.tar.gz](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_18_archive_names_are_included/project/hft_results_latest.tar.gz>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_18_archive_names_are_included/project/results.7z](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_18_archive_names_are_included/project/results.7z>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_19_csv_existing_output_is_not_overwritten/existing.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_19_csv_existing_output_is_not_overwritten/existing.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/baseline.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/baseline.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/differences.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/differences.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/metadata.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/metadata.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/verification.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_20_verify_cli_validates_current_files/verification.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_21_create_cli_preserves_preexisting_output/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_21_create_cli_preserves_preexisting_output/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_21_create_cli_preserves_preexisting_output/existing.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_21_create_cli_preserves_preexisting_output/existing.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_21_create_cli_preserves_preexisting_output/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_21_create_cli_preserves_preexisting_output/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_22_ctime_only_difference_is_metadata_warning/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_22_ctime_only_difference_is_metadata_warning/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_23_root_symlink_is_not_dereferenced_for_elf_magic/elf_outside](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_23_root_symlink_is_not_dereferenced_for_elf_magic/elf_outside>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_23_root_symlink_is_not_dereferenced_for_elf_magic/project/root_elf_link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_23_root_symlink_is_not_dereferenced_for_elf_magic/project/root_elf_link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/created.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/created.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/created.sha256](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/created.sha256>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_24_cli_create_produces_sha256_sidecar/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_environment.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210458809540Z_91f2227e/test_environment.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_01_regular_file_and_required_metadata/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_01_regular_file_and_required_metadata/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_02_different_sha256_same_size_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_02_different_sha256_same_size_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_02_different_sha256_same_size_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_02_different_sha256_same_size_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_03_different_size_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_03_different_size_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_03_different_size_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_03_different_size_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_04_added_file_fails/after/analysis/added.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_04_added_file_fails/after/analysis/added.py>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_04_added_file_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_04_added_file_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_04_added_file_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_04_added_file_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_05_missing_file_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_05_missing_file_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_05_missing_file_fails/before/scripts/missing.sh](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_05_missing_file_fails/before/scripts/missing.sh>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_05_missing_file_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_05_missing_file_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_06_mode_change_fails/after/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_06_mode_change_fails/after/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_06_mode_change_fails/before/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_06_mode_change_fails/before/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_07_mtime_change_preserves_content_pass/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_07_mtime_change_preserves_content_pass/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_08_symlink_records_link_not_target_bytes/outside_data](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_08_symlink_records_link_not_target_bytes/outside_data>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_08_symlink_records_link_not_target_bytes/project/src/symbolic.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_08_symlink_records_link_not_target_bytes/project/src/symbolic.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_09_directory_symlink_is_not_expanded/outside_directory/not_scanned.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_09_directory_symlink_is_not_expanded/outside_directory/not_scanned.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_09_directory_symlink_is_not_expanded/project/src/linked_directory](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_09_directory_symlink_is_not_expanded/project/src/linked_directory>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_10_broken_symlink_is_preserved/project/src/broken](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_10_broken_symlink_is_preserved/project/src/broken>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_11_root_elf_requires_magic_and_is_never_executed/project/ordinary_executable](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_11_root_elf_requires_magic_and_is_never_executed/project/ordinary_executable>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_11_root_elf_requires_magic_and_is_never_executed/project/synthetic_elf](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_11_root_elf_requires_magic_and_is_never_executed/project/synthetic_elf>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_12_json_existing_output_is_not_overwritten/existing.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_12_json_existing_output_is_not_overwritten/existing.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_13_same_input_same_content_fields/project/results/broken](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_13_same_input_same_content_fields/project/results/broken>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_13_same_input_same_content_fields/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_13_same_input_same_content_fields/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_14_mtime_difference_is_visible_metadata_only/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_14_mtime_difference_is_visible_metadata_only/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_15_changed_symlink_target_fails/after/src/link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_15_changed_symlink_target_fails/after/src/link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_15_changed_symlink_target_fails/before/src/link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_15_changed_symlink_target_fails/before/src/link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_16_file_type_change_fails/after/src/item](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_16_file_type_change_fails/after/src/item>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_16_file_type_change_fails/before/src/item](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_16_file_type_change_fails/before/src/item>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/artifacts/unprotected.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/artifacts/unprotected.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/docs/unprotected.md](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/docs/unprotected.md>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/tools/unprotected.py](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_17_unprotected_scope_is_not_scanned/project/tools/unprotected.py>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_18_archive_names_are_included/project/hft_results_latest.tar.gz](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_18_archive_names_are_included/project/hft_results_latest.tar.gz>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_18_archive_names_are_included/project/results.7z](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_18_archive_names_are_included/project/results.7z>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_19_csv_existing_output_is_not_overwritten/existing.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_19_csv_existing_output_is_not_overwritten/existing.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/baseline.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/baseline.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/differences.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/differences.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/metadata.csv](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/metadata.csv>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/verification.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_20_verify_cli_validates_current_files/verification.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_21_create_cli_preserves_preexisting_output/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_21_create_cli_preserves_preexisting_output/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_21_create_cli_preserves_preexisting_output/existing.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_21_create_cli_preserves_preexisting_output/existing.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_21_create_cli_preserves_preexisting_output/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_21_create_cli_preserves_preexisting_output/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_22_ctime_only_difference_is_metadata_warning/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_22_ctime_only_difference_is_metadata_warning/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_23_root_symlink_is_not_dereferenced_for_elf_magic/elf_outside](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_23_root_symlink_is_not_dereferenced_for_elf_magic/elf_outside>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_23_root_symlink_is_not_dereferenced_for_elf_magic/project/root_elf_link](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_23_root_symlink_is_not_dereferenced_for_elf_magic/project/root_elf_link>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/cli_01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/cli_01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/created.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/created.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/created.sha256](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/created.sha256>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_24_cli_create_produces_sha256_sidecar/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_25_ext4_birth_time_is_recorded_when_available/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_25_ext4_birth_time_is_recorded_when_available/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_26_unavailable_birth_time_is_not_fabricated/project/src/example.cpp](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_26_unavailable_birth_time_is_not_fabricated/project/src/example.cpp>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_27_fifo_is_identified_without_opening_or_hashing/project/src/artificial_pipe](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_27_fifo_is_identified_without_opening_or_hashing/project/src/artificial_pipe>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_28_output_symlink_ancestor_is_rejected/alias_output](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_28_output_symlink_ancestor_is_rejected/alias_output>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_environment.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_artificial_20261018T210624816474Z_40a44956/test_environment.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_test_summary.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_test_summary.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt01.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt01.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt01.stderr.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt01.stderr.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt01.stdout.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt01.stdout.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt02.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt02.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt02.stderr.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt02.stderr.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt02.stdout.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt02.stdout.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt03.json](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt03.json>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt03.stderr.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt03.stderr.txt>)
- [artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt03.stdout.txt](</home/jason/hft-realtime-codex/artifacts/phase1_v2/20261018T210029Z/tests/manifest_v2_unittest_attempt03.stdout.txt>)
- [docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md](</home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md>)
- [tests/test_protected_manifest_v2.py](</home/jason/hft-realtime-codex/tests/test_protected_manifest_v2.py>)
- [tools/protected_manifest_v2.py](</home/jason/hft-realtime-codex/tools/protected_manifest_v2.py>)

</details>

## 28. 所有FAIL、WARNING與NOT AVAILABLE

| 狀態 | 範圍 | 原因／處理 |
| --- | --- | --- |
| ERROR (已解決) | 報告收尾程式首次執行 | 主報告寫入前遇到一處括號SyntaxError；原腳本與失敗輸出保留，修正版另存新檔並通過AST語法檢查。 |
| FAIL (已解決) | Manifest人工測試attempt01 | 第一輪新增的額外ctime-only測試連續chmod/還原落在同一檔案系統時間粒度，ctime沒有變化，人工fixture的assertNotEqual失敗。已僅修正本輪新增測試，使用明確+1ns人工metadata比較樣本；首次FAIL證據保留。不是工具未識別真實已變更ctime。 |
| ERROR (已解決) | 環境探查前兩次 | O_NOATIME讀/proc及root-owned系統標頭回EPERM；改對系統檔採一般唯讀，專案保留O_NOATIME。完整錯誤保留。 |
| ERROR (已解決) | 工具開發讀Linux UAPI標頭 | O_NOATIME系統標頭權限失敗，改一般唯讀取得；不修改系統檔。 |
| WARNING | 5個CSV | 269284筆local−event負差；不能當作負網路延遲。 |
| NOT AVAILABLE | Git commit／狀態 | 本資料夾非Git repository，git rev-parse exit128。 |
| NOT AVAILABLE | CPU isolation | 只讀取sysfs觀察值，未完整驗證隔離配置，不宣稱已啟用。 |
| UNKNOWN | 歷史ExecutionPolicy持久變更 | 保留Recovery結論，缺歷史前態；本次不變更或探測Windows政策。 |
| UNVERIFIED CLAIM | 歷史全面無網路／Testnet／交易否定主張 | 保留Recovery標記；本次僅對本輪執行負責。 |
| UNKNOWN | 954→968新增14檔來源分類 | 保留為既有歷史內容，新基線不改變來源分類。 |

正式九檔checks沒有FAIL或NOT AVAILABLE；5個WARNING保留為資料品質問題，稽核本身已完成。舊Phase1 FAIL保持有效。
<details>
<summary>全部正式資料非PASS檢查（不含重複樣本）</summary>

````json
[
  {
    "input": "results/obi_market_data_20260827_session1.csv",
    "check": "local_event_clock_order",
    "status": "WARNING",
    "count": 60558,
    "checked": 60558,
    "detail": "See errors.csv for every occurrence; samples are capped at 20."
  },
  {
    "input": "results/obi_market_data_20260827_session2.csv",
    "check": "local_event_clock_order",
    "status": "WARNING",
    "count": 99871,
    "checked": 99871,
    "detail": "See errors.csv for every occurrence; samples are capped at 20."
  },
  {
    "input": "results/obi_market_data_20260827_session3.csv",
    "check": "local_event_clock_order",
    "status": "WARNING",
    "count": 57905,
    "checked": 58037,
    "detail": "See errors.csv for every occurrence; samples are capped at 20."
  },
  {
    "input": "results/obi_market_data_test_20260827.csv",
    "check": "local_event_clock_order",
    "status": "WARNING",
    "count": 951,
    "checked": 951,
    "detail": "See errors.csv for every occurrence; samples are capped at 20."
  },
  {
    "input": "results/obi_market_data.csv",
    "check": "local_event_clock_order",
    "status": "WARNING",
    "count": 49999,
    "checked": 49999,
    "detail": "See errors.csv for every occurrence; samples are capped at 20."
  }
]
````

</details>

<details>
<summary>本次完成條件逐項結果</summary>

````json
{
  "initial_968_pass": true,
  "manifest_tests_pass": true,
  "tested_sources_unchanged": true,
  "baseline_exactly_251": true,
  "approved_source_in_baseline": true,
  "cmake_safety_pass": true,
  "configure_success": true,
  "offline_build_success": true,
  "only_two_offline_targets": true,
  "offline_binaries_not_executed": true,
  "dataset_tests_pass": true,
  "nine_datasets_completed": true,
  "audited_input_hashes_match_baseline": true,
  "final_protected_251_pass": true,
  "original_968_final_pass": true,
  "all_prior_files_and_symlinks_preserved": true,
  "new_paths_authorized_only": true,
  "no_project_network_connections": true,
  "no_testnet_or_real_trading": true,
  "execution_policy_not_modified": true,
  "old_phase1_fail_and_recovery_preserved": true,
  "formal_report_created": true
}
````

</details>

## 29. Phase2是否可開始

本次結果為 PHASE 1 V2 PASS。本輪不得進入Phase2；建議先由人工審核報告及CSV時鐘警告，再另行批准後續工作。未建立quantum-hft、模型、回測或Paper Trading。

## 30. 沒有虛構數據

所有測試數、hash、時鐘警告、build結果與時間皆來自本次實際執行及保存的輸出，沒有用舊43項紀錄替代重跑，也沒有把缺欄位當PASS。初次fixture失敗、系統檔讀取權限錯誤及無Git資訊皆保留。PASS只限本次安全研究基線與流程條件，不表示CSV時鐘品質問題已解決，亦不表示策略或交易性能已驗證。完成後停止，等待人工審核。
