# Phase 4B-1 Engineering Recovery-2

**PHASE 4B-1 ENGINEERING RECOVERY-2 PASS**。run_id：20261030T071508Z；UTC：2026-10-30T07:31:22.146045+00:00

本次通過工程修復、人工回歸及既有結果可支持範圍的獨立稽核，不是重新執行正式量子實驗。歷史20261030T062158Z永久保持HISTORICAL_ENGINEERING_FAIL，上一輪20261030T065154Z永久保持RECOVERY BLOCKED。數值驗證不追認舊工程PASS。

## 授權、隔離與執行順序

工作目錄/home/jason/quantum-hft；指定Python=/home/jason/.venvs/quantum-hft-qml/bin/python。先唯讀檢查舊218正式artifacts與82個BLOCKED檔案、報告、manifest與Dataset/Frozen/venv，通過後才建立新UTC run。新run/tmp owner UID1000、0700、非symlink；TMPDIR/TEMP/TMP在每個新Python程序前設定，-I -B與PYTHONDONTWRITEBYTECODE=1；首次tempfile cache None。沒有啟用/tmp或/dev通用白名單，精確dill /dev/null例外未變。
順序：preflight_integrity→原128人工tests→修復52及新增16tests→獨立歷史結果audit→final_integrity→本報告與命令收據→completion。每份輸出exclusive-create，不覆寫舊檔。若必要Gate失敗則寫failure_manifest，不產生假completion；本輪所有必要安全與測試Gate實際通過，未建立failure_manifest。

## 五個ERROR的完整traceback與精確修復

已閱讀上一輪logs/new_tests.stderr.txt的全部5項traceback，均為TEMP_EXCLUSIVE_CREATE_REQUIRED：4項合法fixture初始化採write_text(w/O_TRUNC)，未帶O_EXCL；另1項缺檔fingerprint直接open(rb)，先被scope拒絕而非預期FileNotFoundError。
四項初始化只改用create_fixture→檔案事先不存在＋Path.open(x)。corruption測試之後刻意改寫本程序擁有的private fixture仍保留write_text與原hash不符assertion，沒有將非法覆寫負例變成合法操作，也沒有mock安全寫入。
fingerprint先驗證路徑位於本Recovery授權root且無symlink/..，再lstat：合法缺檔為FileNotFoundError；禁止路徑為ArtifactAccessDenied(PermissionError)。直接未建立temp路徑的raw open仍會被原scope拒絕，已有新增test確認，沒有將所有例外統一或放寬scope。
修復後原52項unittest assertions的AST與原檔逐一相同；diff封存於verification。沒有改動市場模型邏輯、超參數、Feature Map、Fold或dataset。

## Regression、輸出契約與Trace

|組別|探索並執行|PASS|failure/error/import-error/skip|
|---|---:|---:|---|
|原安全與回歸|128|128|0/0/0/0|
|原52項工程tests|52|52|0/0/0/0|
|新增缺檔／初始化／Trace契約|16|16|0/0/0/0|
|總計|196|196|0/0/0/0|

新harness failfast=True；完整case IDs與source SHA在test_list_manifest/new_test_list_manifest，每項outcome與stdout/stderr均封存。無Git commit可用，未捏造版本。
preflight_integrity.json與final_integrity.json已在本run依序各建立一次，路徑分離；17項原輸出契約及新增Recovery2狀態測試通過。重複create、舊artifact覆寫、缺驗收/必要檔案、提前completion、保留欄位注入、中斷後假PASS均拒絕。
人工import ERROR、fixture ERROR與中斷的完整Traceback經真實private檔案排他寫入及讀回驗證，測試後依tmp生命週期清理。真實Gate沒有import/fixture ERROR。stdout/stderr完整保留；監控所有既成operations與events一律在finally封存，不再依賴整組tests先PASS。trace同名寫入拒絕且不遞迴記錄寫入失敗。
人工prediction_call_trace包含main24高層／48底層及其他正負測試monitor，全部保留；每個operation都有全run唯一ID、run/model/fold/first-repeat、parent、level、status與monotonic事件。失敗負例清楚標示人工資料，未刪除多餘事件以湊計數。

## 歷史48／24監控：可證明與不可證明

實際人工SVC與QSVC驗證呼叫鏈：外部predict_once高層→BaseSVC.predict→BaseLibSVM.predict。原profiler對兩個Python predict entry各記一次，所以1個外部預測可產生2筆低層事件；不是要求1:1。真正人工雙predict可見4筆，zero-low-call baseline亦允許。
原formal trace有48筆predict entry，fit紀錄與鎖定程式／輸出可支持24個solver作業：first12、repeat12，涵蓋三fold×四solver；Majority無SVC呼叫。原監控postcondition把raw entry預期成24與此巢狀機制不符。
**HISTORICAL_TRACE_INCOMPLETE**：原48事件沒有operation ID、qualified function、fold/model/pass/timestamps/parent，無法逐筆確證48→24映射。報告保存原48事件與24個fit紀錄，不靠索引配對補造歷史鏈；本輪新人工trace絕不冒充舊trace。
封存predictions bytes未修改，獨立metrics一致；沒有發現額外市場預測的證據。但未重新跑無profiler的市場模型，不能宣稱觀測器對正式模型絕對零因果影響。
歷史Timing與stage execution/完整成本逐筆對應通過，兩政策整體成本只計一次共享Kernel。原measurements包含當時active profiler；raw48事件無duration，無法量化或扣除overhead。個別模型內共享Kernel attribution不能相加兩次；沒有以solver時間宣稱加速。
這項可支持範圍的監控audit已完成；缺失歷史trace明列為限制，依本輪Stage9不阻擋Engineering Recovery驗收，也不使舊FAIL轉PASS。

## 獨立Metrics稽核

**ARCHIVED_METRICS_VERIFIED**：首次15組、repeat15組，逐筆共11520列。只讀歷史run的完整labels/predictions，用純Python confusion counts/Fraction實作，不呼叫原scorer或sklearn metrics。
固定labels[0,1,2]、DOWN/FLAT/UP、zero_division=0；Macro固定三類。BA平均present true classes recall，本次每fold皆有三類。IDs/順序、true label int64 SHA與跨模型一致性、predicted labels、3×3CM、Macro-F1/BA/Accuracy/Macro Precision/Macro Recall、各類P/R/F1/support、預測分布、類別覆蓋與CSV均核對。絕對容許1e-12，最大Macro純量差=5.551115123125783e-17。
首次與repeat逐筆predictions、CM、所有指標一致。三fold cross-summary mean/median/sample std(ddof1)/worst及QSVC−RBF差距由獨立數值重新計算後一致。原per_class_metrics.csv/class_metrics.csv各45列、fold_comparison.csv15列亦核對。
此驗證是對封存labels的獨立評分核對，不是重新從市場價格建label或對外部市場ground truth驗證。未解析Test或Final Holdout。

|Fold|模型|Macro-F1|BA|Accuracy|DOWN recall|FLAT recall|UP recall|
|---|---|---:|---:|---:|---:|---:|---:|
|F1|RBF_None|0.264783|0.333333|0.658854|0.000000|1.000000|0.000000|
|F1|RBF_Balanced|0.381534|0.382489|0.536458|0.156250|0.667984|0.323232|
|F1|QSVC_None|0.250655|0.274777|0.539062|0.000000|0.814229|0.010101|
|F1|QSVC_Balanced|0.263272|0.298245|0.549479|0.062500|0.822134|0.010101|
|F1|Majority_FLAT|0.264783|0.333333|0.658854|0.000000|1.000000|0.000000|
|F2|RBF_None|0.306610|0.333333|0.851562|0.000000|1.000000|0.000000|
|F2|RBF_Balanced|0.435262|0.666581|0.531250|0.714286|0.492355|0.793103|
|F2|QSVC_None|0.408623|0.435425|0.705729|0.178571|0.782875|0.344828|
|F2|QSVC_Balanced|0.408623|0.435425|0.705729|0.178571|0.782875|0.344828|
|F2|Majority_FLAT|0.306610|0.333333|0.851562|0.000000|1.000000|0.000000|
|F3|RBF_None|0.324220|0.346711|0.757812|0.076923|0.963211|0.000000|
|F3|RBF_Balanced|0.298198|0.492939|0.283854|0.794872|0.183946|0.500000|
|F3|QSVC_None|0.300971|0.322185|0.648438|0.153846|0.812709|0.000000|
|F3|QSVC_Balanced|0.300971|0.322185|0.648438|0.153846|0.812709|0.000000|
|F3|Majority_FLAT|0.291850|0.333333|0.778646|0.000000|1.000000|0.000000|

完整30組CM、per-class與prediction distribution、逐檔SHA及獨立cross-summary均在independent_metrics_audit.json，沒有補造或重新predict。

## Kernel、Preprocessing與Determinism範圍

218檔完整集合、大小與SHA通過；1440個Frozen IDs唯一且順序一致，Train最大actual label endpoint<boundary。saved Train/Validation角度形狀、feature order、範圍、參數SHA、Train96 fit註記與first/repeat一致。各fold4份saved Quantum/RBF矩陣file/array SHA、形狀、有限值與Train symmetry/diag/PSD獨立數值核對；無矩陣修補。
這些是已保存陣列的讀取與線性代數驗證，沒有Statevector/Quantum Kernel evaluate、沒有preprocessing fit、沒有正式模型fit/predict。原repeat重用已驗SHA的Kernel，因此Determinism證據不等於重算量子電路的獨立重現。raw market features沒有重新解析，其完整性沿用不變Dataset/Frozen SHA。

## 研究限制與已核對的歷史結果

RBF balanced三fold mean Macro-F1=0.371665、BA=0.514003；QSVC balanced mean Macro-F1=0.324289、BA=0.351952。這些分數現在是已獨立核對的封存觀察值，沒有重訓。
balanced QSVC的BA三Fold均低於RBF；QSVC UP recall不穩定，F3為0。F3 Train UP只有1筆；F1 Validation相鄰實際label區間重疊383對。全部UTC2026-08-26，SAME_DAY_ONLY；三source aliases不等於三獨立市場，PHYSICAL_CAPTURE_SESSION_UNKNOWN；9203筆因額外endpoint witness規則不入候選，存在選擇偏差。
不使用IID顯著性或因子因果主張，不以最高分選交易模型；量子優勢、Quantum Speedup、真實QPU效能、跨日泛化、交易延遲與長期獲利均未建立。Test/Final Holdout未用來選參或評估。

## 完整性、安全、驗收與後續

final_integrity再次核對3919個受保護檔、全部Dataset/Frozen/Budget、舊FAIL/BLOCKED/report/manifest/traceback、7個舊symlink metadata、ML7610與QML10505 entries，均PASS。32個Holdout檔只stat與歷史SHA，不讀內容或重算bytes hash。Test僅opaque checksum。
正式模型fit0、predict0、preprocessing fit0、正式市場Quantum evaluate0；人工fixtures的訓練/量子API測試另存fixture_call_profile與new_fixture_calls。沒有QPU、網路、套件升級、Binance、QUBO/QAOA、交易、Testnet、回測或Paper Trading，未進Phase4B2，也沒有重新執行三Fold正式實驗。
經核准的全部工程條件成立；歷史trace缺失不隱藏，Metrics驗證與工程PASS範圍分開。source SHA、命令stdout/stderr、實際exit code與report SHA由completion_manifest封存。
下一步先人工審核。本次修復可供另行批准的新run進行相同protocol的端到端正式工程驗收，取得新的完整operation trace；不能用新trace追補舊48事件。若只需使用已核對的歷史數值，無需為分數重跑，更不應改參數。後續研究仍應先預註冊跨日且來源較可核實的資料設計，不使用既有Test/Holdout選參。已停止，等待人工審核。
