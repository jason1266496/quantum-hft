# Phase 4B-1 Recovery-2：測試環境與唯讀研究 Gate

**PHASE 4B-1 RECOVERY GATE PASS**。run_id：20261030T042531Z。完成時間 UTC：2026-10-30T04:39:58.915767+00:00

本輪只修復測試執行環境、執行人工fixtures及唯讀Gate。這不是PHASE4B-1正式市場實驗PASS；沒有建立新正式實驗run、沒有市場模型fit/predict、沒有正式preprocessing fit、沒有正式Quantum Kernel或模型評分。完成後已停止，仍需另行人工批准才能重啟Phase4B-1。

## 專用暫存目錄與程序啟動

目錄：/home/jason/quantum-hft/artifacts/phase4b1_recovery/20261030T042531Z/tmp。新建、owner UID=1000、權限0700、非symlink，realpath相同，inode/device與建立時相符。TMPDIR/TEMP/TMP由launcher在啟動新Python前全部設為此路徑；PYTHONDONTWRITEBYTECODE=1與-I -B同時使用，實際sys.dont_write_bytecode=True。
執行Python：/home/jason/.venvs/quantum-hft-qml/bin/python；版本：3.14.4 (main, Aug 20 2026, 10:41:58) [GCC 15.2.0]。child PID=3695；首次受保護選路前tempfile.tempdir=None，gettempdir回傳指定私有目錄，沒有靠已選取/tmp的長生命程序重設cache。child_environment.json與實際launcher命令保存了證據。

## 最小權限與操作紀錄

沿用未修改的experiments/phase4b1_recovery/scope.py::WriteScope.null_probe：只允許真正/dev/null、固定dill.get_file_type/line165、buffering=-1、r+b/wb與對應flags，逐次核對device身分。本輪有6次受限例外（4次實際import型別探測、2次原安全測試）；未擴大/dev或任意null直接寫入。
新PrivateTmpScope只在目前run/tmp允許本程序新建且owner/mode/inode相符的暫存檔讀寫與清理。每次路徑正規化、拒絕任何..與symlink，外部cleanup、Dataset/Frozen/venv/舊成果寫入仍拒絕；非tmp artifacts維持exclusive-create。tempfile.NamedTemporaryFile的io.open目錄placeholder只在已核對stdlib呼叫框架允許，真正檔案仍須通過後續exclusive mkstemp audit；直接寫入該目錄的測試也確認遭拒。
OS操作紀錄wrapper均委派真實os.open/read/write/close/unlink/remove/rmdir，不mock安全結果，原audit hook始終啟用。scope_audit.json記錄建立、FD讀寫、清理與經fixture核對的file-object I/O；沒有聲稱能全域攔截所有C file-object方法。測試完成僅停止非權限控制的call profiler，不移除audit hook。
實際追蹤4個暫存檔（初始gettempdir探測與3個人工fixture），4個均清理完成，沒有剩餘regular temp files。25次刻意越界操作全部拒絕，沒有測試案例之外的非預期拒絕或成功未授權寫入。兩個人工escape symlinks保留為證據，其中一個位於tmp；從未跟隨它們寫入，manifest只封存link target。

## 測試清單與結果

|階段|預期|探索|執行|PASS|fail/error/import-error/skip|
|---|---:|---:|---:|---:|---|
|Recovery-2人工安全測試|22|22|22|22|0/0/0/0|
|原Phase4B-1完整相關regression|106|106|106|106|0/0/0/0|

安全22項先通過才執行原106項；全部128個必要案例實際執行，無刪除或放寬assertion、無未批准skip。原106組成為既有Recovery17、Phase4B1科學／契約54與Phase4B0相關35。沒有Git metadata可提供commit，本輪以原封存檔SHA、pre_gate_source_manifest.json及test_list_manifest.json明列每個完整case ID與source SHA，並核對實際探索清單完全相同；沒有宣稱虛構Git版本。
安全測試包含私有目錄選路、真實暫存檔建立讀寫清理、dill/Qiskit/QSVC imports、/tmp與/var/tmp／其他dev拒絕、相對與symlink逃逸、Dataset/Frozen/兩venv及舊artifact寫入拒絕、清理邊界、import-error traceback捕捉。完整逐案結果見summary/safety_tests.json、summary/regression_tests.json；完整輸出見logs/gate.stdout.txt與gate.stderr.txt。
人工import-error fixture在獨立StringIO中確認完整Traceback與ERROR標記，屬預期測試；實際Gate探索沒有import ERROR。現存FAIL/BLOCKED的原始tracebacks亦未修改。套件FutureWarning及人工單類metric警告原樣保留，沒有為消除warning變更既定參數。
人工fixtures實際呼叫solver fit 11次、preprocessing fit 12次、FidelityStatevectorKernel.evaluate 8次，只處理測試程式內建人工數據。這些不是正式市場模型；單元測試程序拒絕開啟正式CSV values，call profile與readonly Gate均證明正式fit/Kernel為0。人工QSVC標準與precomputed路徑等價性、statevector定義、metrics與失敗契約均通過。

## 既有研究規格唯讀核對

Phase4B0 run20261030T020400Z的Window Manifest SHA：18e28f5c6eea162dc8d13e951969785254e3044214d56328546b5d52dcd2b396。6份fold ID manifests與全部freeze SHA一致；1440個selected IDs及market groups全域唯一，順序、source/session/record/update ID與原始Train列位置相同。
唯讀stream正式1000ms Train150,912列，只保留選定metadata及endpoint price witnesses；未使用4個feature值或future_return符號做統計／學習。每筆實際target == event_time + actual_horizon，match_error<=1ms，同source/session future mid-price witness一致。Train實際終點嚴格早於boundary；embargo=0、lookback=0、Validation來源界線與跨fold不重疊均未改。未重新抽樣、改label或fit scaler。
五候選、RBF C100/gamma0.01、QSVC C100、4qubit ZZ/linear/reps1/FidelityStatevectorKernel/shotsNone、固定feature order與exact三類policy均未改。各fold僅Train96 fit的原preprocessing公式只核對文字與SHA，沒有在市場資料執行fit或transform。原三fold96/384及父階段已知類別支援限制仍保留。

## 完整性、安全與舊紀錄

原FAIL20261030T032635Z completion SHA：02d36d85452fd9204e19634a9b26635b3939cd19cd9cd047889362636f8f2e6d；原BLOCKED20261030T040236Z completion SHA：7eab0f6a607bded30b70e06be13f7f947ad4862cb7b5800206aa8e16c57b3953；兩者及報告／manifest／traceback完整未變。
受保護3563個檔案、原保留symlink、Dataset/Frozen/Budget、既有模型成果與ML/QML兩venv均PASS。非Holdout檔重算SHA；Final Holdout32檔只stat並沿用已封存SHA，未讀內容或重算其bytes hash。Test僅opaque checksum，未解析features/labels、選參或評分。
沒有安裝升級套件、網路、IBM QPU、Binance、QUBO/QAOA、Testnet、回測、Paper Trading或真實交易；沒有正式模型、preprocessing、Kernel或研究分數。版本metadata：{"qiskit": "2.6.1", "qiskit-machine-learning": "0.9.1", "numpy": "2.5.4", "scipy": "1.18.1", "scikit-learn": "1.9.1", "dill": "0.4.1"}。

## 驗收與後續

全部16項驗收條件通過。技術上已具備在相同私有tmp啟動環境下重新啟動Phase4B-1的條件；仍須另行人工批准、新正式UTC run及執行前程式／配置／窗口SHA鎖定。本輪沒有使用這項準備結果直接開始市場實驗，也未進入Phase4B-2。
本報告是環境與工程Gate驗收，不是預測能力、跨日泛化、量子優勢或交易獲利證據。已停止，等待人工審核。
