# Phase 4B-2C Closeout Recovery：Test No-Open Gate
狀態：**CLOSEOUT RECOVERY GATE PASS**。新run_id：20261031T102909Z。
只證明本輪受控執行鏈的No-Open修復，不是完整Closeout PASS，也不消除原事故。

## 原事故稽核
事故狀態永久保留 TEST_OPENED_FOR_OPAQUE_HASH_WITHOUT_PHASE_APPROVAL。三個成功worker各回報20個真Test CSV open，共60次、20個distinct封存檔案（包含副本，不代表20個獨立市場Test集合）。
由既有result PID、command/exit、progress stdout、source及sealed manifests建立timeline；沒有逐檔UTC open時間或OS syscall trace。檔案mtime與run_id不是精確open timestamp，均如實標NOT_RECORDED。
受查舊worker用os.open/O_NOFOLLOW→1MiB串流os.read→SHA256，回傳hash/stat/status及PID，不回傳文件原值；progress logs也未見原文。臨時raw byte buffers必然在worker記憶體中，沒有zeroization／memory／swap／page-cache法證，不能斷言不存在所有資訊洩漏或其他未記錄途徑。
未在本次核閱的程式與收據中找到Test解析、訓練、評分或原始內容輸出證據；舊Supervisor同步順序顯示QML/Demo先於protected worker。這不是對所有其他程序或系統活動的保證。舊資料的確認性使用適格性仍由研究負責人/Custodian依規則裁定。

## 權限修復
統一版本 CLOSEOUT_RECOVERY_NO_OPEN_V1，Supervisor/Child/Worker phase identity、policy SHA、worker config SHA與suite SHA都鎖定。Policy version/schema/role/用途錯誤即拒絕；所有manifest records先preflight，Test/Holdout只能protected_stat，舊version1 opaque manifest無法取得內容能力。
原SHA核心的O_NOFOLLOW、前後identity、size/hash mismatch等檢查保留；verify_record第一步require_active並驗phase用途，再處理stat或open。直接file APIs的audithook重複No-Open檢查，metadata check不能提升為content grant。Standalone舊CLI不接受未綁phase的checksum，新註冊worker仍正常工作，沒有停用Integrity或安全護欄。
明確CSV allowlist、symlink/..與已知protected inode別名拒絕、FD wrapper拒絕；所有子程序-I -B -S且close_fds=True，只允許預註冊argv，沒有shell/網路/native任意載入。這是應用層管控，不是OS強制隔離；同帳戶在本phase之外另起舊程式的風險仍揭露。

## 測試與正式Gate
第一開發run 20261031T102446Z 30/30通過；新開發run 20261031T102713Z補強未知CSV、政策版本、FD及無active policy核心，35/35通過。沒有開發測試失敗被刪除或放寬。
13/13跨程序情境通過，含真Supervisor→Child→Policy→Worker→Access Audit→Result，以及缺/空CLI、錯root、重複、symlink/escape、舊manifest、Test file模式、錯phase、未受限checksum模式／舊核心CLI拒絕。人工Test-like與Holdout-like由setup建立，測試沒有使用真實受保護路徑作open探針。
正式run使用相同鎖定程式；35/35 Regression、0failure/error/skip，三角色policy SHA一致。測試以os.open替身確認protected分支0次底層open，並保留真worker拒絕trace及無成功result證據。本輪沒有模型、Kernel或完整Closeout執行。

## 完整性與讀取範圍
本輪true Test CSV content open=0，Final Holdout content open=0。fresh SHA只針對90個舊事故artifact/seal及1個正常人工fixture。既有20393筆Dataset/Frozen/venv等記錄只lstat/size與舊sealed SHA引用；不冒稱fresh內容checksum或完整目錄樹驗證。Metadata一致不能排除保留mtime的修改，也不證明沒有新增檔。
原BLOCKED及F39歷史FAIL維持原樣，90個事故檔案新算SHA與封存一致。本輪Gate PASS不回寫任何原事故、分割或研究結果。

## 研究狀態與停止
歷史Test仍是曾未經當階段批准作opaque hash讀取，沒有改寫TEST_NEVER_OPENED。未發現模型評估證據，但適合未來確認性評估與否需要教授/研究負責人及Custodian決定。Final Holdout維持LOCKED。
沒有市場/QPU連線、模型fit/predict、Quantum Kernel、交易/回測/Paper、QAOA/QUBO、套件安裝或資料集修改。具備提交人工審核、規劃安全重啟Closeout的條件；需另批准新run與明確讀取契約，不能自動重跑。
本輪完成後停止，等待人工審核。
