# Phase 4B-2B Protocol Review
run_id：20261031T085529Z；日期：2026-10-31 Asia/Taipei。
結論：DESIGN_COMPLETE_PENDING_HUMAN_REVIEW；OFFLINE_FIXTURE_IMPLEMENTATION_ELIGIBLE_FOR_APPROVAL；CAPTURE_AND_MODEL_EXECUTION_NOT_AUTHORIZED。

本輪完成18章研究規格、11類資料契約與46類人工fixture規劃。這些數字不是已執行單元測試；本輪新fixture執行0、正式市場值讀取0、fit/predict/Quantum Kernel0、資料蒐集0。既有171 tests為封存歷史事實，不是本輪重跑。

## 審查方式與證據
先在 /home/jason/quantum-hft 核對 pwd/realpath、AGENTS.md、最新使用者附件。唯讀核對Phase4B2A completion SHA、選定8份封存摘要、正式報告，以及Phase4B0模型/前處理契約；另確認Phase4B0 completion SHA。只對明列文件做SHA，未對市場CSV或venv重跑全量驗證。完整工具命令及結果保留於本次對話工具紀錄；新增文件的驗收另記completion manifest。
兩個同任務審查子代理分別提供統計與raw-reference設計審查，僅設計建議，未寫檔、未讀市場值；這不是教授批准或外部同儕審查。
以OpenAI Docs核對Codex Sol High分工建議的官方產品資訊；查閱Binance官方文件以驗證API規格，沒有執行其範例網路命令。官方網站／GitHub查閱使用網路，不宣稱離線。

## 已納入的審查修正
1. RAW-INDEPENDENT限於可追溯封存原始訊息及獨立重建，不能由SHA直接證明交易所真實性。
2. Snapshot有限深度需證明top5處在已知內界；容器有五檔不足。
3. 保留官方bootstrap邊界文字問題OPEN-API-01，不把LIVE的+1通則偷偷當已確認bootstrap。
4. 新品質政策不要求endpoint還能形成它自己的未來Label，避免再產生歷史額外witness選擇。
5. Reference A/B核心不得共用；需手算oracle與破壞A輸出不影響B的測試。
6. 主要對比只有balanced QSVC−balanced RBF、雙側且接受負結果；相同C不是相同有效正則化。
7. 主estimand限於品質合格且可評估日期；完整計畫日期的缺測最壞範圍是識別界，不是CI。
8. 56日計畫任何缺日都會失去最低推論資格；84日才可容忍部分缺日。最低門檻不保證IID或推論有效。
9. Power必須以既定block分析流程模擬；28日planning僅4週，變異上界是敏感度假設，不能偽稱可靠估計。
10. Majority-Class由Train決定，和舊always-FLAT不同；完整日期、coverage、BA缺類語義及成本均事先規定。
11. Bootstrap保留日曆NA、整塊配對、不把重疊event當IID；確認資料一次解封，不看分數續收。

## 教授需要決定
- 是否接受主要estimand、唯一主要對比、δ=.02與80%模擬power目標；不顯著不等效。
- 是否能支持14日Train＋28日Planning＋7日隔離＋56/84日Confirmation的資源；不足可做探索性研究，不能降格門檻後仍宣稱同等證據。
- Train288、eval384/day、每類Train至少5、推論至少56可用日及少數類支持門檻的取捨。
- QA95%／match≤1ms／gap>1000ms與top5覆蓋政策是否適合主要研究母體；不是歷史設定的默認延伸。
- 確認資料custodian、實際存取權限與一次評估的獨立批准人。
- 官方bootstrap邊界裁定與網路／儲存資源批准責任。正式擷取前必須有版本鎖定證據。

## 可交給Codex Sol High的工程
僅在另獲批准後實作schema、純函式Book狀態機、獨立Reference、人工oracle、CLI與Supervisor E2E、read/write guard、trace、immutable manifest、指標與calendar-block測試。確切模型ID與reasoning設定須記錄；人工負責科學取捨與驗收，不能由Codex自行批准研究。

## 下一個最小驗收階段
E0「離線Capture契約與雙Reference人工fixture Gate」：
新Development Area、禁止網路、禁止正式市場值、禁止模型；完成F01–F46對應案例（實際數以discovery為準），0fail/error/未批准skip；直接測真正Supervisor父子鏈，保存首次失敗、獨立重試、完整trace；seal後停止。
OPEN-API-01未解時只測其拒絕行為，不能藉fixture PASS推論已可正式擷取。

## 尚未具備的條件
確切API revision與bootstrap裁定、raw recorder/雙Reference實作及實測、真實跨日來源、容量與權限隔離、可靠power、Confirmation實際保管均未驗收。未來如需修改提案，新增版本保存差異，不能改本次檔案。
立即訓練只會重複已探索單日資料；開舊Holdout既不能修補原始來源與跨日缺口，也會消耗未使用評估資源。維持Test未使用、Final Holdout LOCKED。

本輪停於文件與審查；不啟動E0、資料擷取、Dataset建置、訓練、QAOA/QUBO或交易。
