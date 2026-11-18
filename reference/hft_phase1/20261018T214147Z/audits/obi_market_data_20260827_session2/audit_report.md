# 資料集唯讀稽核

Run: `phase1v2_20261018T210029Z_obi_market_data_20260827_session2`

整體狀態：**WARNING**

PASS＝已檢查且未發現違規；WARNING＝需解釋的觀測；FAIL＝格式或一致性違規；NOT AVAILABLE＝沒有可檢查的有效證據。

輸入僅供讀取。CSV／JSONL 串流解析；保存時間戳與更新 ID 區間集合以偵測全檔重複，不保存完整 payload。Snapshot 作為一份 JSON 文件載入。

| 檔案 | 類型 | 狀態 | 筆數 | 解析錯誤 | Bytes |
|---|---|---|---:|---:|---:|
| results/obi_market_data_20260827_session2.csv | csv | WARNING | 99871 | 0 | 13226704 |

## results/obi_market_data_20260827_session2.csv

SHA-256: `363e81f86de61a3acc697216082770f11a7158935c8745e172235ee6f9e1fd7c`

| 檢查 | 狀態 | 異常數 | 可檢查觀測數 |
|---|---|---:|---:|
| required_columns | PASS | 0 | 1 |
| parse_errors | PASS | 0 | 99871 |
| missing_values | PASS | 0 | 998710 |
| non_finite_values | PASS | 0 | 998710 |
| invalid_numeric_values | PASS | 0 | 998710 |
| timestamp_schema | PASS | 0 | 199742 |
| update_id_schema | PASS | 0 | 99871 |
| event_time_monotonic | PASS | 0 | 99870 |
| duplicate_timestamps | PASS | 0 | 99871 |
| bid_positive | PASS | 0 | 99871 |
| ask_positive | PASS | 0 | 99871 |
| uncrossed_book | PASS | 0 | 99871 |
| spread_nonnegative | PASS | 0 | 99871 |
| mid_consistency | PASS | 0 | 99871 |
| spread_consistency | PASS | 0 | 99871 |
| volume_nonnegative | PASS | 0 | 199742 |
| obi_range | PASS | 0 | 99871 |
| obi_consistency | PASS | 0 | 99871 |
| local_event_clock_order | WARNING | 99871 | 99871 |

指標：

```json
{
  "first_event_time_ms": 1787773384514,
  "last_event_time_ms": 1787783377014,
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
  "min_event_time_ms": 1787773384514,
  "max_event_time_ms": 1787783377014,
  "local_minus_event_ms_min": "-4541.681",
  "local_minus_event_ms_max": "-47.57",
  "max_obi_absolute_difference": "5E-9",
  "physical_lines": 99872,
  "unique_timestamps": 99871,
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
