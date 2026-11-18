# 資料集唯讀稽核

Run: `phase1v2_20261018T210029Z_obi_market_data_test_20260827`

整體狀態：**WARNING**

PASS＝已檢查且未發現違規；WARNING＝需解釋的觀測；FAIL＝格式或一致性違規；NOT AVAILABLE＝沒有可檢查的有效證據。

輸入僅供讀取。CSV／JSONL 串流解析；保存時間戳與更新 ID 區間集合以偵測全檔重複，不保存完整 payload。Snapshot 作為一份 JSON 文件載入。

| 檔案 | 類型 | 狀態 | 筆數 | 解析錯誤 | Bytes |
|---|---|---|---:|---:|---:|
| results/obi_market_data_test_20260827.csv | csv | WARNING | 951 | 0 | 126181 |

## results/obi_market_data_test_20260827.csv

SHA-256: `aa9bb47e598aaa024640c079654ed17da1e70552ed06632361dc4cb607b8171f`

| 檢查 | 狀態 | 異常數 | 可檢查觀測數 |
|---|---|---:|---:|
| required_columns | PASS | 0 | 1 |
| parse_errors | PASS | 0 | 951 |
| missing_values | PASS | 0 | 9510 |
| non_finite_values | PASS | 0 | 9510 |
| invalid_numeric_values | PASS | 0 | 9510 |
| timestamp_schema | PASS | 0 | 1902 |
| update_id_schema | PASS | 0 | 951 |
| event_time_monotonic | PASS | 0 | 950 |
| duplicate_timestamps | PASS | 0 | 951 |
| bid_positive | PASS | 0 | 951 |
| ask_positive | PASS | 0 | 951 |
| uncrossed_book | PASS | 0 | 951 |
| spread_nonnegative | PASS | 0 | 951 |
| mid_consistency | PASS | 0 | 951 |
| spread_consistency | PASS | 0 | 951 |
| volume_nonnegative | PASS | 0 | 1902 |
| obi_range | PASS | 0 | 951 |
| obi_consistency | PASS | 0 | 951 |
| local_event_clock_order | WARNING | 951 | 951 |

指標：

```json
{
  "first_event_time_ms": 1787765781314,
  "last_event_time_ms": 1787765876414,
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
  "min_event_time_ms": 1787765781314,
  "max_event_time_ms": 1787765876414,
  "local_minus_event_ms_min": "-102.803",
  "local_minus_event_ms_max": "-53.977",
  "max_obi_absolute_difference": "4.9966214887003765116E-9",
  "physical_lines": 952,
  "unique_timestamps": 951,
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
