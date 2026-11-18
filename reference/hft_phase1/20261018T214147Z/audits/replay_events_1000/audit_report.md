# 資料集唯讀稽核

Run: `phase1v2_20261018T210029Z_replay_events_1000`

整體狀態：**PASS**

PASS＝已檢查且未發現違規；WARNING＝需解釋的觀測；FAIL＝格式或一致性違規；NOT AVAILABLE＝沒有可檢查的有效證據。

輸入僅供讀取。CSV／JSONL 串流解析；保存時間戳與更新 ID 區間集合以偵測全檔重複，不保存完整 payload。Snapshot 作為一份 JSON 文件載入。

| 檔案 | 類型 | 狀態 | 筆數 | 解析錯誤 | Bytes |
|---|---|---|---:|---:|---:|
| results/replay_events_1000.jsonl | replay | PASS | 1000 | 0 | 1176899 |

## results/replay_events_1000.jsonl

SHA-256: `26e5059e8a3448a93a72eb0ed9893be439941c039c54110edbc131cc6841b503`

| 檢查 | 狀態 | 異常數 | 可檢查觀測數 |
|---|---|---:|---:|
| parse_errors | PASS | 0 | 1000 |
| event_schema | PASS | 0 | 1000 |
| timestamp_schema | PASS | 0 | 1000 |
| event_time_monotonic | PASS | 0 | 999 |
| update_id_schema | PASS | 0 | 1000 |
| update_id_order | PASS | 0 | 1000 |
| update_id_gaps | PASS | 0 | 999 |
| duplicate_events | PASS | 0 | 1000 |
| backward_events | PASS | 0 | 999 |
| bids_schema | PASS | 0 | 1000 |
| asks_schema | PASS | 0 | 1000 |
| price_quantity_valid | PASS | 0 | 29915 |

指標：

```json
{
  "quantity_zero_updates": 11932,
  "first_event_time_ms": 1789974146914,
  "last_event_time_ms": 1789974246814,
  "min_event_time_ms": 1789974146914,
  "max_event_time_ms": 1789974246814,
  "bids_levels": 15885,
  "asks_levels": 14030,
  "first_firstUpdateId": 100405424367,
  "first_finalUpdateId": 100405424375,
  "last_firstUpdateId": 100405482957,
  "last_finalUpdateId": 100405482989,
  "high_water_finalUpdateId": 100405482989,
  "physical_lines": 1000,
  "unique_update_intervals": 1000,
  "update_id_gaps": 0,
  "duplicate_events": 0,
  "backward_events": 0
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
