# Phase 2C-R1：隱藏目錄鑑識報告

**鑑識完成；來源 UNKNOWN，依使用者第七節停止。** 尚未刪除四個目錄，沒有修改測試或建立新 Phase 2C run；舊 FAIL 未改為 PASS。

## 1. 範圍、run_id 與舊證據

repair run_id：20261018T235018Z。舊FAIL run_id：20261018T232041Z。工作目錄pwd／realpath均為/home/jason/quantum-hft；findmnt確認ext4、/dev/sdd、掛載/。初始唯讀工具namespace顯示ro，statx採證程序namespace顯示rw；這是各次觀察的mount設定，不用來推定歷史建立者。

舊 [20261018T232041Z](/home/jason/quantum-hft/artifacts/phase2c/20261018T232041Z) 與 [PHASE2C_REPORT_20261018T232041Z.md](/home/jason/quantum-hft/docs/PHASE2C_REPORT_20261018T232041Z.md) 完整保留。173份舊FAIL檔案及全部431份既有專案檔案SHA／mode／size／mtime／ctime一致。見 [preservation_comparison.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/preservation_comparison.json)。保存快照是事故證據，**不是新正式研究基線，也沒有將四目錄加入allowlist**。

## 2. 四目錄完整 stat

| 相對路徑 | 絕對路徑 | owner | group | permissions | inode | device | size | nlink |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tests/.agents | /home/jason/quantum-hft/tests/.agents | jason(1000) | jason(1000) | drwxr-xr-x 0o755 | 116288 | 2096 | 4096 | 2 |
| tests/.aws | /home/jason/quantum-hft/tests/.aws | jason(1000) | jason(1000) | drwxr-xr-x 0o755 | 116316 | 2096 | 4096 | 2 |
| tests/.codex | /home/jason/quantum-hft/tests/.codex | jason(1000) | jason(1000) | drwxr-xr-x 0o755 | 116315 | 2096 | 4096 | 2 |
| tests/.git | /home/jason/quantum-hft/tests/.git | jason(1000) | jason(1000) | drwxr-xr-x 0o755 | 116287 | 2096 | 4096 | 2 |

| 目錄 | birth UTC | mtime UTC | ctime UTC | atime UTC |
| --- | --- | --- | --- | --- |
| tests/.agents | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:51.011403337Z |
| tests/.aws | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:51.011403337Z |
| tests/.codex | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:50.815403338Z | 2026-10-18T23:26:51.011403337Z |
| tests/.git | 2026-10-18T23:26:50.811403338Z | 2026-10-18T23:26:50.811403338Z | 2026-10-18T23:26:50.811403338Z | 2026-10-18T23:26:51.011403337Z |

statx取得birth time，mask有效；不是以ctime冒充birth。全部存在、directory=true、symlink=false、symlink target=null。完整原始nanosecond、mount ID與採證方法見 [unexpected_directories_inventory.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/unexpected_directories_inventory.json)。只做lstat/statx與NOFOLLOW／NOATIME目錄列舉，未跟隨任何symlink，未執行其中內容。

## 3. 空白、隱藏內容與 mount 判定

| 目錄 | direct child | recursive entries | hidden entries | 完全空白 | symlink | mount point |
| --- | --- | --- | --- | --- | --- | --- |
| tests/.agents | 0 | 0 | 0 | True | False | False |
| tests/.aws | 0 | 0 | 0 | True | False | False |
| tests/.codex | 0 | 0 | 0 | True | False | False |
| tests/.git | 0 | 0 | 0 | True | False | False |

當次/proc/self/mountinfo無四目錄的exact mount entry，os.path.ismount亦false；覆蓋mount為ext4 /dev/sdd。mount判斷僅代表採證時的程序namespace，未宣稱從來沒有歷史bind mount。最後再次唯讀核對inode、mtime、ctime及空白狀態相同。

## 4. Credential、config 與 Git metadata

四目錄目前recursive entry count全部0，因此沒有任何可見或隱藏credential、config、Git object或其他內容；security_review_required=false。這不證明歷史從未有過內容。沒有讀取auth.json、AWS憑證、login內容或秘密環境值；沒有執行任何隱藏檔案。空目錄沒有子檔可計算SHA，目錄清單本身以JSON及其SHA保存。

## 5. 出現時間與測試先後

前置inventory先掃描，再驗九來源與執行318既有回歸，成功後才產生舊run_id；不能將inventory檔寫入mtime當成掃描時刻。四目錄在該前置清單中不存在。statx birth顯示.git於23:26:50.811403338Z，其餘三者於23:26:50.815403338Z建立，相差4ms。

| 角色／測試 | 原生tool dispatch UTC | session行號 |
| --- | --- | --- |
| root | 2026-10-18T23:30:44.217Z | 3678 |
| audit_rules | 2026-10-18T23:27:27.209Z | 190 |
| builder | 2026-10-18T23:27:00.047Z | 87 |
| reference | 2026-10-18T23:27:09.100Z | 139 |

最早已記錄Phase2C unittest dispatch為23:27:00.047Z，比最晚birth晚9.231596662秒。因此可判定目錄先於**已記錄的Phase2C測試命令發送**存在；不把dispatch當精確subprocess啟動時間，不以結果檔mtime推定執行時刻，也不藉此識別建立者。318既有回歸是更早的不同套件。

原生session證據包含檔案路徑、行號、UTC、input SHA及命令片段，見 [codex_log_analysis.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/codex_log_analysis.json)；完整事件類型、baseline語義及序列見 [unexpected_directories_timeline.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/unexpected_directories_timeline.json)。

## 6. 相關測試、mkdir 與程式碼搜尋

唯讀掃描54份專案Python（核心45份及artifact Python9份），保存每檔SHA、AST呼叫、行號與函式，未import/執行被審查模組。四名稱只有舊FAIL報告生成器敘述／assert命中，沒有建立操作。

主要fixture路徑在 [test_build_features_tool.py](/home/jason/quantum-hft/tests/test_build_features_tool.py) BuildFeaturesTests.setUp／tearDown，以及 [test_feature_writer.py](/home/jason/quantum-hft/tests/test_feature_writer.py) FeatureWriterTests.setUp；暫存使用tests/fixtures/phase2c下隨機cli_artificial_／writer_目錄。沒有直接建立tests直下四名稱的程式碼、git init、HOME重設或chdir。正式FeatureBuilder及Phase2A／2B介面沒有被修改。

CLI測試setUp配置TemporaryDirectory，僅在tearDown清理；若setUp本身失敗，tearDown不一定執行，是一般清理弱點，**沒有因果證據連到這四目錄**，不能據此改測試。完整搜尋字串、等價操作及限制見 [creation_code_search.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/creation_code_search.json)。

## 7. HOME／XDG／AWS／Codex 環境分析

| 變數 | 當下觀察 | 歷史判斷 |
| --- | --- | --- |
| HOME | /home/jason | UNKNOWN；不能以當下值還原歷史 |
| XDG_CONFIG_HOME | 未設 | NOT_AVAILABLE |
| AWS_CONFIG_FILE | 未設 | NOT_AVAILABLE |
| CODEX_HOME | /mnt/c/Users/jason/.codex | 完整歷史環境NOT_AVAILABLE |

僅讀這四個允許的路徑變數，未dump全環境。已查4個本phase相關session（root與3子agent），23:19至23:40共182個tool call；未見四目錄明確建立命令或相關環境重設。出生時間附近23:26:48.030、48.796、49.557有apply_patch發送，但無工具內部mkdir、建立PID或stack trace。

Windows log SQLite checkpoint只到19:04；Linux checkpoint到23:38，在23:25–23:28只有6條無thread ID的一般app訊息，無相關建立證據。SQLite只讀原檔再於RAM查checkpoint，未寫db、未重建WAL；未讀候選／內容排除與缺口在 [codex_log_analysis.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/codex_log_analysis.json)。沒有歷史syscall audit，不能排除外部程序。

## 8. 來源分類與九個必要判斷

| 目錄 | 分類 | 直接建立證據 |
| --- | --- | --- |
| tests/.agents | UNKNOWN | 未找到 |
| tests/.aws | UNKNOWN | 未找到 |
| tests/.codex | UNKNOWN | 未找到 |
| tests/.git | UNKNOWN | 未找到 |

| 題號 | 判斷 | 證據支持的結論 |
| --- | --- | --- |
| 1 | 測試前或測試期間 | 四目錄birth早於已記錄的所有首次Phase2C unittest dispatch；最早dispatch為23:27:00.047Z，比最晚birth晚9.231596662秒。318既有回歸為較早的獨立測試組，不混為Phase2C測試。 |
| 2 | 是否同時建立 | .git先建立，其他三者晚4,000,000ns；近同期但非四者同一精確時間。相同timestamp不能識別建立者。 |
| 3 | 是否同一程式碼建立 | UNKNOWN；沒有creator PID、mkdir syscall或stack trace。 |
| 4 | 是否人工fixture | UNKNOWN；掃描未發現四個hidden名稱對應的fixture建立操作。已記錄的Phase2C unittest dispatch晚於birth，不能把它們稱為已確認測試殘留。 |
| 5 | HOME誤指tests後初始化 | UNKNOWN；當下HOME=/home/jason，歷史完整環境不可得。來源及命令未見相關重設，不能據此還原歷史HOME。 |
| 6 | 路徑逃逸或清理失敗 | 未找到能連結四目錄的直接證據。CLI test setUp中建立TemporaryDirectory而tearDown清理存在setUp失敗時未保證清理的一般弱點，但不是此事故根因證據。 |
| 7 | 實際建立命令或stack trace | NOT_FOUND_IN_SEARCHED_SCOPE；不能把讀取/診斷目錄名稱當成建立命令。 |
| 8 | Codex自身建立可能性 | 時間附近有三個apply_patch dispatch；只有時間關聯，未找到內部mkdir或sandbox建立事件，不能分類CONFIRMED_CODEX_CREATED。 |
| 9 | 外部程序證據 | 已查範圍未找到外部程序建立證據；歷史syscall audit/creator PID不可得，不能排除或確認。 |

不將相同owner、相近時間、四個特殊名稱或附近apply_patch視為creator證明；不使用CONFIRMED_PHASE2C_TEST_ARTIFACT、CONFIRMED_CODEX_CREATED、CONFIRMED_PREEXISTING或CONFIRMED_EXTERNAL_PROCESS。

## 9. 根因

**UNKNOWN**。已確認的是目前空白狀態、birth time及其早於已記錄Phase2C unittest dispatch；未取得建立者PID／實際mkdir呼叫／建立stack trace。沒有直接證據證明由同一段程式、測試、Codex自身或外部程序建立。

[root_cause_analysis.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/root_cause_analysis.json) 對結論逐項連結證據SHA；[command_evidence.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/command_evidence.json) 將實際命令、補丁、診斷提及及stderr分開。未知不等同於測試無缺點，也不等同於已確認Codex行為。

## 10. 建議處理與修復範圍

依使用者第七節停止並保留現況。等待人工決定是否另行授權取得建立程序／syscall事件或有隔離邊界的重現證據；本次沒有做重現實驗。現有證據不足以選定需要修正的測試或正式程式，沒有執行任何修復。

若未來取得直接測試因果證據並另獲批准，再依附件要求採context-managed TemporaryDirectory、失敗路徑清理與環境恢復驗證；不能降低安全檢查、不能將四目錄加入allowlist或新正式基線。

## 11. rmdir 與人工批准門檻

技術採證顯示四目錄當下均為普通、非symlink、非mount的空目錄，但**清理來源證據門檻不成立**，因此目前不可以執行rmdir，也不提出清理批准申請。

沒有執行rmdir或遞迴刪除，沒有取得清理批准。[proposed_cleanup.json](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/proposed_cleanup.json) 將每個條件分別記錄；只有未來直接來源證據及明確人工批准均成立，且再次核對inode／類型／mount／空白後，才可逐一非遞迴rmdir，任何錯誤立即停止。

## 12. 測試修正、回歸與新 Phase 2C

修改測試檔案：無。本次沒有執行修復回歸、318既有回歸或201 Phase2C測試，沒有處理CSV、Replay、Reference或確定性重跑，沒有建立新Phase2C run/report。

舊run的318／201 PASS與特徵結果僅作鑑識參考，**不沿用為新run驗收結果**。新run_id=null、execution_status=NOT_STARTED；Phase2C整體PASS條件仍不成立，保留原FAIL。沒有Label、Target、模型、回測、Paper Trading、QUBO、QAOA、網路或交易，也沒有進入Phase2D。

## 13. 保留聲明、完整性與停止點

**尚未刪除四個目錄。** 四目錄inode、mtime、ctime及空白狀態保持不變；tests/與專案根目錄direct child清單相同。舊FAIL的173份檔案及全部431份既有專案檔案內容／metadata不變；本次新增未核准項目0，仍待處理的原有未核准目錄4。

九HFT來源重新驗證前後SHA及大小一致，三HFT保留樹metadata分別1385／2538／1302筆相同；未寫入HFT、未執行binary。完整性比較排除atime，讀取盡量使用NOATIME；四目錄完整stat另明列atime。

所有命令與工具結果見 [command_history.txt](/home/jason/quantum-hft/artifacts/phase2c_repair/20261018T235018Z/command_history.txt)、root command分片index與三個agent命令JSON。輸出採新run與exclusive create，舊FAIL完全保留。鑑識至此停止，等待人工決定；**不建議開始Phase2D**。
