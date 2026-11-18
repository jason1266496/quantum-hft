# Phase 4A-0 固定實驗規格

本規格只完成實驗準備與小樣本鎖定；Phase4A-1必須另獲人工批准。規格在讀取預算子集合的Validation分布前固定，沒有依Test改設定。
Primary=1000ms、aggregate_core_v1；Feature order：obi_5, spread_bps, bid_volume_5, ask_volume_5；分類沿用direction_3class_exact_v1，Decimal return負／零／正=DOWN／FLAT／UP。
父資料唯一為Phase3B 20261029T220053Z Frozen Subset v2。不得重切原Dataset split，不得改Frozen membership或讀Test／Holdout值。

## 固定抽樣
Prototype Train每類32共96；Validation96。Train只在各Train class內穩定依event_time排序，取floor(i*(N-1)/(k-1))，含頭尾。Validation只按event_time排序取相同rank公式，不讀label決定indices。
Smoke嵌套於Prototype：Train每類8共24，Validation24，沿用相同規則。Smoke與Prototype跨規模重用IDs是刻意嵌套；每個profile/split內無duplicate，Train與Validation在所有profile間完全不重疊。
不足指定樣本即停止，不自動降規、不重複／合成／shuffle；seed42，但抽樣本身無randomness。

## 共同輸入與公平比較
保留父Frozen 1000ms Train3000的StandardScaler參數與SHA，不refit、不更動父manifest。各Budget的角度範圍另只fit該Budget Train；Validation transform only。
z=(x-FrozenMean)/FrozenScale；非constant欄theta=pi*clip((z-zTrainMin)/(zTrainMax-zTrainMin),0,1)。常數欄theta=pi/2。Validation超界只按預定規則clip，記錄次數，不用來改範圍。
Frozen正scale在min-max式中代數抵消，所以有效角度範圍只依該Budget Train的raw extrema。保存base參數、Budget Train IDs SHA、z extrema、constant mask、raw CSV、standardized reference CSV及shared angles CSV。
StandardScaler的z為零中心尺度表示，角度表示為有界[0,pi]且可能clip，兩者幾何不同。未來RBF／QSVC都以相同shared angles檔、相同labels/IDs/order/split比較；不能把舊3000-row RBF score當成same-budget基準。
兩模型C固定100、class_weight=balanced；RBF gamma固定0.01，來源是既有Phase3B的Validation選擇，本輪不重調；QSVC目標FidelityStatevectorKernel。RBF必須在相同Budget Train重新fit，但本階段不執行任何model fit。

## 預定電路
4 features／4 qubits，zz_feature_map，linear [(0,1),(1,2),(2,3)]，reps1、alpha2、parameter prefix x、4個輸入參數；不搜尋電路架構。
本機exact statevector，seed42，不使用QPU。參考未transpile H/P/CX分解為H4、P7、CX6，共17 gates、depth11；這是明列的設計排程推導，不是SDK或硬體實測。若Qiskit缺失，SDK count/depth/parameter count標NOT_AVAILABLE。
實際API與相容性只以本輪metadata/import與允許的circuit construction確認；不以Python版本要求推論完整Kernel／QSVC runtime可用。

## 預算與環境
Smoke 24x24 Train及24x24 Validation-vs-Train各576元素、各4608 bytes，合計9216 bytes；Prototype 96x96各9216元素、各73728 bytes，合計147456 bytes。都是float64 dense理論量，不含cache/model overhead。
4-qubit statevector維度16，單一complex128 vector理論256 bytes；沒有估計或執行quantum runtime，禁止3000-row Quantum Kernel。
缺Qiskit仍完成規劃與非Qiskit測試，runtime標DEPENDENCY_BLOCKED，不安裝套件或建立venv。候選獨立venv /home/jason/.venvs/quantum-hft-qml僅建議；相容pin尚未離線驗證，須另案批准及驗證。
保留Phase3B baseline instability：1000ms Test預測102／0／898、FLAT recall0；本輪不重新評估Test，不假設量子改善。

## 停止條件
輸入hash、Frozen、LOCKED或抽樣規則不符立即FAIL並停止。完成本輪後等待人工審核；無Quantum/RBF訓練、正式Kernel、Test評估、QPU、QUBO/QAOA、網路、交易、回測或Paper Trading。

首個準備run：20261029T222609Z；實際檔案與SHA見該run manifest與FROZEN.sha256。
