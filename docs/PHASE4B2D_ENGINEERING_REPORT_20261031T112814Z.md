# Phase 4B-2D 工程驗收
狀態：**PASS_WITH_RESTRICTIONS**；run_id：20261031T112814Z。
本輪完成可執行的離線核心，不授權正式 Capture、模型研究或交易。F03/F43 未裁定；既有歷史研究結論不變。

## 交付及建置
程式根目錄：/home/jason/quantum-hft/artifacts/phase4b2d/20261031T112814Z；最小流程見 [/home/jason/quantum-hft/artifacts/phase4b2d/20261031T112814Z/README.md](/home/jason/quantum-hft/artifacts/phase4b2d/20261031T112814Z/README.md)。
C++17、GCC 15.2.0、CMake 4.2.3；Boost 1.90.0、nlohmann/json 3.11.3、OpenSSL 3.5.5。
CMake configure/build exit=0，編譯 stderr 為空。未安裝依賴。
Python executable：/home/jason/.venvs/quantum-hft-qml/bin/python，採 -I -B -S，僅標準庫和本次來源，不匯入模型。
完整命令、stdout/stderr/exit：logs/commands.json、logs/command_history.txt、gate/command_history.json。
正式前 development/phase4b2d/20261031T112444Z 已通過同版63測試；code_lock_manifest.json 鎖定20個交付來源／契約／說明檔，正式後逐項SHA再核對通過。與開發版本相同的核心程式；預定差異僅run路徑、人工UUID/時間/受保護inode及新輸出。

## C++ 獨立核心
src/replay.cpp：payload()/envelope() 原生驗證 Spot JSON e/E/s/U/u/b/a，拒絕 Futures pu、額外欄位、型別錯誤、非正價格、負數量、重複價位及重複JSON key。
Engine::snapshot()/diff() 使用 std::map<Exact,Exact>，數量為覆寫、零刪除；有限 Snapshot 內界證明top5、cross/空/不足深度拒絕。
支援Snapshot之前bounded buffer、舊事件忽略、近期duplicate/conflict、連續ID、gap及倒退event time拒絕、明確notice/new Snapshot resync。
Engine::boundary()/tail() 不跨source/session/connection/reset/file建立標籤。每個native invocation只讀一個journal。
src/decimal50.hpp：Exact、decimal50()/mid50()/return50() 用 cpp_int 任意精度有理數及整數HALF_EVEN，不以浮點決定價格、報酬或方向。
加總→舍入→除2→舍入；報酬除→舍入→減1→舍入→乘10000→舍入。
Decimal數值比較容忍0；格式化去除尾零不改變數值。C++未呼叫Python核心。

## Raw-to-Label 與獨立驗證
完整流程已執行：CaptureWriter→journal.jsonl/session_manifest.json→C++ CLI→Python A/B→人工Oracle→integrity。
tools/verify_pipeline.py 的 compare()/observed() 被動觀測未改動的A字典與B Fraction列表，逐行比較已知完整Book、BBO/mid、raw順序、segment、endpoint/actual/error、return/direction及invalid reason。
refs/schema.py、reference_a.py、reference_b.py 與封存來源逐byte SHA相同。
人工Oracle獨立手算：bid99、ask101→mid100；1000ms插入bid100、ask101→mid100.5，return50bps、UP=2。
另有DOWN/FLAT、同timestamp第一筆、1001ms可用、1002ms MATCH_ERROR、tail、重連不跨段、精度50舍入、top5數量/刪除、錯誤與資源上限斷言。
正常案例 6 Book + 6 labels 一致；first及cold repeat輸出SHA：2c839a826b4ef02d528969b3760bc302a200b610f58b7d34d35511017e999b42。
Engine::invalid_endpoint() 對first future Book失效保留timestamp/actual/error及INVALID_FUTURE_FEATURE_ROW，future_mid=null，不產生return/direction；後續exit2並保存RESYNC_REQUIRED錯誤。
Buffered-before-Snapshot及失敗案例亦有獨立人工斷言；並非每項錯誤都能由舊Python核心回傳逐列結果（舊A/B會raise），不將錯誤分支冒稱逐列三方等價。
所有一致性只適用已執行人工案例，沒有驗證真實市場所有輸入。

## F03 仍 PARTIAL
沿用已封存政策：先忽略u<=L，首個剩餘事件要求U<=L<u；同步後U>local_u+1則UPDATE_GAP。
gate/f03_boundary_results.json 明列L−1、L、L+1、L+2、u=L等結果，另有同步後連續/gap/重複與緩衝測試。
U=L+1 bootstrap繼續拒絕，未改主路徑。
官方文字依據只引用既有封存快照 artifacts/phase4b2c_closeout/20261031T100236Z/official_github_document.md（SHA在integrity_report），本輪未上網。
該文件bootstrap要求L位於[U,u]，steady-state另有local+1規則；不同階段的文字不能直接視為同情境矛盾，也不能擅自採寬鬆解讀。
沒有上游commit及2026-08-26歷史版本證據；教授仍須裁定正式版本與Bootstrap政策。

## Capture Writer、持久化與恢復
tools/capture_writer.py：CaptureWriter.append()/reconnect()/close() 記錄session/connection UUID4、source SYNTHETIC_ONLY、producer版本、接收wall/mono、processing時計、raw順序、Snapshot/Diff IDs、notice及UTC起迄與環境。
每筆保留raw_payload/raw SHA及record hash chain；closeout全檔SHA與大小；C++同時計算raw/record鏈及全檔SHA。
receive_wall_ns是人工append的使用者空間讀取完成近似；不是kernel network receive。Exchange E、wall、monotonic、processing及replay計時分開，不估網路延遲。
新檔exclusive；每筆flush、每64筆fsync、closeout檔與目錄fsync。
read_journal()/recover() 驗證完整prefix；不截斷舊檔，複製到新檔。新connection/new Snapshot重新開始，不猜測中斷期間行情。
已測人工partial-last-record及未closeout恢復、原始SHA不變、完整但損壞record拒絕、重新啟動及manifest SHA不符。
這是故障注入，不宣稱已實測斷電、SIGKILL、磁碟控制器或檔案系統耐久性。

## 測試、效能與可重現性
Regression **63/63 PASS**：原Strict V2 30項＋新離線管線/權限/儲存33項；0failure/error/skip。
CTest **1/1 PASS**，內含7項精確算術檢查。
沒有重跑舊90項全Runner Suite，也沒有將F03/F43或歷史F39改為PASS。
共保存61個native子程序命令；其中預期拒絕的exit2由測試斷言驗證，不是成功資料。
兩個獨立冷啟動native程序讀同一封存人工journal，Book/label bytes完全一致；未聲稱OS page cache已清空。
大量人工資料：
| events | replay seconds | process peak RSS KiB | max pending | book levels |
|---:|---:|---:|---:|---:|
|5000|0.152699|45416|1000|14|
|20000|0.614960|45416|1000|14|

固定價格人工Oracle逐列驗證：N−1000筆FLAT有效label、1000筆tail；20,000事件沒有載入為一個Python列表。
RSS為getrusage process high-water，可能包含啟動/配置成本，不是原生Book allocator精確用量或HFT延遲benchmark。
Writer每5000筆輸出已處理/總數/百分比/錯誤數及可估ETA；C++每5000筆輸出同類進度，ETA未可靠估計則NOT_AVAILABLE。
C++ endpoint使用deque單向處理、Book使用map；不做O(N²)未來搜尋。原B僅小fixture運行，不用於大流。
明確技術cap與超限拒絕：raw行4MiB、metadata8MiB、decimal1024字元/小數512位/計算指數4096、單側updates10000、Book接受上限100000、pending及bootstrap4096、duplicate window8192；full Book診斷256價位上限。
極舊已涵蓋事件忽略，不宣稱8192筆以外仍能證明所有重複payload衝突。參數超限失敗不可靜默drop後標成功。

## 開發失敗保留
開發各次紀錄仍在development/phase4b2d/：111247測試程式名稱誤擋；111812人工canary名稱誤擋；111857拒絕日誌名稱誤擋；112214準備路徑替換錯誤未啟動管線；112020通過57項，112242通過62項，112444最終63項。
修正程式/fixture用途與證據檔名，未移除assertions、未使用市場結果選擇設定；前述失敗未改寫為PASS。
development_preflight.json與各run的logs、development_history.json保留版本與證據。

## 安全、完整性及歷史事故
integrity_report.json：21878既有檔案/連結 metadata一致；包含ML venv 6838、QML venv 9352、舊artifacts 5639、舊docs 49。
核對mode/size/mtime_ns/inode/device；目錄僅核對身分/mode，允許新增本輪路徑導致父目錄mtime變動。
Dataset/Frozen/venv未被本次命令修改；**這是metadata完整性，不是重新驗證內容SHA**，無法排除相同size/mtime的外部惡意改寫。
5個明列非市場文件/manifest錨點SHA與封存值一致；只讀那些文件，不遞迴使用舊opaque manifest授予內容存取。
真實Test/Holdout內容open=0；模型fit/predict=0；市場Quantum Kernel=0；網路/套件安裝/QPU/交易/回測=0。Final Holdout LOCKED。
原事故永久保留TEST_OPENED_FOR_OPAQUE_HASH_WITHOUT_PHASE_APPROVAL、60次歷史Test open與原F39 FAIL，舊Test未來確認資格仍需研究負責人審核。
phase_read_policy.json 綁定本run/phase、synthetic-only與舊inode deny；Python Guard與native使用同一版本政策。
私有TMPDIR 0700、TMPDIR/TEMP/TMP啟動前設定、無pycache；外部寫入、symlink、..、protected inode aliases、人工Test/Holdout存取及覆寫拒絕測試通過。
應用層防護不是OS強制隔離；沒有全機syscall監控證據，不排除同帳戶惡意程式、FD繼承、TOCTOU與政策替換；不宣稱普遍無資訊洩漏。

## 後續工程條件
已具備離線Capture資料契約與C++ replay的可執行基礎，可提交下一輪工程審核。
**尚未具備啟動正式跨日Capture的全部條件**：F03正式版本/政策裁定；F43保管角色與批准；歷史Test事故資格裁定；真實傳輸/限速/重試/磁碟配額/跨日rotation/OS帳戶隔離及實際故障驗收；真實raw來源與雙Reference驗證。
沒有新增模型因素、沒有使用Test/Final Holdout選參，也未開始競賽報告、QAOA或QPU。
本輪完成後停止，等待人工審核。
