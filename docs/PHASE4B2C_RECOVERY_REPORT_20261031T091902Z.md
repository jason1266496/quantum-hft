# Phase 4B-2C Recovery-1：Strict Spot Schema Validation
狀態：**PHASE 4B-2C RECOVERY GATE PASS**。run_id：20261031T091902Z。
此結論僅是Schema修復Recovery Gate，不是原Phase4B2C全46類PASS或正式Capture可上線。

## 根因與範圍
舊schema.py:7-24僅迴圈確認required keys，沒有未知欄位拒絕；:29的additionalProperties=false只是輸出宣告，未由validator執行。含pu人工反例已在修補前重現。沒有發現驗證前自動刪key；也沒有證據顯示已實作Futures模型。COMMON與E/U/u/b/a混在舊物件，缺少e/s欄位；舊child.py:21直接呼叫A/B，正式人工入口未強制先驗證。pu被接受未拋例外，因此原始證據是schema_contract_audit及fixture，不虛構原始Python traceback。
本次只在新開發區修復：spot_strict_synthetic_v2明確區分Spot Diff(e/E/s/U/u/b/a)、Snapshot(lastUpdateId/bids/asks)、Envelope(metadata+payload_kind+payload)，未知欄位立即拒絕。缺欄與未知欄分開錯誤，含fixture ID/path/fields；巢狀結構、十進位字串、價格數量、UUID與U<=u驗證。同步/缺口邏輯保持在原Reference，不塞入型別驗證。
pipeline.process先驗證整批輸入再呼叫A/B。最後一筆事件非法時，兩套spy核心均呼叫0次、不產生Label。外層schema_failure Child的完整trace保存在獨立開發負向run，沒有ready或oracle假PASS。
原35項測試與fixtures/ORACLE、reference_a.py、reference_b.py逐byte SHA不變。為保留舊人工fixture，from_legacy_fixture只接受SYNTHETIC_ONLY及exact舊shape，顯式加入人工e/s後交strict validator；不把舊merged格式當正式raw payload，也不silent dropping。兩個低階core函式本身仍可直接呼叫，不宣稱它們是OS安全邊界。

## 測試與啟動驗收
開發與正式各35/35原Regression、30/30新增Schema測試，0failure/error/skip。新增包含pu、未知/Futures T、缺e/E/U/u、bool/float ID、U>u、b/a型別、非法decimal、Snapshot/Diff互混、未知巢狀、Envelope混淆、拒絕後A/B不執行、完整異常與零有效Label、合法oracle不變等。
開發真Supervisor→Child→Strict Validator→A/B→Oracle→opaque worker完成；原9項E2E情境重驗，另加Schema拒絕整鏈，10/10。所有command argv/cwd/stdout/stderr/exit保留。正式使用相同implementation SHA、相同--run-dir與私有TMPDIR介面，僅root/run_dir與預先定義fault配置差異；正式exit0，無同run修補重跑。
手算oracle不變：100到100.5、1000ms、50bps、UP2。新process的開發與正式首次/重建repeat一致；不冒稱真市場raw cold replay已驗證。

## Coverage與完整性
保留原46類Matrix完整副本。只F09 FAIL→PASS；目前{"PASS": 20, "FAIL": 0, "PARTIAL": 16, "NOT_EXECUTED": 10}。PARTIAL/NOT_EXECUTED沒有自動升級。尚未完成的模型/統計、故障注入、raw replay、跨capture/quality等仍保留。
原BLOCKED 45個artifact逐檔SHA/大小、completion SHA、報告SHA均前後一致。現有Dataset/Frozen/兩venv等20,393筆記錄只lstat，identity前後一致；沒有fresh內容checksum，不將其標全面完整性PASS，也不能排除維持mtime的內容修改。原A/B、oracle與35測試SHA一致。opaque worker只檢人工文件。

## 官方規格與安全界線
DOCUMENTATION_VERSION_GAP：本輪不使用網路，僅依使用者明列7欄與既有封存官方摘要核對。官方完整revision尚未鎖定，Snapshot bootstrap OPEN-API-01仍待人工裁定；未擴充正式網路／同步規格。C++ production A亦未實作，仍為Python原型。這些不被Schema Recovery PASS自動消除。
Test/Final Holdout未開內容、未評估；Final Holdout LOCKED。無市場連線、QPU、模型fit/predict、Quantum Kernel、QAOA/QUBO、交易/回測/Paper/Testnet、套件變更或下階段啟動。負向DNS案例由hook在解析前拒絕；不宣稱量測全機流量。UNIT_WRITE_SCOPE延續，未關閉或擴大既有guard。

## 後續
具備提交人工審核、恢復Phase4B2C剩餘離線驗收的條件；須另批准範圍。未具備全46類、官方版本與production Capture完整驗收條件。保留原BLOCKED，不回寫PASS。本輪完成後停止，不啟動資料擷取。
