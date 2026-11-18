# Phase 4A-2：Quantum Kernel 診斷與類別預測分析

**PHASE 4A-2 PASS**；run_id：20261030T000951Z。PASS 僅表示本輪診斷、證據核對與完整性檢查完成，沒有金融預測能力或量子優勢的認證。

工作目錄 /home/jason/quantum-hft；使用 /home/jason/.venvs/quantum-hft-qml/bin/python（Python3.14.4，NumPy2.5.4）。來源為 Phase4A-1 20261029T232311Z 的首輪 Prototype96/96 結果與其 SHA 連結的 Phase4A-0 prototype Train／Validation 原始四特徵及共享角度。沒有回到完整市場表重抽樣。

本輪未 fit／predict 模型，未生成 Statevector 或重新評估量子電路。未保存 RBF Kernel 的部分僅用固定 gamma=0.01 與既有四維角度補算兩個96×96矩陣；不是新增金融模型或大型計算。Formal Quantum Gram 與預測均直接載入已封存檔。診斷規格與門檻先於本輪正式資料分析寫入 [diagnostic_protocol.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/diagnostic_protocol.json)。

## 1. 類別失衡與錯誤

| 分布 | DOWN | FLAT | UP |
| --- | --- | --- | --- |
| Train | 32 (33.3333%) | 32 (33.3333%) | 32 (33.3333%) |
| Validation | 5 (5.2083%) | 86 (89.5833%) | 5 (5.2083%) |
| rbf預測 | 50 (52.0833%) | 22 (22.9167%) | 24 (25.0000%) |
| qsvc預測 | 65 (67.7083%) | 17 (17.7083%) | 14 (14.5833%) |

Train 人工平衡，Validation 保留自然比例；total variation distance=0.5625。此差異已確認，但不能當作唯一因果根因。balanced class_weight 在32/32/32 Train實際均為1；現在直接比較 None 與 balanced 不會形成不同權重處理。每個稀有 Validation 類別只有5筆，單筆錯誤造成 recall變動20個百分點。時間相依與重疊標籤使樣本／pair不宜視為獨立重複，本輪沒有 bootstrap、重抽樣或 IID 信賴區間。證據：[class_imbalance_report.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/class_imbalance_report.json)。

| 模型 | 類別 | Precision | Recall | F1 | support |
| --- | --- | --- | --- | --- | --- |
| rbf | DOWN | 0.1 | 1 | 0.181818182 | 5 |
| rbf | FLAT | 1 | 0.255813953 | 0.407407407 | 86 |
| rbf | UP | 0.166666667 | 0.8 | 0.275862069 | 5 |
| qsvc | DOWN | 0.0615384615 | 0.8 | 0.114285714 | 5 |
| qsvc | FLAT | 0.823529412 | 0.162790698 | 0.27184466 | 86 |
| qsvc | UP | 0 | 0 | 0 | 5 |

Confusion Matrix 列為真實 DOWN／FLAT／UP，欄為預測 DOWN／FLAT／UP：

RBF：[[5, 0, 0], [44, 22, 20], [1, 0, 4]]；QSVC：[[4, 1, 0], [58, 14, 14], [3, 2, 0]]。

RBF Macro-F1=0.288362553，Balanced Accuracy=0.685271318；QSVC分別為0.128710125、0.320930233。與封存數值一致。

RBF 的86筆真實FLAT僅22筆命中，44筆判DOWN、20筆判UP，漏判64/86（74.4186%）；FLAT precision=1不代表覆蓋足夠，recall僅25.5814%。QSVC則僅14筆命中FLAT、58筆判DOWN、14筆判UP，漏判72/86（83.7209%）。

QSVC五筆真實UP全部漏判：3DOWN、2FLAT；14筆預測UP全部其實是FLAT。這不是『從不預測UP』；模型三類都有輸出，因此沿用的 CLASS_COVERAGE_WARNING 不觸發，另列零recall診斷。證據：[confusion_analysis.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/confusion_analysis.json)#/models、#/true_UP_cases、#/QSVC_predicted_UP_cases。

| 真實UP sample_id | RBF預測 | QSVC預測 |
| --- | --- | --- |
| bf62fc37a6f231bcf89c61dcf406fe5403af87b420ac41505871b9d78f9de847 | DOWN | FLAT |
| 57b1d5efc2717379c271af142143bb7be19c2f727006d50f01c06e757a264f4d | UP | FLAT |
| 9f184abfca9fa9f142a21495df5ac2d712bd3ea594d960cb2593dca679270268 | UP | DOWN |
| 38df2e9335e72fd70f087d03e97dd4405d6a18ab597d01dcd60957ccf2693d49 | UP | DOWN |
| 84f022a2bdb9cd75fa0c97af1ee2ea2b1d35d1dbe3625a3bc8e879ea7bf35e54 | UP | DOWN |

JSON逐筆保留上述樣本原四特徵、共享角度與對三類Train樣本的量子相似度mean/max。相似度不是QSVC decision_function；例如某筆UP對UP平均相似度最高仍判DOWN，不能以單一類別平均推斷SVM邊界。歷史模型的dual coefficients、support vectors與decision scores未封存，本輪不為取得它們而重訓。

## 2. Kernel數值與類別結構

| 項目 | Quantum | RBF |
| --- | --- | --- |
| 最小eigenvalue | 0.000629670553 | -2.26031551e-15 |
| 最大eigenvalue | 12.1842536 | 90.7579496 |
| 數值rank（門檻1e-10） | 96 | 52 |
| entropy effective rank | 43.6891988 | 1.30543427 |
| participation ratio | 27.042605 | 1.11705683 |
| 首eigenvalue／trace | 0.126919309 | 0.945395308 |
| condition（宣告rank門檻） | 19350.204 | INFINITE_AT_DECLARED_RANK_TOLERANCE |
| raw SVD condition估計 | 19350.204 | 1.41521714e+19 |
| centered label alignment | 0.128633613 | 0.369972537 |

兩矩陣皆96×96、finite-real、對稱且對角線為1；PSD容許誤差1e-10。Quantum min eigenvalue>0，數值rank96，condition約1.94×10^4，沒有保存矩陣的數值失效證據。RBF最小eigenvalue約-2.26×10^-15屬容許誤差；其數值rank52與門檻下condition無限，不能解讀為數學上精確rank52或模型必然失效。沒有修補、截斷或修改任何矩陣。

entropy effective rank = exp(-sum(p log p))；p由正eigenvalues正規化，僅在熵統計中略去數值負roundoff；participation ratio=(sum lambda)^2/sum(lambda²)。完整96項光譜、所有容許誤差與統計見 [quantum_kernel_diagnostics.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/quantum_kernel_diagnostics.json)、[rbf_kernel_diagnostics.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/rbf_kernel_diagnostics.json)。

| 類別pair（不含對角線） | Quantum mean | RBF mean |
| --- | --- | --- |
| DOWN/DOWN | 0.0631559519 | 0.961176888 |
| DOWN/FLAT | 0.0724736394 | 0.942043279 |
| DOWN/UP | 0.0665697229 | 0.906793944 |
| FLAT/FLAT | 0.111667412 | 0.965989969 |
| FLAT/UP | 0.122098769 | 0.95642061 |
| UP/UP | 0.128738232 | 0.964053972 |

同類1488個unique pairs，異類3072個；全部4560個上三角pair，對角線排除。Quantum within=0.101187199、between=0.0870473771，差=0.0141398216；RBF分別為0.963740276、0.935085944，差=0.0286543319。不同Kernel不能只按絕對mean差大小判優。

Quantum同類／異類分布高度重疊；FLAT/UP異類平均相似度0.122099還高於FLAT/FLAT的0.111667。Quantum label alignment0.128634低於RBF0.369973；這支持目前映射的類別分離／泛化能力可能有限，但不構成映射無法學習三類的因果證明。Quantum完整Train rank也不能證明可泛化。兩Kernel centered alignment=0.203716015，off-diagonal Pearson=0.183262173，幾何結構確有差異。

| Validation真實類別／Train類別 | Quantum mean | RBF mean |
| --- | --- | --- |
| DOWN/DOWN | 0.0822885278 | 0.972905527 |
| DOWN/FLAT | 0.0464616132 | 0.93506988 |
| DOWN/UP | 0.03554869 | 0.89259609 |
| FLAT/DOWN | 0.0672582689 | 0.95540488 |
| FLAT/FLAT | 0.0585310634 | 0.957763491 |
| FLAT/UP | 0.0579677608 | 0.939437273 |
| UP/DOWN | 0.0570379319 | 0.923492032 |
| UP/FLAT | 0.0555647906 | 0.954756663 |
| UP/UP | 0.0585007295 | 0.956183723 |

Validation UP對三個Train類別的Quantum平均相似度均約0.056–0.059，沒有清楚的聚合優勢；真實FLAT對Train DOWN的平均甚至高於對FLAT。這是相容於錯誤的幾何證據，不是SVM決策機制的重建。保存的是Validation×Train，沒有Validation×Validation Quantum矩陣，因此不虛構後者的PSD／光譜，也不補跑量子電路。

### Concentration的界線

Quantum off-diagonal mean=0.0916614242、std=0.135793236、CV=1.48146548，q05–q95=0.00109341601–0.385660546；沒有本輪near-constant判準的證據。RBF mean=0.944436305、std=0.0463315573、CV=0.0490573658，符合預先宣告的std≤0.05且CV≤0.10判準；首特徵值佔trace94.5395%、entropy rank約1.305也支持其近常數結構。

這是單一矩陣的描述性heuristic。不能由此宣稱／排除隨qubit數增加的漸近Quantum Kernel concentration，亦不能以RBF低effective rank推導它應比QSVC差。不同中心化後類別alignment可與共同常數成分並存。

## 3. Preprocessing稽核

原四特徵依序為obi_5、spread_bps、bid_volume_5、ask_volume_5。兩模型使用完全相同的封存共享角度，不使用時間戳、future return或class_label作特徵。原始特徵分布、quantiles、IQR、std、unique count、角度histogram與entropy均見 [preprocessing_analysis.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/preprocessing_analysis.json)#/splits。

Frozen StandardScaler來自Phase3B Train3000，mean/scale完整保留；Budget角度上下界只來自這次Train96。z=(raw-mean)/scale，theta=pi*clip((z-zTrainMin)/(zTrainMax-zTrainMin),0,1)；正scale在後續min-max代數抵消，故有效範圍是Budget Train原特徵min/max，不代表本輪重新fit了任何參數。

Train及Validation四特徵below/above clipping均為0、常數mask均False、無nonfinite；重算固定公式與共享CSV角度最大差0。本輪排除Prototype clipping、常數特徵及錯用不同輸入。Smoke24曾有7筆spread下界clipping，屬不同功能驗證集，不能套成Prototype預測的成因。

| 特徵 | Train raw mean | Validation raw mean | Train角度q05–q95寬度/pi | Validation角度q05–q95寬度/pi |
| --- | --- | --- | --- | --- |
| obi_5 | 0.19026552 | -0.0486196111 | 0.994995016 | 0.922647721 |
| spread_bps | 0.00127277497 | 0.00126970607 | 0.70404123 | 0.304158868 |
| bid_volume_5 | 2.67557885 | 2.04017448 | 0.824248132 | 0.443243262 |
| ask_volume_5 | 1.64772844 | 2.2759499 | 0.314604296 | 0.348265084 |

特徵不是常數，但存在分布集中與變動：Train ask_volume_5最大14.79405、q95僅4.6607425，其角度median0.18138 rad，Train q05–q95只覆蓋全[0,pi]約31.46%；Validation spread角度平均0.92133對Train1.78493，Validation q05–q95寬度約30.42%。這支持壓縮／covariate shift風險，無法證實它們造成QSVC失敗；不據Validation更改處理。

單一P(2*x)的pi週期不能推論完整ZZ feature map每一維也獨立pi週期；ZZ的2*(pi-x_i)*(pi-x_j)交互項一般會改變。僅以既有Train角度計算7個gate phase係數的圓距離，不建立電路或Statevector。預先宣告『角度距離≥Train pair q90=3.60242423且既有Quantum相似度≥0.9』的pair數為0；目前不足以證明遠距樣本因週期折疊接近，更不能說週期性是錯誤根因。這個零計數不排除較細微的折疊。

## 4. 公平比較與可推論範圍

IDs／順序、Train和Validation labels、四特徵順序、C=100、class_weight=balanced、seed42、Decimal sign三分類政策、Train-only標準化與角度映射全部核對PASS。RBF gamma固定0.01；QSVC的gamma=scale只是繼承參數，在precomputed模式不參與Quantum Gram。證據：[fairness_review.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/fairness_review.json)；歷史共用輸入路徑見 [Phase4A1 runner.py](/home/jason/quantum-hft/experiments/phase4a1/runner.py) 的stage函式。

**同樣C不代表不同Kernel具有相同有效正則化。這是預先固定設定的受控比較，不是兩個充分最佳化的最強模型比較。** RBF gamma曾由舊Phase3B Validation選定，量子map則預先固定；不能宣稱搜尋預算相等或量子優勢。

未保存Prototype Train預測、support vectors或decision_function，因此本輪不能量化Train/Validation訓練分數落差、證明過擬合或指定某個support vector為根因。少樣本、時間分布與既有Validation重複研究都限制外推。Final Holdout與Test沒有參與本輪分析或選參。

## 5. 原因評估

沒有已證實的唯一因果根因。CONFIRMED用於可直接核對的描述性事實；SUPPORTED_BUT_NOT_CAUSALLY_PROVEN是相容於證據的假說；INSUFFICIENT_EVIDENCE不代表假說已被否定；RULED_OUT僅限明載的檢查範圍。完整分級、來源pointer與因果限制見 [root_cause_assessment.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/root_cause_assessment.json)。

| 項目 | 分類 | 本輪判斷 |
| --- | --- | --- |
| prior_shift | CONFIRMED | 32/32/32對5/86/5；balanced權重全1，已確認分布差異 |
| qsvc_up_errors | CONFIRMED | 5個UP全錯；14個預測UP全是FLAT |
| rbf_near_constant_structure | CONFIRMED | 固定gamma下RBF近常數結構；非失敗因果證明 |
| imbalance_contribution | SUPPORTED_BUT_NOT_CAUSALLY_PROVEN | 先驗差異可能影響方向預測；不是唯一根因 |
| limited_label_separation | SUPPORTED_BUT_NOT_CAUSALLY_PROVEN | Quantum類間重疊、較低label alignment與Validation錯誤一致 |
| sampling_uncertainty_and_time_shift | SUPPORTED_BUT_NOT_CAUSALLY_PROVEN | 稀有類別各5筆、特徵分布變動；不能確定貢獻大小 |
| quantum_numerical_failure | RULED_OUT | 已保存Quantum Gram的數值故障在宣告容許誤差內排除 |
| prototype_clipping / constant_features | RULED_OUT | Prototype無clip、無常數、無nonfinite |
| unfair_membership_or_transform | RULED_OUT | 在封存manifest／source可稽核範圍內排除 |
| quantum_empirical_near_constant | RULED_OUT | 僅排除本輪近常數判準；不是漸近定理 |
| independent_mod_pi_equivalence | RULED_OUT | 單一phase gate週期不能套給完整ZZ map |
| asymptotic_quantum_concentration | INSUFFICIENT_EVIDENCE | 只有固定4-qubit單次矩陣 |
| periodic_folding | INSUFFICIENT_EVIDENCE | 宣告far/high-fidelity pair為0，較細微效應未知 |
| svm_margin_or_support_vectors | INSUFFICIENT_EVIDENCE | 未封存dual／margin，未為此重新fit |
| optimal_regularization | INSUFFICIENT_EVIDENCE | equal C不等效；本輪不調參 |
| upstream_market_label_quality | INSUFFICIENT_EVIDENCE | 完整性及sign一致不等於上游所有標籤經濟意義均正確 |

## 6. 下一輪候選設計（只建議）

所有方案須另建protocol、新run_id、新Budget封存與人工批准，不能用既有Test選參。需預先限制Validation檢視次數與比較次序，避免持續看同一Validation導致研究層面的過擬合。詳見 [proposed_experiments.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/proposed_experiments.json)。

1. 從原Dataset v1 Train另建自然市場比例的小樣本；現有3B已平衡Train不能靠再做label-blind子抽樣恢復自然先驗。本輪沒有讀取原完整Train。
2. 在自然比例Train比較預先固定的None／balanced，或先驗指定不等權重；目前32/32/32直接None對balanced沒有有效差異。
3. 預先固定一種替代map（如Z-only對ZZ），保持qubits／reps及共同輸入，單因子比較。
4. 預先固定一種角度範圍或平滑bounded scaling；同一表示仍由兩模型共用，不能依本Validation改值。
5. 新budget可提議Train96→192；需固定scaler fit範圍以隔離樣本數效應，沒有在此產生192矩陣。
6. 預先指定多個連續時間區段，以Train-only purged development切分檢查穩健性；遵守實際標籤終點／lookback，不shuffle。
7. 下輪以1000ms作主horizon；其他horizon另註冊，不依Test挑選。

## 7. 測試、完整性與來源

人工 fixture單元測試38/38 PASS（零skip／failure／error）；涵蓋identity／rank-one光譜、負eigenvalue與shape拒絕、排除對角線、固定RBF公式、三類零recall統計、Train固定轉換、clipping／constant handling、ZZ週期界線、Test/Holdout讀取拒絕、公開NPY header roundtrip／超大shape／錯誤dtype、AST安全檢查。獨立算式複核25項PASS；不是重新跑Quantum或訓練模型。證據：[summary/unit_tests.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/summary/unit_tests.json)、[summary/independent_audit.json](/home/jason/quantum-hft/artifacts/phase4a2/20261030T000951Z/summary/independent_audit.json)。

初次run20261030T000449Z因診斷loader使用NumPy不再提供的私有header API而FAIL，該FAIL、traceback、程式快照與報告永久保留。改用公開read_array_header_1_0／2_0並新增3個header fixture測試後，本run從頭執行，沒有沿用未完成分析；既有Phase4A-1結果完全不變。

完整性：受保護非Holdout檔案2997個fresh SHA全部一致，涵蓋Phase4A-1和舊FAIL封存；兩個venv逐項hash／mode／symlink snapshot一致；Phase3B Frozen、Phase4A-0 Budget與Dataset v1保持不變。Dataset非Holdout資料只做opaque SHA完整性讀取，沒有解析Test values。32個Final Holdout CSV僅stat metadata比對與沿用既有封存SHA，未開啟內容，因此不宣稱重新hash了Holdout內容。Dataset tree證據：{"btcusdt_aggregate_v1_20261026T202040Z": {"mode": "fresh non-Holdout SHA, prior Holdout SHA plus unchanged stat; no Holdout CSV content read", "status": "PASS_WITH_SEALED_HOLDOUT_HASH_REUSE", "tree_hash": "1f86a013d9eddc240fbeda7b5dd0eb3286d65049df7e1bae15648a1a892bafe0"}, "btcusdt_depth_top5_v1_20261026T202040Z": {"mode": "fresh non-Holdout SHA, prior Holdout SHA plus unchanged stat; no Holdout CSV content read", "status": "PASS_WITH_SEALED_HOLDOUT_HASH_REUSE", "tree_hash": "d55541bdc1bd2ab1bea3d0767932fa9a713a059c68f95590c262aa644d7c0687"}}。

沒有安裝套件或網路下載、沒有新模型fit、量子電路評估、QPU、QAOA、QUBO、Binance、Testnet、真實交易、Paper Trading或回測。Final Holdout保持LOCKED。

| 判斷／功能 | 來源檔案與函式 |
| --- | --- |
| 輸入／label／SHA核對 | experiments/phase4a2/io.py::load, rows, matrix, read_npy_header |
| 類別比例／錯誤 | experiments/phase4a2/analysis.py::imbalance, confusion, error_cases |
| Kernel光譜／within-between／concentration | experiments/phase4a2/analysis.py::spectrum, class_similarity, kernel_diagnostics, alignment |
| 固定前處理／特徵分布／週期 | experiments/phase4a2/analysis.py::transform, feature_distributions, phase_coefficients, periodicity |
| 公平性／原因／建議／安全guard | experiments/phase4a2/runner.py::fairness, assessment, proposals, static_audit |
| 完整性 | experiments/phase4a1/contracts.py::integrity, snapshot, verify_budget, sha（唯讀重用，未import模型runner） |
| 獨立數值複核 | 本run/independent_audit.py（直接計算saved array與prediction統計） |
| 人工fixture測試 | tests/test_phase4a2_diagnostics.py；tests/fixtures/phase4a2/helpers.py |

完整命令、實際stdout／stderr與exit code見command_ledger.json、command_history.txt和logs。無可用Git commit時以summary/code_manifest.json及completion_manifest.json內SHA作程式版本。本報告與run全檔以exclusive新增方式封存，不覆寫既有檔案。

**本階段完成後停止，等待人工審核；沒有進入下一研究階段。**
