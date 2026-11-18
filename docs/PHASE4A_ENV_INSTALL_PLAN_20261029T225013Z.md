# Phase 4A-ENV 安裝批准計畫

狀態：等待明確批准建立新venv與安裝。Python3.14／PyPI dry-run已批准；此計畫不代表runtime相容性PASS。

Python：/usr/bin/python3.14，3.14.4；未找到Python3.13。目標：/home/jason/.venvs/quantum-hft-qml，目前不存在。

## 精確套件版本

|套件|版本|
|---|---|
|cloudpickle|3.1.2|
|dill|0.4.1|
|joblib|1.6.0|
|narwhals|2.28.0|
|numpy|2.5.4|
|qiskit|2.6.1|
|qiskit-machine-learning|0.9.1|
|rustworkx|0.18.1|
|scikit-learn|1.9.1|
|scipy|1.18.1|
|setuptools|84.2.1|
|stevedore|5.9.1|
|threadpoolctl|3.7.0|
|typing-extensions|4.16.0|

全部14個wheel URL及SHA-256見plan/environment_install_plan.json；requirements.lock固定全部版本與下載hash。pip bootstrap25.1.1使用本機ensurepip，不另外upgrade。

## 預定命令

建立前再次確認目標不存在，任何非空環境均停止，不刪除或覆寫。

```bash
/usr/bin/python3.14 -I -B -m venv --copies /home/jason/.venvs/quantum-hft-qml
/home/jason/.venvs/quantum-hft-qml/bin/python -I -B -m pip --disable-pip-version-check --no-cache-dir install --require-hashes --only-binary=:all: --index-url https://pypi.org/simple --retries 1 --timeout 30 --report /home/jason/quantum-hft/artifacts/phase4a_env/20261029T225013Z/install_report.json -r /home/jason/quantum-hft/artifacts/phase4a_env/20261029T225013Z/plan/requirements.lock
```

實際子程序會清除PIP_*自訂索引設定並設PIP_CONFIG_FILE=/dev/null、停用pip cache，暫存只寫本run。安裝需要再次連線官方PyPI/files.pythonhosted.org下載已鎖定wheel；不接IBM QPU、Binance或Testnet。

## 保護與驗證

舊ML venv完整7610個entry baseline已保存；不安裝至系統或舊venv。Python3.14.4僅因本次明確批准才採用，不能從Requires-Python推論完整相容。

安裝後執行pip check、imports、4-qubit ZZ reps1 linear、Statevector、6x6人工Kernel及人工三分類QSVC fit/predict。任何必要失敗BLOCKED，不自行更換版本或升級；不進Phase4A-1。

本輪不開啟Holdout CSV，只沿用先前封存SHA及本輪stat metadata；不聲稱重新hash Holdout內容。其餘受保護檔案與Frozen使用fresh SHA256。沒有正式市場模型輸入。

PyPI dry-run已實際下載metadata與wheel，來源和stdout/stderr已封存；不得宣稱本任務完全沒有網路。
