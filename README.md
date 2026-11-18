# 訂單簿價格方向預測與持倉選擇：量子核與 QAOA 評估

**Order Book Price Direction Prediction and Position Selection: An Evaluation of Quantum Kernels and QAOA**

> 量子金融競賽研究專案｜BTCUSDT 歷史訂單簿｜離線研究與模擬原型（不進行真實交易）

## 研究簡介

本研究探討以訂單簿微結構特徵預測短期價格方向，並評估量子核分類器與量子近似最佳化演算法（QAOA）的可行性。預測研究使用量子核支援向量分類器（QSVC）及傳統 RBF-SVM 作為對照；持倉選擇研究另以小型 QUBO／QAOA 原型驗證最佳化計算。**預測與最佳化目前屬分開研究的模組，尚不宣稱已構成完整可交易的端到端系統。**

### 研究流程

```text
歷史 BTCUSDT 訂單簿資料
          |
          v
訂單簿重建、來源與時間檢查
          |
          v
特徵：OBI(5)、spread(bps)、bid/ask volume(5)
          |
          v
1000 ms 價格方向標籤：DOWN / FLAT / UP
          |
          v
時間切分、purge、Train-only preprocessing
          |
          +-------------------------+
          |                         |
       RBF-SVM                  Quantum Kernel + QSVC
          |                         |
          +-----------+-------------+
                      |
          分類指標／成本／穩定性比較

另行研究：小型 QUBO 問題 → exact solver 對照 → QAOA 原型
```

## 已完成的研究工作與證據

| 模組 | 目前有證據支持的內容 | 原始資料或程式 |
| --- | --- | --- |
| 資料處理 | CSV / replay adapter、訂單簿重建、特徵與標籤、時間切分及驗證程式 | [data_pipeline](data_pipeline/) · [tests](tests/) |
| 經典基準 | RBF-SVM、其他經典基準及評分工具 | [experiments/kernel_comparison](experiments/kernel_comparison/) · [experiments/classical](experiments/classical/) |
| 量子核分類 | 4-qubit ZZ feature map、FidelityStatevectorKernel、QSVC / RBF 比較原型 | [Phase 4A-1 報告](docs/PHASE4A1_REPORT_20261029T232311Z.md) · [實作](experiments/phase4a1/) |
| 權重消融 | 固定樣本上的 class_weight=None / balanced 受控比較，Phase 4A-4 Recovery PASS | [Phase 4A-4 報告](docs/PHASE4A4_REPORT_20261030T012252Z.md) |
| 時間驗證設計 | 三個預先封存的時間窗口、資料洩漏稽核；Phase 4B-0 PASS（**僅代表研究準備與規格驗收**） | [Phase 4B-0 報告](docs/PHASE4B0_REPORT_20261030T020400Z.md) |
| 三時間窗模型實驗 | 三窗五候選模型的首次與重複計算已產生結果；該次 Phase 4B-1 **工程驗收 FAIL**，不可視作正式 PASS | [Phase 4B-1 原始報告與失敗原因](docs/PHASE4B1_REPORT_20261030T062158Z.md) |
| QAOA 最佳化 | 小型 QUBO、Ising、statevector QAOA 與 exact enumeration 對照的開發原型；不是市場實盤或端到端策略績效 | [QAOA 原型](development/phase5/phase5_dev_v2_20261031T183635164716Z/qaoa_v2.py) · [驗證程式](development/phase5/phase5_dev_v2_20261031T183635164716Z/verify.py) |

**注意：** 文件中標示的「PASS」為各階段特定工程／稽核項目的驗收，不表示市場預測有效、模型泛化成功或具有量子優勢。原有 FAIL 記錄保留，不回溯改寫。

## 選定實驗結果（含限制）

### Phase 4A-1：固定 Prototype Validation（96 筆）

| 模型 | Macro-F1 | Balanced Accuracy | Accuracy |
| --- | ---: | ---: | ---: |
| RBF-SVM (balanced) | 0.2884 | 0.6853 | 0.3229 |
| QSVC (balanced) | 0.1287 | 0.3209 | 0.1875 |

來源：[Phase 4A-1 正式報告](docs/PHASE4A1_REPORT_20261029T232311Z.md)。本原型比較中 RBF-SVM 表現較好；結果僅適用於該固定樣本及已宣告設定，不代表跨市場或獨立日期的泛化結論。

### Phase 4B-1：三時間窗探索性觀察（每窗 Validation 384 筆）

下表為已封存的 **Macro-F1**；本次工程驗收 **FAIL**，原因是完整性輸出檔案名稱衝突，並非把實驗提升為正式通過的證據。

| 模型 | Fold 1 | Fold 2 | Fold 3 |
| --- | ---: | ---: | ---: |
| RBF-SVM / None | 0.2648 | 0.3066 | 0.3242 |
| RBF-SVM / balanced | 0.3815 | 0.4353 | 0.2982 |
| QSVC / None | 0.2507 | 0.4086 | 0.3010 |
| QSVC / balanced | 0.2633 | 0.4086 | 0.3010 |

對照另含 Majority-FLAT。三窗均來自**同一市場日期的來源資料**，不等於三個獨立交易日；稀有方向類別支持度低，部分模型出現單類預測或 UP recall=0。完整配置、混淆矩陣、重複計算與成本資訊請以 [Phase 4B-1 報告](docs/PHASE4B1_REPORT_20261030T062158Z.md) 為準。**現有證據不足以宣稱 QSVC 優於 RBF-SVM 或產生量子加速。**

## 評審快速導覽

- [研究方法與固定實驗規格](docs/PHASE4B0_REPORT_20261030T020400Z.md)
- [QSVC 與 RBF-SVM 原型比較](docs/PHASE4A1_REPORT_20261029T232311Z.md)
- [權重消融與限制](docs/PHASE4A4_REPORT_20261030T012252Z.md)
- [三時間窗模型結果與工程 FAIL 說明](docs/PHASE4B1_REPORT_20261030T062158Z.md)
- [訂單簿與特徵處理程式](data_pipeline/)
- [量子／經典比較程式](experiments/)
- [QAOA 開發原型](development/phase5/phase5_dev_v2_20261031T183635164716Z/)
- [自動化測試](tests/)

## 可重現性與資料範圍

研究程式主要使用 Python；量子比較紀錄的環境包括 Python 3.14.4、Qiskit 2.6.1、Qiskit Machine Learning 0.9.1，詳見各 Phase 報告。不同實驗有不同樣本、時間窗口、權重政策與硬體／計時邊界，**不可將其分數當成同一個完整的獨立測試**。

大型原始資料、模型中間產物、run logs、憑證與執行環境未包含在此公開儲存庫。因此這是一份可供審查的**程式與研究紀錄**，並非已保證一鍵執行的完整資料封裝；重現特定結果前須依相應報告取得合法資料與一致環境。

## 研究限制與後續方向

1. 評估資料具有時間相關性、FLAT 類別占比高與少數類別支持不足等限制。
2. Quantum Kernel 的實驗採本機 **statevector simulation**；並未據此證明量子硬體優勢。
3. QAOA 僅展示小型最佳化問題的研究原型，尚未證實與真實訂單簿預測完整串接，也沒有真實交易績效。
4. 不使用實際下單；交易成本、滑價、成交限制與最終風險評估須另行嚴謹驗證。
5. 目前有些歷史報告含原本機絕對路徑，僅能作為實驗紀錄；GitHub 導覽請以本 README 的相對連結為主。

---

**Project status:** Research prototype and documented experiments. No demonstrated quantum advantage, no live trading, and no claim of a complete production-ready trading platform.
