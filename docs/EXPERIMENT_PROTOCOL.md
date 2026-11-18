# Experiment Protocol

狀態：PROPOSAL_ONLY／NOT_EXECUTED。本次只鎖定候選比較架構與最低紀錄要求。尚未建立模型、量子電路、kernel matrix、QUBO、QAOA、回測或 Paper Trading；所有實驗結果 NOT_AVAILABLE。任何實驗要在前階段驗收與人工批准後執行。

## 比較架構

| 階段 | 候選方法 | 公平比較要求 |
| --- | --- | --- |
| Phase 3 | 固定 OBI ±0.6 規則 | 正側／負側／中立區規則預先固定；建倉、平倉、持有、成本另明定，不把閾值直接當成完整交易策略 |
| Phase 3 | Logistic Regression | 同資料、特徵、label、時間 splits、scaler 與搜尋預算 |
| Phase 3 | Linear SVM | 同上；搜尋空間與選擇依據事前記錄 |
| Phase 3 | RBF-SVM | 同上；與 kernel 方法比較時記錄 pairwise 計算及記憶體成本 |
| Phase 4 | Fixed Fidelity Quantum Kernel | feature encoding、qubits、depth、shots、seed、backend 與測量政策待明確批准；不得預設優勢 |
| Phase 4 | Trainable Quantum Kernel | 參數訓練只用 Training；kernel learning／搜尋成本完整計入 |
| Phase 4 | QSVC | 明確指定搭配哪種 kernel；不將 QSVC 與其 kernel 視作獨立不相干證據 |
| Phase 5 | Classical exact QUBO solver | 小型相同 QUBO instance 的精確目標值與可行性參考；規模限制明列 |
| Phase 5 | QAOA | 與 exact solver 同 objective／constraints／instances；記錄 shots、depth、seed、iteration、總成本 |

以上是候選清單，沒有套件、程式或結果。分類預測與決策最佳化分開驗收；QAOA 不直接與分類器以同一分類分數排名。

## 資料、標籤與切分

遵守 [Phase 2 計畫](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)。100／200／500／1000ms 標籤保存 actual horizon、match error 與有效性。不同 horizon 的有效樣本集合不同時，主比較使用同一明確交集，另報 coverage，不能靠排除困難樣本美化結果。

max_match_error_ms=null；gap 閾值、return classification 門檻及訓練區間只在 Training profile 與研究 protocol 中決定並經人工審核後凍結。原始 epoch 為 metadata；local_timestamp_us 不作模型特徵或延遲。Validation 用於事先定義的模型選擇，Final Holdout 全程封存直到唯一最終評估。

Train／Validation／Test 按時間排序，不 shuffle；Scaler 僅 Training fit。以實際 label future endpoint purge split 重疊，記錄 feature lookback。時間相關樣本的統計推論方法另預註冊，不能將逐筆資料當獨立觀測而不說明。

## 指標與計量邊界

| 指標 | 定義／必要紀錄 |
| --- | --- |
| Balanced Accuracy | 各類 recall 平均；類別定義、樣本數、缺類情況明列 |
| Macro-F1 | 各類 F1 平均；零分母政策與 support 明列 |
| Precision／Recall | 逐類報告並附混淆矩陣；不能只報單一平均掩蓋少數類 |
| 成本後報酬 | 明定 fee、spread、slippage、交易時點、持倉與資本尺度；不得假設無限可成交 |
| 最大回撤 | 依成本後 equity curve；取樣時間與定義固定 |
| 交易次數 | 定義 order、fill、round trip 或持倉變化；不能混用 |
| 推論時間 | 實測本機 pipeline／model 邊界，warmup、batch、hardware、分位數；不能由舊 CSV local−event 推得 |
| 訓練時間 | 含 scaler、特徵選擇、kernel 計算與調參者需清楚拆分及總計 |
| Qubit 數 | 邏輯 qubits、實際 backend 規模與 ancillary 分開 |
| 電路深度 | 編譯前後、gate set、connectivity 及 transpilation 設定 |
| QAOA 可行率 | 所有測得候選中符合原始 constraints 的比例；constraint／penalty 固定 |
| QAOA 目標值差距 | 與同 instance exact optimum 比較 absolute gap；相對 gap 分母為零時明列不適用 |

費用、滑價、延遲與 fill 假設不能由現有來源憑空推定。Phase 3 統一回測須先定義再使用；Testnet ACK 不等於 fill，CSV local 時間不是網路延遲證據。當階段不適用指標標 NOT_APPLICABLE；未量測標 NOT_AVAILABLE，均不可填 0。

## 可重現性、資源及報告

每次保存唯一 run_id、原始資料與資料集 SHA-256、程式版本／SHA、環境、所有參數、random seeds、split 時間及 hash、訓練／驗證／測試樣本數、invalid/purge 數量、完整命令／stdout／stderr／exit code、搜尋空間及總試驗數。

量子方法另保存 encoding、kernel PSD／數值處理規則、shots、noise/backend、qubits、depth、最佳化預算；小型 pilot 的樣本及 kernel matrix 大小須先核准，避免無上限 O(n²) 記憶體。CPU affinity 不等於 isolation，模擬器時間不等於量子硬體時間。不得只挑最好的 seed 報告。

Phase 6 自動搜尋及重新訓練須保留 champion/challenger、退化判準、模型版本與人工批准紀錄。Codex 不得批准自己的模型，不可自動更新啟用中的模擬策略。

## 驗收與停止

Phase 2 只驗收資料與 lineage；Phase 3 再建立經典基線與成本回測；Phase 4、5 才研究量子方法；Phase 6、7 各有獨立人工 gate。本次不得執行任何上述實驗，完成交接後停止。
