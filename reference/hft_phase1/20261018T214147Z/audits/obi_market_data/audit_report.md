# 資料集唯讀稽核

Run: `phase1v2_20261018T210029Z_obi_market_data`

整體狀態：**WARNING**

PASS＝已檢查且未發現違規；WARNING＝需解釋的觀測；FAIL＝格式或一致性違規；NOT AVAILABLE＝沒有可檢查的有效證據。

輸入僅供讀取。CSV／JSONL 串流解析；保存時間戳與更新 ID 區間集合以偵測全檔重複，不保存完整 payload。Snapshot 作為一份 JSON 文件載入。

| 檔案 | 類型 | 狀態 | 筆數 | 解析錯誤 | Bytes |
|---|---|---|---:|---:|---:|
| results/obi_market_data.csv | csv | WARNING | 49999 | 0 | 6683124 |

## results/obi_market_data.csv

SHA-256: `e71676d8d2d6c04e6cf9b4f80ef3eb113de78a92eff8a280fd633541ac8231e7`

| 檢查 | 狀態 | 異常數 | 可檢查觀測數 |
|---|---|---:|---:|
| required_columns | PASS | 0 | 1 |
| parse_errors | PASS | 0 | 49999 |
| missing_values | PASS | 0 | 499990 |
| non_finite_values | PASS | 0 | 499990 |
| invalid_numeric_values | PASS | 0 | 499990 |
| timestamp_schema | PASS | 0 | 99998 |
| update_id_schema | PASS | 0 | 49999 |
| event_time_monotonic | PASS | 0 | 49998 |
| duplicate_timestamps | PASS | 0 | 49999 |
| bid_positive | PASS | 0 | 49999 |
| ask_positive | PASS | 0 | 49999 |
| uncrossed_book | PASS | 0 | 49999 |
| spread_nonnegative | PASS | 0 | 49999 |
| mid_consistency | PASS | 0 | 49999 |
| spread_consistency | PASS | 0 | 49999 |
| volume_nonnegative | PASS | 0 | 99998 |
| obi_range | PASS | 0 | 49999 |
| obi_consistency | PASS | 0 | 49999 |
| local_event_clock_order | WARNING | 49999 | 49999 |

指標：

```json
{
  "first_event_time_ms": 1791238160414,
  "last_event_time_ms": 1791243186114,
  "columns": [
    "local_timestamp_us",
    "event_time_ms",
    "update_id",
    "best_bid",
    "best_ask",
    "mid_price",
    "spread",
    "bid_volume_5",
    "ask_volume_5",
    "obi_5"
  ],
  "min_event_time_ms": 1791238160414,
  "max_event_time_ms": 1791243186114,
  "local_minus_event_ms_min": "-375.662",
  "local_minus_event_ms_max": "-304.107",
  "max_obi_absolute_difference": "4.9999575165897716942E-9",
  "physical_lines": 50000,
  "unique_timestamps": 49999,
  "duplicate_timestamps": 0
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
