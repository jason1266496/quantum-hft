# Phase 4A-ENV：獨立 Qiskit 環境建立與相容性驗證

**PHASE 4A-ENV PASS**；run_id：20261029T225013Z

新環境：/home/jason/.venvs/quantum-hft-qml；Python executable：/home/jason/.venvs/quantum-hft-qml/bin/python；Python：3.14.4 (main, Aug 20 2026, 10:41:58) [GCC 15.2.0]
本輪採Python3.14.4，因未找到3.13並已另獲人工批准。先批准PyPI metadata／dry-run，再依精確計畫另獲建立與安裝批准；兩次原始答覆與request ID均封存。
Qiskit2.6.1／Qiskit Machine Learning0.9.1／NumPy2.5.4／SciPy1.18.1／scikit-learn1.9.1。不是僅憑Requires-Python>=3.10推定相容；以下均為新環境實際執行。

## 版本、來源與安裝
使用/usr/bin/python3.14 -m venv --copies建立全新目標，沒有覆寫非空環境。pip25.1.1來自本機ensurepip；14套件依requirements.lock精確版本與wheel SHA256安裝，與dry-run解析及實際install report逐項一致。
套件來源為官方[PyPI](https://pypi.org/project/qiskit-machine-learning/0.9.1/)與files.pythonhosted.org。dry-run已下載metadata與wheel，實際安裝再次下載wheel；本任務明確使用了網路。完整URL、SHA、pip stdout/stderr與exit均封存，停用自訂PIP索引與cache。
沒有安裝qiskit-ibm-runtime、qiskit-optimization、PyTorch或QAOA額外套件；qiskit-algorithms不是本次成功Statevector路徑的必要安裝。

|套件|實際版本|
|---|---|
|cloudpickle|3.1.2|
|dill|0.4.1|
|joblib|1.6.0|
|narwhals|2.28.0|
|numpy|2.5.4|
|pip|25.1.1|
|qiskit|2.6.1|
|qiskit-machine-learning|0.9.1|
|rustworkx|0.18.1|
|scikit-learn|1.9.1|
|scipy|1.18.1|
|setuptools|84.2.1|
|stevedore|5.9.1|
|threadpoolctl|3.7.0|
|typing-extensions|4.16.0|

## pip check 與 imports
pip check：exit0，No broken requirements found。pip_freeze.txt記錄全部15個distribution（含bootstrap pip）。
9/9 imports PASS：qiskit、qiskit_machine_learning、numpy、scipy、sklearn、FidelityStatevectorKernel、FidelityQuantumKernel、QSVC、zz_feature_map。模組路徑均在新QML venv；使用Python -I -B，未混入舊ML venv。
FidelityQuantumKernel只驗證import；實際數值Kernel測試使用FidelityStatevectorKernel，不宣稱所有Quantum primitive／API或QPU路徑皆已測試。

## 人工電路與Statevector
4 qubits、4 input parameters、ZZ feature map、linear entanglement、reps1、alpha2。SDK實測邏輯電路depth11；H4、P7、CX6，共17 gates，未transpile到任何硬體。
Statevector已由綁定人工輸入的電路生成，維度16，有限complex amplitudes；norm squared=0.9999999999999994。

## 人工Kernel數值Smoke
僅6筆人工4維輸入，seed42。6×6 FidelityStatevectorKernel，enforce_psd=False，沒有事後PSD修補。
對稱最大誤差=0.0；對角線偏離1最大誤差=0.0；全部有限實數。
最小eigenvalue=0.6518247784981095，容許誤差1e-10，PSD PASS。矩陣、eigenvalues及人工輸入完整保存；不是正式HFT Quantum Kernel Matrix。

## 人工三分類QSVC
9筆人工Train，每類3筆；另3筆人工evaluation。QSVC fit/predict API成功，classes=[0,1,2]，輸出=[0, 1, 2]。C100、balanced、seed42。
這只是API／數值功能smoke，沒有金融accuracy或獲利宣稱，沒有讀任何市場資料作為模型輸入。沒有模型部署或策略更新。

## 既有資料與環境保護
舊ML venv全部7610個entries（regular files SHA/size/mode、directories與symlink targets）前後完全相同。舊NumPy2.3.5／SciPy1.16.3／sklearn1.9.1沒有升級；系統預設Python沒有修改。
2268個受保護檔案fresh SHA256一致，含HFT66來源／程式與舊正式結果。Phase3B Frozen25項、Phase4A-0 Frozen Budget25項全部fresh SHA256 PASS。
兩份Dataset非Holdout檔案fresh SHA256一致；Holdout受本階段禁止讀取限制，32個既有Holdout CSV只核對size/mtime/inode/device並沿用先前批准的封存SHA，不開啟內容、不宣稱fresh重讀hash。混合模式重建的Dataset tree與封存值一致，限制明列於integrity reports。
Final Holdout維持LOCKED，未使用feature/label、transform、prediction或metric。Phase4A-0歷史DEPENDENCY_BLOCKED結果保持原狀；本輪只建立另一個可執行的QML環境。
沒有QPU、Binance、Testnet、真實交易、回測、Paper Trading、QUBO或QAOA。Smoke程式沒有遠端API呼叫；網路活動只在已批准套件查詢／下載階段，非全機封包監測。

## 結論與停止
此Python3.14.4與鎖定套件組合已通過本輪實際CPU Statevector與QSVC人工smoke；不代表所有API或金融預測能力。既有Phase3B baseline instability仍保留。
環境準備條件滿足；Phase4A-1仍須另行人工批准，本次未進入。所有結果由實際執行輸出產生，沒有虛構量子或交易結果。

## 證據
environment_report.json、dependency_versions.json、dependency_check.json、pip_freeze.txt、qiskit_import_test.json、circuit_smoke_test.json、quantum_kernel_smoke_test.json、qsvc_smoke_test.json、compatibility_report.json、network_activity.json、command_history.txt皆位於本run。
summary/completion_manifest.json封存檔案清單與SHA；summary/qml_venv_manifest.json封存新venv狀態。已停止等待人工審核。
