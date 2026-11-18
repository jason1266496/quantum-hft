# Phase 4B-2B Preregistration Protocol：跨日市場資料、原始訂單簿與確認性量子研究
文件版本：4B2B-design-v1；文件 run_id：20261031T085529Z。
審查日期：2026-10-31（Asia/Taipei）。狀態：DESIGN_COMPLETE_PENDING_HUMAN_REVIEW。
本文件是待人工批准的預註冊提案，不是已執行研究或已生效的 Capture 授權。所有標為「設計選擇」的數值須在相應批准 Gate 前鎖定；變更須新增版本、理由、SHA 與適用日期，不修改本文及舊成果。

標記：**FACT**＝封存證據／本次核對支持；**HYPOTHESIS**＝待檢驗；**DESIGN**＝提出並可執行的選擇；**UNKNOWN／NOT_ESTABLISHED**＝未證實。工程 PASS、來源資格、統計推論及量子優勢是不同判斷。

## 1. Executive Summary

**DESIGN**：本研究首先提升原始事件可追溯性及跨日評估可信度，再比較固定 QSVC 與 RBF。主要研究為固定模型在未來日期的配對 Macro-F1 差異，允許負面或不確定結果。目標不是保證量子模型勝出。

本輪只新增這份規格、審查文件與 manifest；不建立程式、fixture 執行器、Dataset、網路擷取工作或排程。本輪人工 fixture 為測試規劃，執行數 0；未 fit／predict／計算正式 Kernel。只讀歷史報告、設定與摘要；未讀市場 CSV、Test 或 Holdout 內容。官方技術文件有經網路查閱，沒有 Binance 行情 REST／WebSocket 連線或行情下載。

**下一個最小工程 Gate**：離線 Capture schema／Snapshot-Diff 狀態機／雙 Reference 的人工 oracle 契約測試；新 Development Area、無網路、無正式資料、無模型。可以送交批准，現在不執行。

## 2. Current Evidence Assessment

| 判斷 | 證據與界線 |
|---|---|
| FACT：Phase 4B-2A PASS_WITH_RESTRICTIONS | run 20261030T114058Z；封存 171/171 tests、150,912 Train、1,440 Walk IDs 一致，return/direction/time/endpoint mismatch 0 |
| FACT：PRICE-WITNESS-INDEPENDENT 150,912；RAW-INDEPENDENT 0 | 獨立重配來自 pre-label aggregate CSV 的價格，不是 Snapshot/Diff 重建證明 |
| FACT：同一 UTC 日期 2026-08-26 | 三個來源 alias 不是三個獨立物理 capture；物理 session 數與 exact historical producer UNKNOWN |
| FACT：額外 witness 排除 9,203 | 9,174 endpoint 自己的 match error >1ms；29 endpoint 自己處於 tail；不是證明其當下價格無效 |
| FACT／歷史結果：RBF balanced mean Macro-F1 .371665、BA .514003；QSVC balanced .324289、.351952 | 引用歷史封存與使用者審核，不在本輪重算；三個同日 Fold，非三個獨立交易日 |
| FACT／歷史限制 | F3 Train UP=1；F1 Validation 標籤高度重疊；歷史工程 FAIL 不被後續指標稽核改成端到端 PASS；predict trace 不完整 |
| NOT_ESTABLISHED | 跨日／跨市場泛化、量子優勢、量子加速、可成交或獲利能力、完整無漏包、真實網路抵達時間 |
| 保護狀態 | 舊 Test 不參與開發或評估；Final Holdout LOCKED；新 Confirmation 是另外的前瞻性封存，不是舊 Holdout 改名 |

本次核對最新 completion SHA 為 c8552056002722ebe41564b3894fcbbaa7b2bae800494e14efd8b1d6cf6092d9，並核對選定摘要的 SHA／大小；不是重新執行 20,393 項完整性檢查。Dataset／Frozen／venv 的完整性 PASS 引用上一輪已封存證據，本輪未開其內容、未修改，沒有虛報新的全量 integrity PASS。

證據：[最新正式報告](/home/jason/quantum-hft/docs/PHASE4B2A_REPORT_20261030T114058Z.md)、[證據分級](/home/jason/quantum-hft/artifacts/phase4b2a/20261030T114058Z/evidence_level_coverage.json)、[來源評估](/home/jason/quantum-hft/artifacts/phase4b2a/20261030T114058Z/source_findings_assessment.json)、[歷史模型契約](/home/jason/quantum-hft/artifacts/phase4b0/20261030T020400Z/model_protocol.json)。

## 3. Research Questions

1. 能否讓每列特徵／Label 從不可變原始 Snapshot＋Diff 重建，而非只證明衍生表相符？
2. 固定訓練、固定四特徵與預算時，QSVC 與 RBF 在未見日期的 Macro-F1 差異及不確定度為何？
3. balanced 權重是否改變少數類別辨識、預測覆蓋及日期間穩健性？
4. 排除政策會留下哪些時間、來源品質、類別與特徵分布？差異能否以 provenance 解釋？
5. 相同資料與固定設定下，量子模擬 Kernel 的完整運算成本與數值品質如何？

問題 1 是工程／測量效度；問題 2 才是主要統計問題。問題 3–5 不作事後選擇主要模型的理由。

## 4. Primary／Secondary Hypotheses

**HYPOTHESIS P1**：對指定擷取時段及資格政策所定義的未來日期母體，令
d_date = MacroF1(QSVC balanced, date) − MacroF1(RBF balanced, date)；
主要 estimand 為依預註冊品質政策合格且可評估日期的等權平均 Δ，而非所有事件混在一起的 F1；有缺日時不冒稱它是完整計畫日期平均。H0：Δ=0；H1：Δ≠0，雙側 α=.05。方向不預設。固定模型的條件式比較，不涵蓋所有可能 Train 抽樣或跨市場環境。

**DESIGN**：規劃有意義差距 δ=.02 Macro-F1、目標 power=.80，須教授確認其研究意義。若 CI 排除 0 但幅度小於 δ，不宣稱具實質優勢。未拒絕 H0 不等於等效；本次未預註冊等效／非劣性主張。

Secondary：None QSVC−None RBF、同模型 balanced−None、權重與模型的差異交互作用、BA／各類 Recall／coverage／成本／品質分層。全部完整報告，預設描述性，不另製造未校正的顯著性結論。若教授要求第二個確認性檢定，必須在 Confirmation 前新增明確假設族、Holm 校正及 power 規劃，不能看完結果再升格。

Raw-to-label 一致、零跨邊界 Label、完整 trace 是 Gate，不以模型分數決定工程 PASS。替代 horizon、deadband、Feature Map、scaling、新 class weighting 都不是本次主要研究變數。

## 5. Capture Protocol

**官方文件核對，非本輪連線執行**：Spot Diff Depth 提供 E、U/u、b/a，支援 100ms 頻率；Snapshot 深度上限有限，數量更新是指定該價位的新數量，零量刪除。啟動須先緩衝串流再用 Snapshot 銜接；一般更新 U>本地 ID+1 表示缺口並重建。官方文件亦列出連線壽命、ping/pong 與限流要求，實際擷取前須鎖定當時版本。[官方串流與 Book 指引](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md)

**DESIGN**：未來僅訂閱 BTCUSDT Spot 的單一 Diff Depth 100ms 串流，預設毫秒 E；不使用 partial depth 代替 Diff。REST Snapshot 預計 GET /api/v3/depth，symbol=BTCUSDT、limit=5000；保存原始回應、請求參數及時序。官方文件顯示此深度對應 request weight 250；不可把重試當無成本。[官方 Snapshot 規格](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market)

**OPEN-API-01，正式 Capture 阻擋項**：本次所讀官方 GitHub bootstrap 第 5 步寫 lastUpdateId 位於 [U,u]，一般套用步驟則允許 U=本地 ID+1。兩個位置對「第一個 U=L+1」的邊界表述不同，不能默默宣稱官方已證實同一個 bootstrap 規則。工程前建立 L−1/L/L+1/L+2 fixtures；正式 Capture 前須鎖定一份經人工審核、附官方版本來源的解釋。暫定保守 bootstrap 只接受 U≤L<u；U=L+1 不默默接受，記 BOOTSTRAP_BOUNDARY_UNRESOLVED，重取 Snapshot／超過預定次數則該 session 失敗。此保守規則是設計選擇，會降低可用率，不是宣稱交易所不允許 U=L+1。此問題不阻止離線契約測試，會阻止正式擷取批准。

建議狀態機：
STOPPED → CONNECTING → BUFFERING → SNAPSHOT_PENDING → ALIGNING → LIVE_VALID；
遇解析破損、U/u 缺口、重連、未知深度、時間倒退等 → INVALID_SEGMENT → RESYNC；
任何寫入丟失、hash 錯誤、重試耗盡 → SESSION_FAILED。
每次重連換 connection UUID，重新 Snapshot；不沿用舊 Book 假裝連續。恢復只在固定 session 時窗內，不能延長到取得有利資料。

**擷取實作設計選擇**：
- 將 WebSocket library 交付的完整訊息 bytes 先封存再解析；標記為應用層 payload，不冒稱 TCP/IP 封包或 wire framing。長度、SHA、單調 receive_sequence、raw offset 必存。控制訊息、關閉原因、parse error 不丟棄。
- wall clock 用 CLOCK_REALTIME ns；monotonic 用 CLOCK_MONOTONIC ns；記 boot ID、clock API、實際程式採樣位置及兩次取樣間隔。其他可用精度／同步誤差 UNKNOWN 時寫 UNKNOWN。
- user_receive_complete：library 完整訊息交付後、parse 前採樣；處理階段另存 parse_start/end、book_apply_start/end、feature_emit；Replay 的開始／完成時間另欄。Exchange E 不宣稱撮合瞬間，任何 local−E 不叫網路延遲。
- Snapshot 存 request_start、response_complete 的兩種時鐘，不把 response_complete 當 Snapshot 的 exchange timestamp。
- 限流器、ping/pong、關閉通知與重連行為依鎖定官方文件實作；未鎖定的 HTTP error、退避、服務區域可用性、停市狀態語義標 PENDING_OFFICIAL_VALIDATION。
- 提案最多每 session 10 次重連、單次銜接最多 3 次 Snapshot、退避 1/2/4/8/16/30 秒封頂；遇官方 retry-after 必須遵守更長等待。這些是保守資源政策，不是交易所保證值。完整 rate-weight 預算與磁碟 cap 在網路批准前固定。
- 寫入失敗不得靜默 dropping；bounded queue 溢出須記缺口並立即失效。raw 持久化未確認的資料不能標為研究有效。
- 單 session 主要來源檔案連續寫入；不得跨來源檔建立主要 Label。若尺寸 cap 觸發輪替，記新資料區段與其 tail 排除，不把檔案切換藏起來。未批准前不建立 daemon、cron 或可自啟腳本。

## 6. Source Provenance Contract

**DESIGN**：schema 欄位約束如下；本文件是欄位規格，尚未宣稱 JSON Schema 驗證器已實作。UUID 採 UUIDv4；時間與 update ID 用精確整數，價格／數量保存十進位字串；必填欄位缺失 fail closed，不能猜測來源。UNKNOWN 僅限明列可未知的環境資訊；核心 lineage 不可 UNKNOWN。

| Schema | 必填欄位與關係 |
|---|---|
| Capture manifest v1 | schema_version、protocol_sha256、run_id、capture_session_uuid、venue/market/symbol、scheduled_start/end_utc、actual_start/end、status、producer_code_sha、config_sha、environment_sha、檔案 path/size/SHA 清單、failure_reason |
| Raw event v1 | capture/connection UUID、source_file_id、receive_sequence、byte_offset/length、payload_sha、原始 bytes 引用；event_type、E、E_unit、U/u、b/a decimal strings、user_receive_wall_ns/mono_ns、parse_status；U/u 僅 depth event 必填 |
| Snapshot v1 | snapshot_uuid、capture/connection、原始 body bytes 引用/SHA、method/path/params、HTTP status、request/response timestamps、lastUpdateId、bids/asks、銜接 raw ID、採用／拒絕原因 |
| Session metadata v1 | host/boot/process identity、OS/kernel/CPU、Python/C++及依賴版本、git commit或code tree SHA、dirty diff SHA、時鐘 API／同步服務／offset估計與不確定度、檔案權限、磁碟與queue policy、來源文件版本 |
| Gap/reconnect log v1 | 原因、上一個 local u、下一個 U/u、原始訊息引用、偵測的 wall/mono、舊／新 connection與segment、snapshot UUID、失效範圍、重試及恢復結果 |
| Independent reference row v1 | sample_id、capture/connection/segment/source、raw current/endpoint ref、snapshot SHA、current/endpoint book digest、E_current/E_target/nominal、mid/return decimal、direction、actual_horizon/match_error、invalid_reason、evidence_level、reference_code_sha |
| Dataset build manifest v1 | 新 dataset_id、來源 manifests SHA、protocol/schema/code/環境 SHA、每個 split 日期與 IDs SHA、列數、排除 ledger SHA、Label policy、feature_order、品質門檻、父版本關係；不得覆蓋 Dataset v1 |
| Dataset lineage v1 | sample→current/endpoint raw offsets→snapshot＋所有套用 Diff 範圍→source SHA；每段重建狀態摘要可加速驗證但不能代替原始事件 |
| Quality audit v1 | 全部排定／成功／失敗日期與session、原始／有效／排除分母、reason×date×time-slot、1000/1001/>1001分布、class與feature分布、reference mismatch、深度覆蓋、QA審查人／時間 |
| Reproducibility manifest v1 | code/config/schema/protocol SHA、environment lock、seed、完整 command argv、cwd/env allowlist、stdout/stderr/exit、開始結束、input/output SHA、parent run、repeat links、實際 fit/predict/kernel counts |
| Review/approval v1 | reviewer身份、時間、文件SHA、授權階段、允許輸入／輸出／網路、未解問題、失效條件；不得由模型自行批准 |

capture_session_uuid 是實際開始／停止擷取的身分；connection_uuid 是每次連線；reconstruction_segment_uuid 是可驗證連續且時間單調的區段。換 UUID 不代表市場事件統計獨立。chunk_id 與檔名日期亦不是 capture 身分。

source SHA 只證明 bytes 完整性，不證明交易所對訊息簽章、無漏網路包或 producer 無惡意。未來保存 endpoint hostname、TLS 驗證設定與可取得的 peer 記錄，仍只聲稱對受驗證連線所封存訊息的可追溯性；不宣稱交易所全域真相。

## 7. Raw-to-Label Verification Protocol

**DESIGN，兩個獨立實作**：
A：新隔離實作的 C++ Book（精確定點／整數 decimal lexeme）＋production builder；
B：新 Python Reference（Decimal 價格字典、獨立排序取 top5、獨立 endpoint search）。
這是未來模組提案，不修改 HFT 原始碼。A、B 可共用 schema／雜湊格式／人工 oracle 文件，不共用 Book update、top5、mid、matcher、return、direction 函式或 A 的衍生輸出。B 不讀 A 的 future time／future mid／labels來選 endpoint。跨語言高精度實作若需要新依賴，須另批准；現在不安裝。未能實現所定 Decimal 舍入則 Gate BLOCKED，不能改用 float 代替。

重播依 connection 的原始接收順序與 U/u，不先按 E 重排。先驗證合法 Snapshot、bootstrap，排除過時已涵蓋事件；LIVE 中 U>local_u+1 為缺口，終止舊區段。u=local_u 的完全重複事件僅保留 raw，不重複產生樣本；同 ID 不同 payload 標 DUPLICATE_CONFLICT、隔離而非任選。重疊 update ranges 依鎖定規則逐筆更新並留下處置紀錄；數量是覆寫而非增量。

每次合法事件全部 bid/ask 更新完成後才輸出狀態，不使用事件中途暫態 Book。價格必須正、數量非負有限，零量刪除；重複價位、非整數 ID、U>u、錯 symbol、缺 key、非有限數 fail closed。空側、bid≥ask、五檔不足、未知外部深度可能進入 top5 均使 row 無效並重建。

**有限 Snapshot 的保守 top5 證明**：保留初始 bid 最低已知價格 B_min、ask 最高已知價格 A_max；持續無缺口更新下，前五個 bids 必須都 ≥B_min、asks ≤A_max，且各有五個有效非零價位。不能以「容器有五檔」代替此覆蓋證明。越過內界即 BOOK_DEPTH_COVERAGE_INSUFFICIENT，重取 Snapshot；全深度市場重建仍 NOT_ESTABLISHED。

**主要 Label 保留 Phase 2D 語義**：
- 每個有效事件建立同 source／capture／connection／segment／來源檔的候選 current；倒退 E 終止段，重複 E 不去重，tie 用原合法事件順序。
- nominal=current_E+1000；在同一有效區段尋找第一個 E≥nominal 的事件。不先過濾 future 的 Label eligibility，也不為改善 match 選第二個事件；找到的事件本身 Book／feature無效則標 invalid。
- mid=(best_bid+best_ask)/2；Decimal precision=50、ROUND_HALF_EVEN，各運算舍入順序固定為加總→除2；return_bps=(future_mid/current_mid−1)×10000，除法→減1→乘10000逐步依相同 context。
- direction=該已定義 Decimal return 的負／零／正，DOWN=0、FLAT=1、UP=2。沒有 deadband，不四捨五入成交易 tick 後再分類。
- target_event_time 是實際匹配事件時間；nominal 獨立保存；actual=target−current，error=actual−1000。主要研究納入 error∈{0,1}，分別報告1000/1001ms。
- A 採 streaming two-pointer；B 採每段原始順序的 timestamp array＋獨立 lower-bound。原始事件→Book→價格均各自生成，不把 A 的索引餵給 B。
- 逐列比較 IDs、有效性／reason、current/endpoint Book top5、時間、mid、return、direction。Decimal精確相等容忍度0；float feature的唯一轉換規則另鎖定，數值容忍不能依結果放寬。
- invalid reason固定優先序：來源/hash/sequence問題（段失效）→時間倒退→current Book/feature問題→無endpoint（segment/session/file/split tail）→endpoint Book/feature問題→match error超標→split purge。保留所有觸發flags，primary reason只是可重現摘要。
- 主 Label 不跨 gap、重連、session、來源檔、split；儲存 candidate 未通過列，不刪證據。

Reference獨立性驗收：故意破壞 A 的 mid/target/labels，B 輸出應完全不變且 comparator 必須報錯。手工 oracle 要涵蓋零量刪除、top5換位與極小return；兩程式一致不等於不共享規格錯誤。冷啟動 repeat 重讀 raw、從 Snapshot 重播；不把 cache 命中當獨立重建。

每列只有原始 lineage 完整、A/B 獨立 Book/Label 相等、同步／深度／時間檢查通過才給 RAW-INDEPENDENT。該等級限定於封存原始訊息，不表示交易所全市場真實性或可執行交易。缺少 raw 時只能降級，不能用成功比例掩蓋缺失。

## 8. Data Quality／Exclusion Policy

**DESIGN，主要 cohort Q1**：raw lineage完整；Snapshot/Diff連續且 top5已知；當下和first future端點有效；同段／檔／session；actual∈{1000,1001}ms；label endpoint嚴格落在split與session結束之前。維持所有候選 ledger與多重原因。額外 inactivity gap 提案為相鄰 E 差>1000ms時切段，絕不 ffill；這是新資料品質政策，不是假稱歷史 Phase2D 有此門檻。精確1000ms與1001ms gap fixtures另驗，不能與 label horizon混為一談。

**Endpoint witness的新定義**：端點必須直接指向有效 raw/Book；不要求它存在於 filtered Train，也不要求它有自己的1000ms future label。尾端事件可當較早列的合法價格端點，即使自身Label無效。端點本身 Book無效與端點未來Label無效嚴格分開。

**預定品質敏感度（描述性、不選模型）**：
- Q0：可重建且有合法first endpoint，保存所有actual/error分布，不自動拿較寬horizon訓練。
- Q1：主要0..1ms政策。
- Q2：Q1再加endpoint自身也通過Q1，僅量化舊額外 witness規則的選擇；不得取代Q1，也不重做舊Fold。
- exact1000與1001 strata分開報告；較寬match、不同gap／deadband若要模型比較須新次要protocol，本次不執行。

**來源接受政策**：原始資料全部封存，包括失敗。進入主要研究的session須UUID/producer/檔案/時序完整、無未解hash或重建mismatch；有效連續Book覆蓋排定2小時至少95%，且Q1候選≥192。日須兩個固定時窗皆通過。覆蓋由receive/mono時間及失效段計算，不以價格、類別、波動或模型分數選日；event inactivity缺口仍另報。局部gap可使該段無效，不把整個session冒充無gap。未知來源、未解重建mismatch隔離，不能補值。

全部排定日期均列入study flow，不合格日為missing，不刪掉日曆再把鄰日當連續。不得換成「下一個好日」。報告每個date/session/time-bin的候選、Q0/Q1/Q2、tail、match、深度與連線排除率；比較篩選前後可得的feature分布與direction比例，unlabelable不強填方向。以標準化差異與圖表描述，不用p-value宣稱篩選無偏。品質門檻會條件化母體，QA即使盲於模型結果也不保證無 selection bias。

## 9. Prospective Date Selection

**DESIGN，完整日曆先鎖**：
D0 = 所有網路擷取批准完成後至少72小時的第一個00:00 UTC。批准時將公式展開為明確日期表、寫SHA；不得用近期市場表現選D0。
每天固定兩個physical capture sessions：00:00–02:00、12:00–14:00 UTC，各2小時；連線可在前2分鐘warm-up並保存，但模型候選僅在指定區間。結束後不延長補樣本，不跨session建標籤。每次獨立啟動都有captureUUID；週末照排。只能推論這些時段與市場，不能宣稱24小時代表性。

| 日曆區間 | 角色 | 允許用途（均須未來授權） |
|---|---|---|
| D0..D13：14日 | Development Train | 資料工程、固定Train抽樣、fit preprocessing／固定四模型 |
| D14..D41：28日 | Validation／Planning | 固定模型的探索性跨日檢查、日間變異／品質／成本規劃，不挑參數或日期 |
| D42..D48：7日 | 凍結／隔離間隔 | 獨立審查、鎖定Confirmation N及分析程式；不納入主要研究、不需擷取 |
| D49起N個連續日 | Confirmation | N於D49前固定，候選56或84日；資料由受控custodian保管，一次批次評估 |

總規劃跨度為105或133日（含7日空檔）；這是資源提案，不是足夠power保證。若教授的競賽期限不容許，只能另批准較短的探索性研究，不稱確認性優勢實驗。

來源故障不替換日期、不延長至得到顯著結果。若開發階段需修改builder／Label／QA規格，保存失敗與變更，用新protocol/new D0再規劃；已見日期不能重新宣稱未見確認資料。若D48前未完成鎖定，取消原Confirmation日曆，正式重新批准未來日期；不可把已蒐集且可能被看過的日期悄悄保留為確認集。

## 10. Temporal Split Protocol

**DESIGN**：全部模型共享相同 Train／Validation／Confirmation IDs、label、raw lineage及特徵順序。split按預定UTC日期，不能random shuffle。舊2026-08-26資料只作歷史背景，不混入新Train或樣本數估計。

主要試驗只fit一次固定Train模型，再評估Validation及未來Confirmation；不在確認日期滾動加入標籤、不以Validation最佳模型取代四個指定模型。若日後研究rolling retrain，另立protocol；此處估計的是固定模型隨時間推進的表現，包括模型老化風險。

抽樣先封存metadata IDs，後統計labels：
- Train：14日所有Q1候選按 UTC event time、capture schedule ordinal、connection ordinal、receive_sequence、sample_id 排序；N=288，使用含首尾的 floor(i×(M−1)/(N−1)) 等距索引。自然類別，不依label重抽；須所有14日來源資格通過，M≥288。M不符停止，不換日期。
- Validation／Confirmation：每個固定2小時session各選192個Q1候選，同樣等距metadata索引；一天384列。先封存完整日期IDs，再由受控流程計算label。若session不足192，該日為missing，不借另一session補足。這是有限預算的事件分布抽樣，不保證時間均勻或市場代表性。
- 抽樣會受預先固定品質政策影響，明確報告每個Train日期/時段被選數量；不以「先ID後label」誤稱完全不受未來可用性選擇影響。
- 四個當下Book特徵lookback=0；不加入raw E、receive時間或未來特徵。每列feature可用時間至少是其訊息接收完成＋Book更新完成，不能把exchange E當當地可下單時間。
- 所有Train實際endpoint必須嚴格早於split end；後一split開頭另作1001ms embargo。session/source/segment/date邊界亦檢查；7日確認前空檔是額外研究隔離，不替代逐列purge。
- 不僅比sample_id；以venue/symbol、U/u、canonical raw payload digest、capture lineage比對跨split市場事件。重複連線可能看到同一事件，不能把UUID不同當新樣本。
- 相同市場事件若內容相同，原始副本全保留，分析只留預定capture schedule ordinal較早者；不以延遲最快／模型較好者挑選。同ID內容不同則隔離所有相關衝突列。partial overlaps不能只憑U/u相似就任意合併。
- 重疊標籤群、capture和日期都記cluster IDs；減少重疊不代表剩餘樣本IID。

**缺類別**：提案Train三類各至少5筆才能進入主要三類比較；不足則 INSUFFICIENT_TRAIN_CLASS_SUPPORT、保存原IDs、不重抽、不更改權重。少於2類更是SVC執行阻擋。5是工程與解釋門檻，不是少數類學習充分樣本數證明。Validation／Confirmation缺少某類不刪日、不補抽；按第12節報不可估Recall及coverage，必要時只作描述。

## 11. Model Comparison Protocol

| 模型 | 固定設定（DESIGN，延續封存比較） |
|---|---|
| RBF-SVM／None | C=100、gamma=.01、class_weight=None、probability=False、random_state=42 |
| RBF-SVM／balanced | 相同設定，class_weight=balanced |
| QSVC／None | C=100、class_weight=None、4 qubits、ZZ feature map、linear、reps=1、alpha=2、FidelityStatevectorKernel、shots=None、enforce_psd=False、probability=False、random_state=42 |
| QSVC／balanced | 相同設定，class_weight=balanced |
| Majority-Class | 只用封存Train計數決定最多類；tie以DOWN、FLAT、UP固定順序；確認期間不更新 |

Majority-Class不同於歷史always-FLAT，明列為本次預先定義的baseline變更，不假裝相同實驗。None實際每類權重1；balanced用 n/(K×n_class)，三類存在時K=3；各模型記錄實際weights與SVC設定。禁止在本研究搜尋C/gamma/reps、另挑seed或挑最佳權重政策。底層tol、shrinking、cache_size、max_iter、decision_function_shape、break_ties、特徵映射參數順序等完整resolved設定，在人工fixture Gate固定並寫manifest；不能默默依新套件預設變動。既有環境僅唯讀使用，版本若不同於封存依賴則停止作相容性審核，不自行升級。

**Train-only preprocessing**：每個預定實驗的scaler只fit該Train288。沿用[封存公式](/home/jason/quantum-hft/artifacts/phase4b0/20261030T020400Z/preprocessing_protocol.json)：
z=(x−Train_mean)/Train_population_std；
theta=π×clip((z−z_Train_min)/(z_Train_max−z_Train_min),0,1)。
constant feature→π/2，保存constant mask；非finite直接Gate失敗，不silent imputation/drop。float64；四特徵順序 obi_5、spread_bps、bid_volume_5、ask_volume_5。量volume是top5數量總和，OBI=(bid_volume−ask_volume)/(bid_volume+ask_volume)，spread_bps=10000×(best_ask−best_bid)/mid。schema鎖定單位與價格數量數值解析。

四模型共享同一theta矩陣；Validation／Confirmation只transform，報below/above clip、常數、新range越界與periodicity診斷，不根據其結果修scaler。若日後有多Train folds，各fold各自fit，不共享未來fold的scaler。本次主要研究只有一個Train模型組。

相同C不等於相同有效正則化；kernel的譜、尺度及幾何不同。這是固定設定與固定樣本的受控比較，不是兩種模型各自充分最佳化後的最強對決。有限小Train亦限制結論，不能宣稱任何QSVC方法普遍無效或有效。

**Kernel一致性與預算**：
- Train最多288；每天evaluation384；Validation28日、Confirmation最多84日。
- 單次上限 n²＋n×384×112=12,469,248 個matrix entries；首次與獨立repeat合計24,938,496，上限25,000,000。這是pair entries的預算，不是QPU shots或實際API evaluate次數。稀疏缺日不以新日期填滿。
- 對同一Train的兩種class_weight可以共用核；cache key必含code/config/scaler/feature-order/Train與eval ID順序/input bytes/matrix SHA。QSVC仍須走可證明等價的正式QSVC kernel介面，不能無聲換成另一模型。
- 首次與repeat分開保存；repeat重新生成相同statevectors／matrices，實際工作計數記錄，不能把讀cache當獨立數值repeat。可預先限制保留矩陣與批次記憶體（提案peak RSS≤8GiB、整個固定比較牆鐘上限24h）；超預算停下報 RESOURCE_BLOCKED，不事後砍難樣本或只保留勝出模型。
- 對Quantum/RBF保存矩陣shape、symmetry、diagonal、finite、PSD eigenvalues、condition、effective rank。Kernel容忍度、有效rank公式、condition零特徵值規則在人工數值fixtures鎖定；不得強制PSD投影掩蓋超容差異常。
- 本輪不計算任何正式矩陣，不執行成本benchmark。未來純人工dry-run可評估工程cap，但須另批准。

**完整成本**：相同機器、執行緒、版本、輸入與禁止並行干擾設定；按日期奇偶預先交替模型執行順序；記錄raw驗證、feature build、preprocessing fit/transform、statevector建立、Kernel entries/evaluate calls、solver fit、predict、I/O、cold total、warm/cache total、CPU time、wall time、peak RSS。共享成本同時報「單一模型獨立成本」及「共用pipeline成本」，不能讓QSVC忽略kernel或讓RBF重複計算兩次以塑造加速。
高階fit/predict operation UUID與底層nested trace分開計數，避免重演歷史predict數量歧義。報告simulation成本，不宣稱QPU成本或量子加速。

## 12. Statistical Analysis Plan

**DESIGN**：Primary Macro-F1固定三類labels=[0,1,2]、zero_division=0。每日期兩session的384列一起算Macro-F1，再日期等權平均；另報session層與event-pooled confusion供描述，不能交換estimand。四模型與baseline的accuracy、macro precision/recall、per-class precision/recall/F1、true/predicted counts、confusion matrix、class coverage均完整輸出。

某日期true support=0的類別Recall報 NOT_ESTIMABLE；不把0叫「辨識失敗」或1叫「辨識成功」。固定三類Macro-F1仍照預定規則計算並加coverage warning。BA明列兩欄：observed-class BA（軟體實際定義）與full-three-class BA（只在三類都有support時可比，否則NA）。不能把缺類日的兩類BA與三類BA無說明混比。

**相依性／不確定度**：
- 主要統計單位是UTC日期配對差，不是event數、同日Fold數、重複seed或repeat次數。
- 主要CI：paired calendar moving-block bootstrap，block長7曆日、B=10,000、seed=20261031；從原始曆日格點的全部連續7日窗口抽整塊，保留兩模型配對及NA格點，串接後截至原N日。每個replicate對可用日期差值取均值；95% percentile CI。主要H0比較依此近似CI是否含0，明示其近似性，不宣稱精確隨機化檢定。
- 預先報block長1與14敏感度，不從中選最有利結果。跨日與日內相依不因UTC午夜消失；session／日期身份不是IID證明。
- 主推論最低資格提案：至少56可用日期、按Confirmation起點分成的不重疊7日塊至少8個完整塊、可用日期≥排定數80%、每類合計true support≥20且分布至少10個日期。這些是審慎最低設計門檻，不是統計有效性的充分定理；56日設計任何缺日都因可用日不足56而只能降為描述，80%門檻不放寬此條件；84日設計才可能容忍部分缺日。
- 缺失日不刪除後壓縮日曆；bootstrap全NA replicate記不可估，不重抽以湊漂亮結果；比例>1%停止主推論。跨日不穩定、已知結構斷裂或區間對block選擇不穩健須揭露，不能以門檻通過宣稱統計保證。
- 主要估計條件化於預定QA合格日期；同時報所有排定日期missing流程。以Δ_date∈[−1,1]給缺日最壞範圍：[(sum_observed−missing)/N,(sum_observed+missing)/N]，與抽樣CI分開，不將其當CI。不能從合格日直接外推所有計畫日期。
- 少數類別Recall不做event-IID binomial精準推論；提供按日／session聚類的描述區間或標不足。一天只有數筆UP時，即使accuracy高也不代表少數類辨識可靠。
- 記錄模型間paired prediction changes與方向，不能用大量重疊event做獨立McNemar或t-test來誇大證據。

| 評估層級 | 可以怎麼稱呼 |
|---|---|
| Within-day validation | 同日內時間外推；只能探索，不能當跨日證據 |
| Cross-day validation | 日期不同但已看過／用於設計或反覆比較；仍探索性 |
| Cross-capture validation | 來源UUID/過程不同；須市場事件不重複，仍不自動統計獨立 |
| Prospective locked Confirmation | protocol/模型/IDs規則/分析先鎖，未見未來日期、獨立保管及一次批准批次評估；可作限定母體的確認比較 |
| True independent holdout evaluation | 相對所有選參與決策確實隔離、獨立審核存取紀錄；「未使用」不保證時間序列機率獨立，兩者要分開說 |

即使QSVC CI較好，最多支持「指定來源、時段、品質政策、固定模型與計算預算下的預測差異」。不等於量子演算法複雜度優勢、硬體優勢、跨交易所普適性或獲利；4-qubit classical statevector可被經典計算，僅比單一RBF不足以宣稱Quantum Advantage。

## 13. Sample-size／Power Planning

**FACT**：現有同日研究不能估計可靠日間變異。增加同日重疊列數無法補足獨立日期。以下是規劃方法，不是已完成power分析。

**DESIGN**：先在固定28日Validation/Planning取得每日paired d及缺失率，完全不查看Confirmation。獨立日期近似：
N_ind ≈ (1.96+.84)²×σ_d²/δ²。
δ=.02時，σ_d=.02/.05/.10約需8/49/196個獨立日期；未計相依、缺失與小樣本估計誤差，不能直接把8當足夠。

未來樣本規劃程式在人工fixture Gate鎖定：以planning日差制定變異的保守敏感度情境（28日僅約4週，不能宣稱此上界有可靠覆蓋率），calendar block生成零假設及δ位移情境；包含7/14日相依、實際QA缺測與預定保守缺測情境，至少10,000模擬。方法、bounded score處置、seed、CI與size檢查先定。若pilot本身太少、各類不足或非平穩，標 POWER_NOT_ESTABLISHED；不得將小估計方差或同日Fold當可靠證據。

選擇規則：在{56,84}曆日中取能以第12節既定calendar-block CI／決策流程在預定保守情境達模擬power≥.80、且虛無size可接受的最小N（不是以IID公式直接宣布power），完整參數/模擬報告於Confirmation開始前由教授審核；沒有合格N則停止確認性主張，或另批准新的更大資源protocol。不能默默使用84並宣稱足夠，不得用Confirmation interim分數更新N。選定後不因p-value續收、停止或改主要對比。

Train288／eval384是計算預算選擇，不是統計power結論；少數類別集中及source QA可能使其不足。若pilot顯示需要增加樣本，須在Confirmation尚未開始前另版本鎖定資料／預算／模型比較，前版完整保留；不能藉此重新抽到理想labels。所有確認日期結束後才能一次解封評估。

## 14. Reproducibility and Integrity Plan

**DESIGN**：階段權限隔離如下；箭頭不是自動啟動。

Development Area → Pre-registration Lock → Data Capture → Raw Validation → Dataset Build → Model Experiment → Independent Review

Development只人工fixtures。預註冊lock包含文件/code/schema/settings/官方文件版本及manifest SHA，鎖後正式run不可修補重跑；錯誤另new run_id，先保存FAIL/BLOCKED與trace。Unique run_id採UTC YYYYMMDDTHHMMSSZ，若撞名等到新UTC秒，不重用；exclusive create、O_NOFOLLOW/實際路徑驗證、防symlink/../空路徑，output名稱由單一owner負責。

未來每個run只讀明列inputs，寫新run-root；TMPDIR/TEMP/TMP於child啟動前設私有0700，禁pycache外寫。Supervisor顯式--run-dir，schema/phase identity/cwd/env先驗；真正Supervisor→Child→discovery→worker→結果→seal的人工E2E先通過，不能只測child。全部必要測試實際探索/執行，0未批准skip；失敗不產生PASS。

Capture worker只存raw；Reference worker只讀明列raw；比較器才看兩套outputs；Market Loader不能解析AGENTS/任意檔，Integrity worker只回SHA/size/status；一般Python子程序/audit hook不宣稱OS等級隔離。Confirmation保管區需要實際OS權限或獨立帳戶及可稽核存取控制；未實作前標 UNKNOWN，不把寫在文件的LOCKED當已落實。

品質custodian可在固定無模型流程處理Confirmation raw與labels，但研究者不能看到feature values、labels、predictions、score；只收到預先限定的capture/QA計數與失敗狀態。模型snapshot、preprocessing、分析程式與input IDs規則全部先lock。一次批准解封後所有指定模型與baseline批次執行，完整輸出，不能只報winner。看到確認分數後改模型／篩選／統計方法，該批轉探索性；不能再稱未使用Confirmation。

每筆sample ID由canonical metadata（schema/protocol/source/session/segment/current raw identity）產生；不要用label值決定ID。raw bytes SHA與canonical parsed SHA分存；canonical JSON固定UTF-8、排序與數字字串規則。Manifest不能包含自己的SHA造成循環；獨立seal記其SHA。檔案不可變、保留first/repeat/失敗；hash證明完整性，不取代來源真實性或讀權限。

舊Dataset v1、Frozen、HFT、兩venv、Test及Final Holdout完全不納入新設計的可寫清單；未來網路資料應寫獨立新增capture storage，位置/容量須另批准，不把既有HFT原始資料複製到此專案。本次僅新增文件與manifest，沒有完整性全量重跑需求。

## 15. Research Risks

| 風險 | 預定處置／不可宣稱 |
|---|---|
| 官方bootstrap邊界語句不一致 | OPEN-API-01正式capture前人工裁定；離線同時測相鄰邊界；不能默認 |
| 有限Snapshot與缺包 | 深度內界證明、U/u連續性、無silent drop；不能稱全市場Book |
| 使用E建label與當地可用時間差 | 保存receive/process clocks；offline exchange-time題目，不是可交易訊號 |
| Snapshot初始state對早期event時間含義 | 暖機/銜接前不產生樣本；沒有snapshot exchange-time則UNKNOWN |
| 全部來自單交易所及固定時段 | 主張限於該範圍，不擴張到全日／所有資產 |
| 品質篩選與match≤1ms選擇 | 全分母ledger、Q0/Q1/Q2、時段與缺日敏感度；不依模型改門檻 |
| 少數類別、模型老化、反覆Validation | 固定Train support Gate、自然抽樣、不回流Confirmation、完整負結果 |
| 日依賴、週期／制度變化 | calendar block、不確定度與power限制；不保證任何固定天數充分 |
| 四維低qubit可經典模擬 | 報研究比較與成本，不能由分數宣稱量子加速 |
| 多實作共享規格偏誤 | 手算oracle、不同核心演算法、破壞A不影響B的負向測試 |
| Python guards非OS防護 | 明列邊界，實際隔離另驗，不做過度安全宣稱 |
| 長期capture容量、API規範變動 | 網路Gate前鎖文件/資源，超限停止，不偷偷降低raw保真度 |
| 工程PASS誤當科學成功 | 工程、來源、推論資格及研究結果分開status，分數不決定PASS |

## 16. Competition Deliverable Plan

**DESIGN**：可提交一篇誠實的「原始訂單簿可追溯驗證與固定量子核跨日比較」研究，負面結果同樣有價值。交付原始來源契約、雙重重建與oracle測試證據、不可變lineage、公開可重現人工fixtures、完整五模型／各日期／不確定度／成本報告、失敗紀錄與限制。

| 擬議主張 | 最低證據 |
|---|---|
| 原始資料可追溯、Label RAW-INDEPENDENT | 真實Capture manifest＋原始Snapshot/Diff＋兩套重建＋手算oracle＋逐列lineage＋零未解mismatch |
| 跨日受控比較完成 | 先鎖日期/模型/樣本規則、自然分布、同IDs/labels/preprocessing、全部日期及missing流程 |
| 確認性預測差異 | 未污染Confirmation、統計資格與方法假設、主要配對CI、限制範圍；不靠單一最高Macro-F1 |
| 可重現工程 | 冷啟動E2E、first/repeat、trace、完整input/output/code/env SHA、獨立審查 |
| Quantum Advantage／交易盈利 | 本設計不足以支持；不得提出 |

論文附錄公開protocol版本差異與偏離表；若授權不允許公開原始市場資料，提供schema、人工資料及可核對SHA，分享權限另由人工決定。競賽規則/資料授權尚未核對，標 UNKNOWN，不推定已合規或需上傳任何資料。

## 17. Phase Execution Roadmap

| 次序（均須另批准） | 範圍 | 最小驗收與停止點 |
|---|---|---|
| E0：離線契約與人工oracle Gate | 新schema、明確CLI、Snapshot/Diff純狀態機、雙Reference、下列fixture矩陣；禁止網路／市場CSV／模型 | 正常/錯誤皆有預期結果；所有測試實際執行0error/fail/未准skip；權限、exclusive output、true Supervisor E2E PASS；封存code/config/trace後停止 |
| E1：Capture實作／安全預檢 | 依核准契約實作但預設不能連網；mock transport、fault injection、容量與退避 | 無自啟daemon；寫入失敗可追溯；OPEN-API-01已解；教授批准才進網路 |
| E2：限定capture pilot與raw資格 | 另外的明確網路授權、固定時窗、小範圍capture；不模型 | 真實Snapshot/Diff/UUID/時鐘/來源鏈可重建；不得直接當未污染Confirmation |
| E3：正式前瞻日曆／Dataset build | 日期與QA鎖定後收集Train/Validation；雙Reference獨立驗證 | 新Dataset版本與所有排除ledger，raw-to-label PASS，舊資料完全不變 |
| E4：固定探索性模型與power規劃 | 僅已批准Train/Validation，固定四模型＋baseline | train-only scaler、成本及kernel檢查、日差不確定度、Confirmation N/分析code鎖定；不開舊Holdout |
| E5：Confirmation封存與一次批次評估 | 分開批准capture與解封評估，無中途選參 | 全日曆完成、品質/類別/統計資格、完整結果，不據分數續收 |
| E6：獨立審查／競賽稿 | 獨立重算指標、lineage與主張 | 工程證據與科學結論分開，人工審核後才決定下一研究 |

**Codex Sol High 分工（工程建議，不是本輪派工授權）**：
適合處理規格明確的schema validator、獨立模組、人工fixtures、CLI/manifest/read-write guards、trace、hash與報告生成；每次小範圍、先review再E2E。A/B Reference分開開發後獨立review，避免共用核心缺陷；不能讓同一自動流程自我批准來源或統計結論。
教授／研究者負責estimand、δ、資源與power折衷、來源資格的科學合理性、確認資料解封與論文主張。
OpenAI官方列GPT-6.1 Sol適用複雜程式工作且支援high reasoning；您所稱「Codex Sol High」的確切UI模型ID仍需在實際派工時記錄，不自行替換或聲稱某型號必然更正確。[官方模型資料](https://developers.openai.com/api/docs/models/gpt-6.1-sol)

## 18. Explicit Approval Gates

本文件完成後立即停止。已有授權僅本次設計／文件；以下不是默認批准：

| Gate | 人工需要決定／驗收 |
|---|---|
| G0：研究方向 | 主比較balanced對balanced、日期等權Macro-F1、δ=.02、固定模型老化的estimand；負結果可接受 |
| G1：離線工程 | E0的新增目錄/檔案與fixture範圍；不得碰市場值、網路、HFT/venv或正式模型 |
| G2：來源／網路 | OPEN-API-01、官方文件固定版本、API限流/重連、儲存容量/保留、time sampling、真實來源與network allowlist |
| G3：日期／品質／預算 | 14/28/7/56或84日方案；每日00/12UTC兩2小時；QA95%、Train288/Eval384、類別門檻、成本25Mentries/8GiB/24h、沒有好日替補 |
| G4：主要預註冊鎖定 | exact日期、protocol/code/schema SHA、統計/樣本規劃可執行規格、所有UNKNOWN阻擋項處置；不得靠文件文字冒稱LOCK已執行 |
| G5：模型授權 | 新Dataset raw驗證PASS、Train/Validation只讀授權；沒有Test/舊Holdout權限 |
| G6：確認集 | N與分析程式已鎖，實際保管權限通過、日期完成、獨立reviewer同意一次評估；QA人與模型人職責分開 |
| G7：結論／下一階段 | 完整結果與偏離表由人工核准；不自動進QAOA/QUBO/交易或新的參數搜尋 |

**本次審核結論**：具備提出E0離線人工fixture工程的條件；尚不具備啟動正式Capture或確認性模型實驗的全部條件。教授須決定G0/G3及確認資料保管人；API bootstrap邊界、正式資料格式實作、雙Reference、power、storage與權限隔離尚待驗收。現在訓練只能重複已看過的單日問題；開舊Holdout既不解決raw來源缺口，也會消耗尚未使用的評估證據。

### 附錄 A：人工 fixture 驗收清單（規劃，不曾執行）

每個ID須至少一個獨立可執行案例、預期輸出與失敗證據；必要時拆多案例，實際測試數以discovery manifest為準，不以清單長度冒充tests PASS。

| ID | 人工情境／必須觀察的結果 |
|---|---|
| F01 | Snapshot太舊：拒絕、保存重試，不產生有效Book |
| F02 | Bootstrap U=L且u>L：正常銜接與手算結果相符 |
| F03 | Bootstrap U=L+1：依OPEN-API-01鎖定選擇；未解時不得接受 |
| F04 | U=L+2：缺口、舊區段失效、需新Snapshot |
| F05 | Snapshot太新／buffer全過時：等待銜接或timeout，不造樣本 |
| F06 | LIVE連續、重疊range、已過時、u=local_u：分別依契約處置 |
| F07 | 同ID同payload重複與不同payload衝突：不重複樣本／隔離 |
| F08 | 新價位、覆寫數量、零量刪除、刪不存在價位：手算Book |
| F09 | 負價格/負量/NaN/Inf/錯型別/缺key/U>u：fail closed |
| F10 | 更新內部暫時crossed但完成正常：只檢查原子事件完成狀態 |
| F11 | 完成後crossed/locked/空側/不足五檔：無效及resync |
| F12 | 容器有五檔但越過Snapshot深度內界：不得宣稱top5完整 |
| F13 | 重複E不同update：保持事件順序，不按時間去重 |
| F14 | E倒退：切段，禁止跨倒退Label |
| F15 | wall clock跳變、monotonic正常：保存clock anomaly，不稱網路延遲 |
| F16 | 重連/boot改變/換檔：UUID與邊界有效、不能跨檔Label |
| F17 | 1000/1001/1002ms endpoint：前兩者Q1、最後match invalid |
| F18 | 相同future E兩個不同事件：選原始順序第一個 |
| F19 | 第一future無效但下一個有效：不得跳到後者修飾Label |
| F20 | Session/file/segment/split tail與1001ms embargo：逐界拒絕 |
| F21 | Endpoint自身沒有下一個Label但當下Book有效：前列Label可有效 |
| F22 | 相鄰E inactivity差1000/1001：依新gap政策處置，不混淆horizon |
| F23 | 正/負/零/極小return、Decimal50 rounding邊界及全域context污染 |
| F24 | A用two-pointer、B用lower-bound：手算endpoint完全一致 |
| F25 | 破壞A衍生mid/target/label：B不變、comparison必敗 |
| F26 | 破壞raw byte/Snapshot/order/UUID/chunk/hash：整體Gate不得PASS |
| F27 | 冷啟動replay：相同book、IDs、invalid flags與Label SHA |
| F28 | Train-only scaler：人工未來極值不得改Train參數；constant角π/2 |
| F29 | 相同Train/Eval IDs、feature order與標籤摘要：任一錯位拒絕 |
| F30 | 缺Train類、缺Evaluation類：停止／NA與warning正確，不抽樣補類 |
| F31 | Majority tie、balanced實際weights：小表手算oracle，不fit模型 |
| F32 | 三類Macro-F1、缺類BA、confusion metrics：人工predictions手算 |
| F33 | 日block bootstrap保留配對/NA/日曆；不得把缺日壓縮或event當IID |
| F34 | 預算上限、cache key錯序/錯scaler：拒絕重用，不能偷偷換QSVC |
| F35 | --run-dir缺/空/舊/symlink/逃逸：啟動前清楚錯誤、不猜路徑 |
| F36 | 真Supervisor→Child→discovery→安全→opaque worker→seal成功 |
| F37 | Child啟動失敗/nonzero/test failure/import error：完整trace、無假PASS |
| F38 | 私有TMPDIR、UNIT_WRITE_SCOPE、限定/dev/null：越界寫入不成功 |
| F39 | Market Loader與opaque integrity分權；Test/Holdout/AGENTS解析拒絕 |
| F40 | 舊artifact不可覆寫；report owner無名稱衝突；seal不得蓋舊FAIL |
| F41 | mock網路／排程：沒有授權時不能連線、自啟或使用真API |
| F42 | queue/disk持久化失敗、Snapshot重試耗盡：session失敗可追溯 |
| F43 | Confirmation未批准：feature/labels/predictions及score均無法解封 |
| F44 | 同市場事件跨capture/split重複、內容衝突：以raw lineage處置 |
| F45 | 品質前後分母/Q0/Q1/Q2/tail ledger：不能靠刪列使mismatch消失 |
| F46 | 開發重試與正式不可重試：新run保留首次失敗，鎖後不改程式 |

### 附錄 B：官方來源與尚未鎖定事項

官方文件查閱日2026-10-31；本輪只保存連結與核對摘要，沒有宣稱已封存第三方頁面完整bytes／commit。正式實作前須封存允許範圍內的確切官方規格版本與SHA，若文件改動則重新審核；目前官方文件revision pin=PENDING。

- [Binance官方GitHub：Diff Depth與Book同步](https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md)
- [Binance官方：Spot Stream欄位](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-streams/~)
- [Binance官方：REST Snapshot](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market)
- [OpenAI官方：GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)

API真實行為、磁碟需求、跨日變異、power、兩套程式一致性、確認區權限與新模型效果目前均未執行驗證。讀官方文件不等於行情連線，本輪不得被記錄為「完全無網路」。
