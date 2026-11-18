# Phase 4B-2E Capture Readiness
run_id：20261031T115910Z。
**ENGINEERING_READY（限定離線人工Capture）／APPROVAL_PENDING；本輪沒有Live Capture授權。**
完成原生C++ Capture Writer/Adapter及正式離線驗收。這不代表已完成真實WS/REST、OS保管隔離或可自動上線。

## 1. 工程交付與執行
根目錄：/home/jason/quantum-hft/artifacts/phase4b2e/20261031T115910Z；重現步驟：[README](/home/jason/quantum-hft/artifacts/phase4b2e/20261031T115910Z/README.md)。
C++17 / GCC15.2 / CMake4.2.3 / Boost1.90.0 / nlohmann3.11.3 / OpenSSL3.5.5；Python：/home/jason/.venvs/quantum-hft-qml/bin/python（-I -B -S）。
configure/build exit0；編譯stderr為空；未安裝或升級套件。
src/capture_adapter.cpp：Transport / SnapshotProvider為注入介面；CLI僅建立SyntheticTransport / SyntheticSnapshots，沒有WebSocket/REST driver或自動工作。
本輪新增CaptureWriter（C++）。Phase4B2D原Writer是Python，未冒稱已存在C++ Writer。
CaptureAdapter::execute()/drain()/reset()處理buffer、Snapshot、同步、gap、reconnect、檔案/session/UTC輪替及shutdown。
src/core.hpp是Phase4B2D原始計算本文逐byte抽出；Book、Decimal50及1000ms標籤政策不改。新Replay只擴充phase-root綁定及拒絕QUARANTINED來源。
Python A/B和Strict Schema仍逐byte與原來源一致。程式與設定在正式測試前鎖定27項SHA，正式後再驗通過。
未修改舊Runner；沿用既有phase_guard.py及path/inode政策，新增Adapter測試工具，不建立新的Recovery階段。

## 2. F03 Decision Matrix
f03_decision_matrix.json列出Bootstrap U=L−1/L/L+1/>L+1、buffer u<=L、steady-state連續/gap、等號/重複衝突與有限Snapshot差異。
現行官方commit：f0ee79c8ce24dbeda6645211b9504e237fddef19（2026-10-15）。
查詢2026-08-26 UTC日結束以前path history，取得候選commit e556feb906511189fc423e3b58c0452366e802d3（2026-06-09）；兩份正文/metadata/query回應均封存。
這補足repo版本證據，不證明歷史producer當時採用何種規格；舊報告不回寫。
官方Bootstrap要求先緩衝、Snapshot不能落後初始U、丟棄buffer內u<=L，再以涵蓋L的首個剩餘event銜接。
steady-state的local_u+1是另一階段；不能直接拿來接受初次U=L+1。
一般舊事件條件對等號的細節與本研究忽略u<=local及duplicate衝突防護不完全相同，須明列核准。
建議教授鎖定官方版本與現有保守Bootstrap，不擅自放寬；**F03仍PARTIAL／APPROVAL_PENDING**。
來源：[現行官方版本](https://github.com/binance/binance-spot-api-docs/blob/f0ee79c8ce24dbeda6645211b9504e237fddef19/web-socket-streams.md#how-to-manage-a-local-order-book-correctly)、
[歷史候選版本](https://github.com/binance/binance-spot-api-docs/blob/e556feb906511189fc423e3b58c0452366e802d3/web-socket-streams.md#how-to-manage-a-local-order-book-correctly)。
metadata時間已明確標為開發封存時刻，不冒稱精確HTTP response完成時間。

## 3. Capture格式、來源與時鐘
CaptureWriter::raw_first()先把原始Transport文字寫入transport_raw.jsonl再parse；包含Transport sequence、offset、raw SHA、synthetic wall/mono與session/connection。
合法事件另寫journal.jsonl，保留原raw文字、hash chain、Strict envelope、Snapshot lastUpdateId與Diff U/u。
journal sequence含Snapshot/notice，與純Transport sequence分開，不能混稱同一個時鐘或序號。
capture_timing.jsonl存真實CLOCK_MONOTONIC parse區間；Book/feature/Label在獨立Replay處理。
Manifest內含Snapshot UUID/ref/offset/SHA/lastUpdateId、binary/config/policy/Protocol SHA及三份檔案size/SHA。
人工delivery時鐘不是kernel receive；processing/replay也不是Exchange E。此版本UUID是deterministic人工fixture身分，不能當作真實capture身份證據；正式UUID來源與時鐘採樣仍需驗收。
Snapshot暫不可取得及過期重試已測；gap log保留previous_u/next_U/next_u/connection/raw引用；reconnect保存來源原因。
SEALED_VALID表示成功封存且同步的候選capture段，仍必須通過Replay/Book/Label/獨立Reference才有研究資格。

## 4. 資源設定與故障
capture_resource_limits.json明列版本、來源及預設。這些是離線工程預設，不是正式擷取預算：
|限制|預設|來源與範圍|
|---|---:|---|
|Queue|64筆／1MiB|工程預設；硬cap4096筆／16MiB|
|Frame|64KiB|工程防護；超限停止|
|處理address space|256MiB RLIMIT_AS|工程預設；實測RSS另列，非OS多帳戶隔離|
|各data stream檔|4MiB|journal/raw/timing各自檢查|
|每job logical quota|32MiB|應用層bytes預算；不是filesystem project quota|
|最低可用空間|4MiB|每次寫入前statvfs，人工低空間注入|
|Metadata預留及單檔cap|64KiB|Manifest/log另受此cap及總quota限制|
|Segments|128|硬cap|
|Connection重建|每session10|Phase4B2B提案；檔案輪替也新connection，計入上限|
|Snapshot requests|每次銜接3次|Phase4B2B提案；不無限重試|
|Backoff|1/2/4/8/16/30秒封頂|本輪虛擬clock；三次請求對應0/1000/3000ms累計|
|fsync|每64筆及closeout|未同步前不承諾該點durability|

大量fixture明確override：data檔64MiB、job96MiB；不更改預設或研究政策。
磁碟quota只計Capture job管理的logical bytes，Gate/Replay結果是另外的測試輸出；allocated blocks另量測。
每筆寫入kernel，batch及closeout fsync；Manifest先.pending→fsync→no-overwrite hardlink→移除pending→fsync目錄。新目錄父層也fsync。
失敗不發布可用seal；原始partial檔及stderr保留；closeout不能對已finalized hash重試製造錯誤seal。
已測：buffer筆數/bytes、空間不足、quota、ENOSPC部分寫入、fsync失敗、file/session/UTC輪替、maxSegments、retry/reconnect耗盡、schema錯誤先保留raw、禁止覆寫。
真實SIGKILL在人工握手邊界中止後，驗證prefix恢復到新檔、原檔SHA不變，重新新session/Snapshot；真實SIGTERM/SIGCONT測得優雅closeout。
沒有斷電/硬體耐久性、真實HTTP Retry-After或網路故障的證明；虛擬retry時鐘不冒充實際等待或已驗收HTTP backoff。

## 5. 正式端到端與Determinism
真正CaptureAdapter→原生Writer→Raw/journal→C++ Replay→Python A/B→人工Oracle→Integrity。
normal：6筆人工diff，完整Book/價格/mid/endpoint/return/方向與獨立Reference一致；手算mid100→100.5，1000ms、50bps、UP。
fault flow：6筆，Update ID gap=1；前3筆所在段QUARANTINED且Replay拒絕，後段新Snapshot獨立驗證，1200→2200ms為50bps/UP。所有Transport序號0..5仍保存。
不同file/session/connection不跨段Label；輪替tail不隱藏。
正常與含gap的有效後段都經獨立冷啟動native重播，核心輸出完全相同。
正常輸出SHA：d48e1b8931bcb78299df4d53ffe95ab5cfc01f60f058ccda16efde8c7b16c76e；repeat：d48e1b8931bcb78299df4d53ffe95ab5cfc01f60f058ccda16efde8c7b16c76e。未宣稱OS page cache已清空。
完整證據：end_to_end_test_results.json、replay_comparison.json、determinism.json及adapter_gate/。

## 6. 測試與量測
**Regression 92/92 PASS**：原63項＋新29項，0failure/error/skip；**CTest1/1 PASS**，含7項精確算術assertions。
也驗證所有已發布session_manifest的journal SHA/大小與實際檔案一致，Snapshot與binary/config/policy引用正確。
大量人工事件20000：
- Capture Adapter wall：1.154889s；Replay：0.615840s。
- Adapter/Replay process peak RSS：32052 / 32052 KiB；queue最多1筆／77 bytes；Replay pending最多1000。
- Capture logical disk：32478859 bytes；allocated：32501760 bytes（包含job Manifest）。
- 20000 Book、19000 FLAT有效Label、1000tail逐列通過人工固定價格Oracle。
- 每5000筆輸出processed/total/%/stage/errors/gaps/elapsed/queue/disk與可估ETA；不可可靠估計時標NOT_AVAILABLE。
RSS是getrusage high-water，不是每個容器的精確allocator量測；這是人工吞吐測試，不是HFT延遲benchmark。
原Python B只在小fixtures執行，大流採C++ deque匹配＋獨立常數價格Oracle，避免沿用B的大量二次搜尋。

## 7. 安全與完整性
共22261既有檔案/連結metadata一致，含ML venv 6838、QML venv 9352、歷史artifacts 6021、docs 50。
核對mode/size/mtime_ns/inode/device；父目錄允許新增子路徑造成mtime變化。
Dataset/Frozen/venv本輪未修改；這是metadata完整性，**沒有重新hash其內容**，不能排除同size/mtime的外部惡意改寫。
3個明列非市場封存錨點SHA一致；沒有使用舊opaque清單授權內容存取。
Python Supervisor、Adapter及Replay使用PHASE4B2E_OFFLINE_V1/root綁定、舊inode deny；Test/alias/symlink/..及overwrite測試通過。
TMPDIR/TEMP/TMP在程序前設定同一私有0700路徑，pycache停用，UNIT_WRITE_SCOPE維持。
真實Test open=0／未評估；Final Holdout未開啟、LOCKED；未訓練模型、計算市場Quantum Kernel、使用QPU、交易/回測/模型選參。
歷史TEST_OPENED_FOR_OPAQUE_HASH_WITHOUT_PHASE_APPROVAL、60次opaque open及F39 FAIL永久保留。舊Test確認性資格需研究負責人裁定。
有GitHub官方文件/commit與web文件查核的網路活動；沒有Binance WebSocket/REST、行情下載或交易網路。沒有套件安裝。
防護是應用層，沒有OS全機syscall監控/跨帳戶隔離證據，仍有FD繼承、同帳戶惡意程式、TOCTOU及policy替換風險；不宣稱普遍無洩漏。

## 8. F43與正式啟動條件
f43_approval_requirements.json明列Data Owner、Custodian、Capture Operator、Storage、Quota、Retention、新日期Dataset/Confirmation分離、一次性解封批准、Protocol SHA與操作存取紀錄。
所有未授權具名角色與Live儲存/預算/保留/保管安排保持APPROVAL_REQUIRED。沒有教授簽名或批准單。
舊Test/Final Holdout不得代替新日期Confirmation。
readiness_checklist.json：ENGINEERING_READY（OFFLINE_SYNTHETIC_CAPTURE_ONLY），APPROVAL_PENDING，NOT_AUTHORIZED_THIS_PHASE。
正式前尚需F03決策、F43保管安排、正式容量/備份/保留、真實Transport與ping/pong/rate-weight/HTTP Retry-After/timeout、真實UUID/receive clock、OS帳戶隔離/撤權/硬體故障驗收，以及新的明確Live授權。
建議下一步先送審上述決策與Transport驗收方案；目前不建議直接批准市場擷取。

## 9. 開發失敗與停止
development/phase4b2e/20261031T113819Z保留部分寫入後Manifest契約失敗及完整trace；修復I/O失效不能seal、原子發布。
114851保留正常輪替fixture超過10次connection上限的失敗；修正人工fixture20筆／9次輪替，未提高上限，超限負測仍在。
115000通過90項，115345通過91項，115540最終92項。命令過長/準備腳本SyntaxError都在程序開始前失敗，setup/history保留記錄，無市場資料操作。
未刪除assertions、未將舊FAIL改PASS。所有新正式輸出採唯一run與exclusive建立。
本輪完成後停止，不自動連線或執行下一階段。
