# 唯讀 Dataset Audit

`tools/dataset_audit.py` 以 Python 標準函式庫稽核明確指定的資料，不連接網路、不執行既有程式、不修改輸入。建議使用 Python 3.10 以上，以 `python3 -B` 避免產生 `__pycache__`。

## 使用方式

以下僅為執行範例；先完成人工資料測試，再由授權工作執行正式資料稽核。

```sh
python3 -B tools/dataset_audit.py \
  --csv results/obi_market_data_20260827_session1.csv \
  --pair results/replay_snapshot_1000.json results/replay_events_1000.jsonl \
  --run-id my_unique_run
```

- `--csv PATH`、`--replay PATH`、`--snapshot PATH`、`--pair SNAPSHOT REPLAY` 可重複指定。
- `--pair` 會自動納入對應輸入；不以檔名猜測配對。
- 預設輸出為 `artifacts/dataset_audit/<run_id>/`。省略 run ID 時以 UTC 時間加 UUID 產生唯一值；分析本身不使用隨機性。
- `--output-root` 必須解析到本專題 `artifacts/` 內；拒絕輸出路徑的符號連結／junction。run 目錄已存在即拒絕，報告檔使用 exclusive create。
- `--progress-every SECONDS` 設定進度頻率，預設一秒；每檔完成時固定顯示已處理筆數／估計總筆數、bytes 百分比、elapsed、ETA、parse errors。估計筆數以目前平均每筆 bytes 換算，並非事先完整掃描的精確筆數。
- 程式退出碼：`0` 表示完成且無 FAIL（仍可能有 WARNING 或 NOT AVAILABLE），`1` 表示完成但資料有 FAIL，`2` 表示參數、輸出安全或 I/O 錯誤。退出碼 0 不等於全部檢查 PASS。

## 輸出與穩定 schema

每次執行產生四份新檔案：

| 檔案 | 內容 |
|---|---|
| `audit_report.json` | schema 版本 `1.0`、run ID、總狀態、metadata、參數、逐檔稽核、Snapshot／Replay 配對 |
| `audit_report.md` | 易讀摘要、逐項狀態與檢查筆數、metrics、限制 |
| `files_manifest.json` | 每個輸入路徑、種類、檔案大小、實際讀取 bytes 的 SHA-256；環境與參數 |
| `errors.csv` | 每個異常的位置與說明，欄位為 `path,kind,line,record,check,status,message` |

`audit_report.json.files[]`：

```text
path, kind, status, sha256, size_bytes, records, parse_errors,
checks: {check_name: {status, count, checked, detail, samples}},
metrics: {...}
```

`count` 是該項異常次數，`checked` 是可執行該檢查的觀測次數；例如價量檢查可按 level 計數。缺欄位、不合法依賴、零筆資料等不能執行的檢查保留 `NOT AVAILABLE`。JSON 每項僅保留前 20 個異常樣本；`errors.csv` 保留全部異常，不截斷。

CSV 與 JSONL 的 `line` 指實體輸入行。Snapshot 是整份 JSON 解析，語意錯誤透過 `message` 中的側別／level index 定位；其 `line` 是讀取進度的最後一行，不是語意欄位的精確原始行號。JSON 語法錯誤的 parser 訊息另外包含行／列位置。不可將 Snapshot 的 `line` 欄誤當成完整 JSON source map。

`pairs[]`：`snapshot`、`replay`、`status`、`check`、`last_update_id`、`snapshot_valid`、`first_valid_event`、`first_candidate_event`、`sequence_only_alignment`、`payload_valid`、`skipped_events`、`detail`。

狀態優先序為 FAIL、WARNING、NOT AVAILABLE、PASS。只有存在可檢查觀測且沒有違規時，單項檢查才是 PASS；不把缺資料當作通過。

## 格式與判斷

- CSV 必需十欄：`local_timestamp_us,event_time_ms,update_id,best_bid,best_ask,mid_price,spread,bid_volume_5,ask_volume_5,obi_5`。逐筆檢查欄數、空值、非數值／非有限值、正價、crossed book、spread、mid、兩側總量及 OBI。
- CSV 數值使用 `Decimal`，mid／spread／OBI 絕對誤差容忍為 `1e-8`。總量皆零時 OBI 預期為零，與既有公式一致。update ID 與時間必須是非負整數字串。
- Replay 每行為 JSON object；ID 與 `eventTime` 必須為 JSON 整數，拒絕 bool、浮點數或字串。`bids`／`asks` 是 `[{"price": ..., "quantity": ...}]`，與現有 capture 格式相同；quantity=0 是有效刪單更新，另外計數。
- Snapshot 為一份 JSON object，包含整數 `lastUpdateId` 及 `[[price,quantity],...]` 兩側非空陣列。價格／數量須為正，bids 嚴格遞減、asks 嚴格遞增，最高 bid 必須小於最低 ask。
- JSON 使用精確十進位解析浮點值，拒絕重複 object key 及非標準 NaN／Infinity 常數。字串形式的非有限價量亦不合法。
- 重複事件以 `(firstUpdateId,finalUpdateId)` 識別，包含非相鄰重複；時間重複以整份 CSV 判斷。只保存 ID／時間集合，不保存完整 CSV／Replay payload。其額外記憶體仍隨唯一 ID／時間數量增加；Snapshot 作為一份 JSON 文件載入。
- Gap 判斷使用不下降的 finalUpdateId high-water，避免倒退事件重設基準而掩蓋後續缺口。相鄰合法區間可重疊，須覆蓋 high-water+1。
- 配對先略過 `u <= snapshot.lastUpdateId`。首個剩餘候選需符合 `U <= lastUpdateId+1 <= u` 且時間／價量 payload 合法；無符合候選為 NOT AVAILABLE，不會假定可銜接。另保存 ID-only 銜接結果，避免將格式錯誤誤報成完整通過。
- `first_event_time_ms`／`last_event_time_ms` 是檔案順序的首末有效時間，`min_event_time_ms`／`max_event_time_ms` 是全檔範圍。
- CSV local timestamp 不能當作已驗證的 WebSocket 接收時間。local−event 為負只記 WARNING；不把它解釋成網路負延遲。

## 可重現性與限制

記錄實際輸入 SHA-256、Git commit 或 unavailable 原因、Python／OS／機器架構／CPU 數／時區、UTC 執行時間、完整輸入與容忍參數。隨機種子記為不適用，因為稽核不使用隨機抽樣；自動 run ID 的 UUID 只用於避免命名衝突。

完整機器／編譯器環境另外保存於 `artifacts/environment/<run_id>/environment.json`。此稽核只驗證保存的資料，不能證明交易所來源、完整逐檔 order book、接收時鐘準確性、成交可行性或策略獲利。
