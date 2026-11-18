# 資料集唯讀稽核

Run: `phase1v2_20261018T210029Z_replay_snapshot_1000`

整體狀態：**PASS**

PASS＝已檢查且未發現違規；WARNING＝需解釋的觀測；FAIL＝格式或一致性違規；NOT AVAILABLE＝沒有可檢查的有效證據。

輸入僅供讀取。CSV／JSONL 串流解析；保存時間戳與更新 ID 區間集合以偵測全檔重複，不保存完整 payload。Snapshot 作為一份 JSON 文件載入。

| 檔案 | 類型 | 狀態 | 筆數 | 解析錯誤 | Bytes |
|---|---|---|---:|---:|---:|
| results/replay_snapshot_1000.json | snapshot | PASS | 1 | 0 | 560071 |

## results/replay_snapshot_1000.json

SHA-256: `ee4bd68eac23fb8277d6842e9212100b27a9cbe32785f6b907f891fcdeaa5ada`

| 檢查 | 狀態 | 異常數 | 可檢查觀測數 |
|---|---|---:|---:|
| parse_errors | PASS | 0 | 1 |
| event_schema | PASS | 0 | 1 |
| last_update_id | PASS | 0 | 1 |
| bids_schema | PASS | 0 | 1 |
| asks_schema | PASS | 0 | 1 |
| price_quantity_valid | PASS | 0 | 10000 |
| bid_sort | PASS | 0 | 1 |
| ask_sort | PASS | 0 | 1 |
| uncrossed_book | PASS | 0 | 1 |

指標：

```json
{
  "lastUpdateId": 100405424366,
  "bids_levels": 5000,
  "asks_levels": 5000,
  "physical_lines": 40007
}
```

## Snapshot／Replay 銜接

NOT AVAILABLE：未明確指定 --pair，不以檔名推定配對。

## 解讀限制

- CSV 本機時間尚未證明為 WebSocket 接收時間。local−event 為負記為 WARNING，不能解讀為負的網路延遲。
- CSV 數值一致性使用 Decimal 與絕對容忍誤差 1e-8；總量為零時使用 OBI=0，符合既有公式。
- Snapshot quantity 必須為正；Replay quantity=0 是合法刪單更新，另外計數。
- 重複事件指相同 (firstUpdateId, finalUpdateId)，包含非相鄰重複。Gap 使用不下降的 high-water ID。
- errors.csv 保留全部異常；JSON 每項最多保留 20 個樣本。稽核不證明經濟有效性、交易所來源或獲利。
