# Phase 4B-1 Engineering Recovery：BLOCKED

**RECOVERY BLOCKED**。run_id：20261030T065154Z。UTC：2026-10-30T07:02:03.366296+00:00

本輪僅執行工程修復與人工fixtures，未進行新的正式模型訓練、正式預測或正式Quantum Kernel。原FAIL20261030T062158Z仍為HISTORICAL_ENGINEERING_FAIL，218個artifacts與報告完整未改。必要人工回歸有5項ERROR，已停止後續獨立研究結果稽核；沒有同run修補／重跑。completion_manifest.json依規格不建立，原failure_manifest.json保留。最終failure_evidence_manifest.json只封存BLOCKED證據，不代表PASS。

## 保護範圍與執行前核對

工作目錄/home/jason/quantum-hft與realpath完全相符，Linux ext4。Python=/home/jason/.venvs/quantum-hft-qml/bin/python。開始前先以唯讀hook核對舊completion SHA bfb822c89665b16abf8e042bdf9e5ce93e095607217f26f1192cd907ee457f06、218檔逐一SHA/size、原report、鎖定來源、3615先前受保護檔、Frozen/Budget/Dataset與ML/QML venv，再建立新run。新baseline合計3835檔與5個舊symlink。沒有寫入HFT專案、Dataset、Frozen或兩venv。
新run/tmp：owner UID1000、0700、非symlink；TMPDIR/TEMP/TMP在新Python程序前設定，PYTHONDONTWRITEBYTECODE=1與-I -B；fresh tempfile cache None且gettempdir正確。沿用PrivateTmpScope的精確dill /dev/null例外與不可覆寫限制，未擴大/tmp、/dev。兩個人工escape symlink作證據保留，未跟隨寫入。

## 輸出衝突修復契約與測試

原衝突：唯讀Gate先建立final_integrity.json；runner最終以exclusive-create再次建立同檔，安全機制拒絕覆寫。新RunOutputs明確分離preflight_integrity.json與final_integrity.json，completion只在完整Gate/必要報告之後建立，失敗使用獨立failure_manifest.json。禁止覆寫未關閉；17項輸出契約人工測試全部通過，涵蓋正常產生、分離、重複拒絕、舊artifact保護、中斷無假PASS、缺Gate/必要檔案與保留欄位注入拒絕。這些是人工子目錄fixtures，不是本Recovery的提前PASS。
本run只建立preflight_integrity.json；未建立final_integrity.json或completion_manifest.json。blocked_integrity.json記錄失敗後的安全完整性重驗，不替代正式驗收。

## 測試結果與新阻擋點

|測試組|執行|PASS|FAIL|ERROR|SKIP|
|---|---:|---:|---:|---:|---:|
|原安全與回歸|128|128|0|0|0|
|新工程回歸|52|47|0|5|0|
|合計|180|175|0|5|0|

完整case IDs/source SHA見test_list_manifest.json、new_test_list_manifest.json；每項結果及完整traceback見new_regression_results.json、logs/new_tests.stderr.txt。沒有刪除或放寬assertion，沒有skip。
5項ERROR：
- engineering_tests.ArtifactIntegrityTests.test_duplicate_prediction_ID_rejected
- engineering_tests.ArtifactIntegrityTests.test_file_corruption_detected
- engineering_tests.ArtifactIntegrityTests.test_file_hash_and_size_verified
- engineering_tests.ArtifactIntegrityTests.test_missing_artifact_detected
- engineering_tests.IndependentMetricsTests.test_prediction_ID_order_and_labels

其中4項人工fixture用Path.write_text()首次建立檔案，該API使用w/O_CREAT/O_TRUNC，缺少O_EXCL，遭TEMP_EXCLUSIVE_CREATE_REQUIRED拒絕。另1項缺檔測試預期FileNotFoundError，但在未建立的私有暫存路徑上直接open(rb)，scope先拒絕讀取，收到ScopeViolation。這些是本次fixture/缺檔例外契約與已批准scope不一致，不能藉放寬scope取得PASS。
unittest批次未設定failfast，52項在2.6秒內全部結束後由Gate封存BLOCKED；完整紀錄保留。此後未啟動Stage4正式結果獨立指標稽核，也未重跑測試或修改既有修復程式。
執行前靜態檢查曾發現新harness的unraisable清單與callback同名；另存run_new_tests_checked.py後才首次執行。未執行版本亦保留，這不涉及舊artifact覆寫或失敗測試重跑。source與pre_execution_review.json封存。

## Predict監控：已觀察與未完成範圍

11項predict監控人工測試通過，包括實際SVC與QSVC的BaseSVC.predict→BaseLibSVM.predict巢狀呼叫；一個高層預測可有兩個底層事件。人工3Fold×first/repeat×4solver共24個高層作業、48個底層事件的assertion通過，另確認真正兩次predict會保留4個底層事件，不刪事件來湊計數。
新監控器實作唯一operation ID、model/fold/first-repeat、call level、parent、status與事件序列；保留既有profiler並恢復，未修改模型predict行為。人工監控與未監控預測一致的測試通過。
但完整人工trace的寫入位於所有新增測試PASS之後；因5項ERROR而沒有執行，子程序結束後無法補造trace rows。prediction_call_trace.json明確標記NOT_ARCHIVED_REQUIRED_TEST_GATE_FAILED。舊48筆原事件缺乏operation IDs/qualified names/timestamps，本輪不能宣稱逐事件歷史映射已完成。狀態維持PREDICTION_MONITORING_UNRESOLVED；根因機制已在fixtures支持，完整歷史與timing稽核未完成。

## 已封存正式結果稽核狀態

218檔逐一checksum、size與檔案集合再次一致，ARTIFACT INTEGRITY PASS；這不等於重新計算指標。依必要測試失敗即停止規則，本輪沒有解析舊逐筆predictions/labels、重算Macro-F1/BA/Accuracy/per-class/CM、驗證matrix array SHA或preprocessing數值。independent_metrics_audit.json= AUDIT_INCOMPLETE / ARCHIVED_METRICS_UNVERIFIED。
原Determinism PASS仍只代表舊run首次與repeat的封存結果一致；repeat未重算Quantum Kernel。這次沒有新增獨立驗證，因此不能將舊PASS evidence擴張為新模型重現或量子模擬重現。原Metrics/Timing/Predictions bytes沒有修改，但其影響的完整工程稽核尚未完成。

## 研究限制（沿用舊封存結論，非新獨立複核）

原RBF balanced mean Macro-F1/BA=0.371665/0.514003；QSVC balanced=0.324289/0.351952。原觀察：balanced QSVC BA三Fold都低於RBF，UP recall不穩定；F3 Train UP1筆、F1高度重疊labels、同UTC日、實體capture來源數UNKNOWN、9203 endpoint-witness排除。這些資料不能證明量子優勢、量子加速、跨日泛化、統計顯著勝出或可持續獲利。

## 安全完整性、封存與後續

失敗後僅執行安全完整性重驗與報告封存：3835受保護檔、32個Holdout stat、ML7610與QML10505 entries、所有Dataset/Frozen/Budget PASS。Holdout不讀內容不重算bytes hash；只stat與歷史SHA。Test只有opaque完整性checksum，不解析值或評分。
正式模型訓練0、正式Quantum Kernel evaluate0；新52項只使用人工資料，solver fit=28、新Quantum evaluate=0。原128項人工Quantum測試另記fixture_call_profile，不與正式計數混計。沒有QPU、網路、套件安裝、Binance、交易、Testnet、回測或Paper Trading，未進Phase4B2。
建議先另行審核fixture建立方式、缺檔例外契約及failfast/trace在失敗時的保存機制；不可放寬scope或刪測試。本輪不修補重跑，不建議立即重啟正式Phase4B1。只有新的工程Gate完整通過與人工批准後才考慮新正式run；舊FAIL永久保留。已停止，等待人工審核。
