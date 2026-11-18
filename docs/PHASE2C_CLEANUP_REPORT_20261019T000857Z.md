# Phase 2C-R2：人工批准清理與逐階段復發監控

**CLEANUP／MONITOR PASS**。來源UNKNOWN；本輪未觀察到復發。

## 1. 舊FAIL run

舊Phase2C run 20261018T232041Z及其報告永久保留FAIL；舊repair run 20261018T235018Z與其報告保持原樣。四個保護位置逐一比對結果見integrity_pre_report.json的protected_evidence。本報告測試、資料輸出、Reference與確定性數字只取本輪新證據，沒有以舊輸出hash或PASS替代新結果。

## 2. 舊repair run

20261018T235018Z；來源分類UNKNOWN沒有改標；所有舊鑑識證據完整保留。

## 3. cleanup run_id與工作目錄

20261019T000857Z（UTC）。pwd/realpath為/home/jason/quantum-hft，Linux ext4；實測見[workdir_verification.json](/home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/logs/workdir_verification.json)與root_commands.json。

```text
{
  "bytecode_disabled": true,
  "cwd": "/home/jason/quantum-hft",
  "platform": "Linux-6.6.114.1-microsoft-standard-WSL2-x86_64-with-glibc2.43",
  "python": "3.14.4 (main, Aug 20 2026, 10:41:58) [GCC 15.2.0]"
}
```

## 4. 人工批准內容

人工只批准清理四個再次證實空白的未授權目錄，並以現有正式程式/測試分stage重跑；不代表確認創建者、不新增允許清單、不降低完整性標準。

[authorization.txt](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/authorization.txt)

## 5. 四個目錄清理前完整stat

```text
[
  {
    "atime": {
      "ns": "1792366011011403337",
      "utc": "2026-10-18T23:26:51.011403337Z"
    },
    "birth_time": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "ctime": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "device": 2096,
    "direct_child_count": 0,
    "exists": true,
    "gid": 1000,
    "group": "jason",
    "inode": 116288,
    "mode": "0o755",
    "mount_id": 80,
    "mount_point": false,
    "mtime": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "ordinary_directory": true,
    "owner": "jason",
    "path": "tests/.agents",
    "recursive_entry_count": 0,
    "statx_mask": 8191,
    "symbolic_link": false,
    "uid": 1000
  },
  {
    "atime": {
      "ns": "1792366011011403337",
      "utc": "2026-10-18T23:26:51.011403337Z"
    },
    "birth_time": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "ctime": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "device": 2096,
    "direct_child_count": 0,
    "exists": true,
    "gid": 1000,
    "group": "jason",
    "inode": 116316,
    "mode": "0o755",
    "mount_id": 80,
    "mount_point": false,
    "mtime": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "ordinary_directory": true,
    "owner": "jason",
    "path": "tests/.aws",
    "recursive_entry_count": 0,
    "statx_mask": 8191,
    "symbolic_link": false,
    "uid": 1000
  },
  {
    "atime": {
      "ns": "1792366011011403337",
      "utc": "2026-10-18T23:26:51.011403337Z"
    },
    "birth_time": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "ctime": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "device": 2096,
    "direct_child_count": 0,
    "exists": true,
    "gid": 1000,
    "group": "jason",
    "inode": 116315,
    "mode": "0o755",
    "mount_id": 80,
    "mount_point": false,
    "mtime": {
      "ns": "1792366010815403338",
      "utc": "2026-10-18T23:26:50.815403338Z"
    },
    "ordinary_directory": true,
    "owner": "jason",
    "path": "tests/.codex",
    "recursive_entry_count": 0,
    "statx_mask": 8191,
    "symbolic_link": false,
    "uid": 1000
  },
  {
    "atime": {
      "ns": "1792366011011403337",
      "utc": "2026-10-18T23:26:51.011403337Z"
    },
    "birth_time": {
      "ns": "1792366010811403338",
      "utc": "2026-10-18T23:26:50.811403338Z"
    },
    "ctime": {
      "ns": "1792366010811403338",
      "utc": "2026-10-18T23:26:50.811403338Z"
    },
    "device": 2096,
    "direct_child_count": 0,
    "exists": true,
    "gid": 1000,
    "group": "jason",
    "inode": 116287,
    "mode": "0o755",
    "mount_id": 80,
    "mount_point": false,
    "mtime": {
      "ns": "1792366010811403338",
      "utc": "2026-10-18T23:26:50.811403338Z"
    },
    "ordinary_directory": true,
    "owner": "jason",
    "path": "tests/.git",
    "recursive_entry_count": 0,
    "statx_mask": 8191,
    "symbolic_link": false,
    "uid": 1000
  }
]
```

[pre_cleanup_inventory.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/pre_cleanup_inventory.json)

## 6. 是否完全空白

四者均普通directory、非symlink、非mount point，direct及recursive entry count全為0；沒有檔案、credential、設定或Git metadata。未執行其中內容。

## 7. 實際清理命令

```text
rmdir tests/.agents
rmdir tests/.aws
rmdir tests/.codex
rmdir tests/.git
```

## 8. 四次rmdir結果

| 命令 | 開始UTC | 結束UTC | exit | stdout | stderr |
| --- | --- | --- | --- | --- | --- |
| rmdir tests/.agents | 2026-10-19T00:09:50.804383+00:00 | 2026-10-19T00:09:50.813125+00:00 | 0 | '' | '' |
| rmdir tests/.aws | 2026-10-19T00:09:50.813482+00:00 | 2026-10-19T00:09:50.816964+00:00 | 0 | '' | '' |
| rmdir tests/.codex | 2026-10-19T00:09:50.817271+00:00 | 2026-10-19T00:09:50.820509+00:00 | 0 | '' | '' |
| rmdir tests/.git | 2026-10-19T00:09:50.820817+00:00 | 2026-10-19T00:09:50.823473+00:00 | 0 | '' | '' |

[cleanup_execution.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/cleanup_execution.json)

## 9. 清理後狀態

四路徑全部不存在；tests其他原有內容保持不變。

[post_cleanup_inventory.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/post_cleanup_inventory.json)

## 10. 來源仍為UNKNOWN

**UNKNOWN**。人工清理批准與本輪未復發均不構成創建者證據；不宣稱是Codex、測試、使用者或外部程序造成。

## 11. 每個監控stage

| Stage | 內容 | 開始UTC | 結束UTC | exit | 復發 | 結果 |
| --- | --- | --- | --- | --- | --- | --- |
| 1A | Phase 2A existing regression | 2026-10-19T00:10:32.093557+00:00 | 2026-10-19T00:10:32.643841+00:00 | 0 | 未觀察到 | PASS |
| 1B | Phase 2B existing regression | 2026-10-19T00:11:17.577234+00:00 | 2026-10-19T00:11:18.626749+00:00 | 0 | 未觀察到 | PASS |
| 1C | Feature schema | 2026-10-19T00:11:18.675191+00:00 | 2026-10-19T00:11:19.222543+00:00 | 0 | 未觀察到 | PASS |
| 1D | Feature formulas | 2026-10-19T00:11:19.269416+00:00 | 2026-10-19T00:11:19.818265+00:00 | 0 | 未觀察到 | PASS |
| 1E | Feature builder | 2026-10-19T00:11:19.864969+00:00 | 2026-10-19T00:11:20.414642+00:00 | 0 | 未觀察到 | PASS |
| 1F | Feature reference | 2026-10-19T00:11:20.462529+00:00 | 2026-10-19T00:11:21.011704+00:00 | 0 | 未觀察到 | PASS |
| 1G | Feature validator | 2026-10-19T00:11:21.059627+00:00 | 2026-10-19T00:11:21.608087+00:00 | 0 | 未觀察到 | PASS |
| 1H | Feature writer | 2026-10-19T00:11:21.655668+00:00 | 2026-10-19T00:11:22.204489+00:00 | 0 | 未觀察到 | PASS |
| 1I | Build features tool | 2026-10-19T00:11:22.251895+00:00 | 2026-10-19T00:11:22.800641+00:00 | 0 | 未觀察到 | PASS |
| 2A | obi_market_data_20260827_session1 first execution | 2026-10-19T00:13:01.812401+00:00 | 2026-10-19T00:13:06.911569+00:00 | 0 | 未觀察到 | PASS |
| 2B | obi_market_data_20260827_session2 first execution | 2026-10-19T00:13:06.912236+00:00 | 2026-10-19T00:13:15.513120+00:00 | 0 | 未觀察到 | PASS |
| 2C | obi_market_data_20260827_session3 first execution | 2026-10-19T00:13:15.513746+00:00 | 2026-10-19T00:13:20.615583+00:00 | 0 | 未觀察到 | PASS |
| 2D | obi_market_data_test_20260827 first execution | 2026-10-19T00:13:20.618040+00:00 | 2026-10-19T00:13:21.216534+00:00 | 0 | 未觀察到 | PASS |
| 2E | obi_market_data first execution | 2026-10-19T00:13:21.218154+00:00 | 2026-10-19T00:13:25.820520+00:00 | 0 | 未觀察到 | PASS |
| 2F | replay_events_1000 first execution | 2026-10-19T00:13:25.822847+00:00 | 2026-10-19T00:13:33.926504+00:00 | 0 | 未觀察到 | PASS |
| 2G | replay_events_1000 independent second execution | 2026-10-19T00:13:33.927351+00:00 | 2026-10-19T00:13:42.030006+00:00 | 0 | 未觀察到 | PASS |
| 2H | replay_events_50000 first execution | 2026-10-19T00:13:42.032735+00:00 | 2026-10-19T00:17:49.788902+00:00 | 0 | 未觀察到 | PASS |
| 2I | replay_events_50000 independent second execution | 2026-10-19T00:17:49.790147+00:00 | 2026-10-19T00:21:57.546524+00:00 | 0 | 未觀察到 | PASS |
| 2J | obi_market_data_20260827_session1 independent second execution | 2026-10-19T00:21:57.547413+00:00 | 2026-10-19T00:22:02.643223+00:00 | 0 | 未觀察到 | PASS |

## 12. 是否重新出現

19個明列stage各保存before/after inventory、實際argv、開始/結束UTC、exit與完整stdout/stderr。四目錄在stage前後及程序執行中每0.5秒抽樣檢查均未觀察到復發；這不是核心層的全部檔案事件追蹤，不能排除兩次抽樣間瞬時出現又消失的行為。tests與專案根目錄direct children、九個HFT來源SHA/大小在每stage前後比較。來源始終UNKNOWN，不由本輪未復發推定過去創建者。

## 13. 第一個復發stage

NOT_AVAILABLE：沒有觀察到復發，沒有可歸因stage。初版driver錯誤另列，與目錄復發無關。

## 14. 是否修改測試

沒有修改任何既有測試；直接逐stage執行。既有回歸318與Phase2C 201項全部PASS。

| Stage | tests | PASS | FAIL | ERROR | skipped | unittest秒 |
| --- | --- | --- | --- | --- | --- | --- |
| 1A | 164 | 164 | 0 | 0 | 0 | 0.313 |
| 1B | 154 | 154 | 0 | 0 | 0 | 0.903 |
| 1C | 13 | 13 | 0 | 0 | 0 | 0.002 |
| 1D | 33 | 33 | 0 | 0 | 0 | 0.002 |
| 1E | 26 | 26 | 0 | 0 | 0 | 0.001 |
| 1F | 41 | 41 | 0 | 0 | 0 | 0.009 |
| 1G | 34 | 34 | 0 | 0 | 0 | 0.004 |
| 1H | 28 | 28 | 0 | 0 | 0 | 0.024 |
| 1I | 26 | 26 | 0 | 0 | 0 | 0.413 |

## 15. 是否修改Feature Builder

Feature Builder、公式、Registry、Phase2A Adapter與Phase2B Rebuilder均未改。版本SHA見[code_manifest.json](/home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/summary/code_manifest.json)；新增監控/報告腳本只在cleanup run。

## 16. HFT與舊證據完整性

| 來源 | bytes | 新驗證SHA-256 |
| --- | --- | --- |
| obi_market_data_20260827_session1.csv | 8019032 | 9931b0d9ef9be5dba36ea26cdd4d6d7fd1552a195af53460c59ffe415ceea8d3 |
| obi_market_data_20260827_session2.csv | 13226704 | 363e81f86de61a3acc697216082770f11a7158935c8745e172235ee6f9e1fd7c |
| obi_market_data_20260827_session3.csv | 7691375 | 72decc3d89cf833f6327bb11dfe66f3a9371fb932df290b54f7b5250d1a4e1b4 |
| obi_market_data_test_20260827.csv | 126181 | aa9bb47e598aaa024640c079654ed17da1e70552ed06632361dc4cb607b8171f |
| obi_market_data.csv | 6683124 | e71676d8d2d6c04e6cf9b4f80ef3eb113de78a92eff8a280fd633541ac8231e7 |
| replay_snapshot_1000.json | 560071 | ee4bd68eac23fb8277d6842e9212100b27a9cbe32785f6b907f891fcdeaa5ada |
| replay_events_1000.jsonl | 1176899 | 26e5059e8a3448a93a72eb0ed9893be439941c039c54110edbc131cc6841b503 |
| replay_snapshot_50000.json | 560071 | 62cb9379220e8325a2b48d02be4fbab373cce546bcac06f0c574bd3784c70750 |
| replay_events_50000.jsonl | 99969619 | c6f27ef16199cfaa94efaf9b4a2444e708484e915a03742d4c90fd9b3b6b59be |

報告產生前[integrity_pre_report.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/integrity_pre_report.json)為PASS。457個既有一般檔案的SHA與已採集metadata（mode、size、mtime_ns、ctime_ns、inode、uid、gid、kind）保持；不包含atime、birth time或device比較。只移除四個批准目錄，modified existing files與未批准項目均為0。合法rmdir、新輸出及既有人工fixture建立/移除引起的父目錄mtime/ctime/size差異已逐項列明；directory identity、mode、owner仍核對，並非宣稱所有directory metadata完全不變。

兩報告產生後root另存[integrity_final.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/integrity_final.json)與[completion_manifest.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/completion_manifest.json)。本產生器不捏造尚未執行的收尾結果；最終交付必須通過該檢查。

舊Phase2C run 20261018T232041Z及其報告永久保留FAIL；舊repair run 20261018T235018Z與其報告保持原樣。四個保護位置逐一比對結果見integrity_pre_report.json的protected_evidence。本報告測試、資料輸出、Reference與確定性數字只取本輪新證據，沒有以舊輸出hash或PASS替代新結果。

## 17. 專題網路與交易

沒有本任務專題網路、Binance REST/WebSocket/Testnet、API key、套件安裝、交易或HFT binary。這是作業命令範圍聲明，不是全機封包監測。

本次未進入Phase 2D，未建立Label、Target、split、模型、QUBO、QAOA、回測或Paper Trading；完成後停止並等待人工審核。

## 18. 所有實際命令

[execution_index.json](/home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/logs/execution_index.json)保存19個stage的完整argv、時間、exit及stdout/stderr路徑；[root_commands.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/root_commands.json)保存清理、監控修訂、報告與完整性驗證等實際工具命令。完整stage stdout/stderr逐檔保留，不以摘要取代。root命令ledger初次整份保存因E2BIG在程序建立前失敗，未寫檔；後續以12個分段與索引保存，索引如實記錄，與測試/資料執行結果無關。報告作者命令另見report_authoring_commands.json；報告後的封存命令由root另存finalization_commands.json。

Stage 1A

```text
python3 -B -m unittest tests/test_registry.py tests/test_csv_adapter.py tests/test_snapshot_adapter.py tests/test_replay_adapter.py tests/test_inspect_data_sources.py
```

Stage 1B

```text
python3 -B -m unittest tests/test_orderbook_continuity.py tests/test_orderbook_rebuilder.py tests/test_orderbook_reference.py tests/test_orderbook_canonical.py tests/test_rebuild_orderbook_tool.py
```

Stage 1C

```text
python3 -B -m unittest tests/test_feature_schema.py
```

Stage 1D

```text
python3 -B -m unittest tests/test_feature_formulas.py
```

Stage 1E

```text
python3 -B -m unittest tests/test_feature_builder.py
```

Stage 1F

```text
python3 -B -m unittest tests/test_feature_reference.py
```

Stage 1G

```text
python3 -B -m unittest tests/test_feature_validator.py
```

Stage 1H

```text
python3 -B -m unittest tests/test_feature_writer.py
```

Stage 1I

```text
python3 -B -m unittest tests/test_build_features_tool.py
```

Stage 2A

```text
python3 -B tools/build_features.py --config configs/data_sources.json --source-id obi_market_data_20260827_session1 --feature-view aggregate_core_v1 --output /home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/sources/obi_market_data_20260827_session1 --compare-reference --repeat 1 --progress-every 5000
```

Stage 2B

```text
python3 -B tools/build_features.py --config configs/data_sources.json --source-id obi_market_data_20260827_session2 --feature-view aggregate_core_v1 --output /home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/sources/obi_market_data_20260827_session2 --compare-reference --repeat 1 --progress-every 5000
```

Stage 2C

```text
python3 -B tools/build_features.py --config configs/data_sources.json --source-id obi_market_data_20260827_session3 --feature-view aggregate_core_v1 --output /home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/sources/obi_market_data_20260827_session3 --compare-reference --repeat 1 --progress-every 5000
```

Stage 2D

```text
python3 -B tools/build_features.py --config configs/data_sources.json --source-id obi_market_data_test_20260827 --feature-view aggregate_core_v1 --output /home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/sources/obi_market_data_test_20260827 --compare-reference --repeat 1 --progress-every 5000
```

Stage 2E

```text
python3 -B tools/build_features.py --config configs/data_sources.json --source-id obi_market_data --feature-view aggregate_core_v1 --output /home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/sources/obi_market_data --compare-reference --repeat 1 --progress-every 5000
```

Stage 2F

```text
python3 -B tools/build_features.py --config configs/data_sources.json --source-id replay_events_1000 --feature-view both --output /home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/sources/replay_events_1000 --compare-reference --repeat 1 --progress-every 5000
```

Stage 2G

```text
python3 -B /home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/repeat_source.py 20261019T001249Z replay_events_1000
```

Stage 2H

```text
python3 -B tools/build_features.py --config configs/data_sources.json --source-id replay_events_50000 --feature-view both --output /home/jason/quantum-hft/artifacts/phase2c/20261019T001249Z/sources/replay_events_50000 --compare-reference --repeat 1 --progress-every 5000
```

Stage 2I

```text
python3 -B /home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/repeat_source.py 20261019T001249Z replay_events_50000
```

Stage 2J

```text
python3 -B /home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/repeat_source.py 20261019T001249Z obi_market_data_20260827_session1
```

## 19. 清理方式限制

四個目標的人工批准清理僅使用上述rmdir；沒有呼叫rm、rm -r或rm -rf命令，沒有wildcard或替代刪除。既有測試的TemporaryDirectory可能透過標準函式庫內部清理自己的人工fixture；這與四目標清理分開，不能宣稱整次沒有任何遞迴cleanup函式呼叫。

## 20. 沒有虛構結果

本報告數值由本輪實際證據生成，未知來源維持UNKNOWN；沒有把舊PASS或預期hash當新結果。

## 21. 監控初版失敗與後續修訂

初版stage_monitor.py的stage_*.json glob把沒有status的before/after inventory也當成stage結果。Stage 1A的164測試及其stage結果已PASS，但初次driver因此exit 1，當時Stage 1B尚未執行。原腳本、1A證據及錯誤命令紀錄保留；v2排除inventory後，resume_stage1.py從1B續跑，沒有覆寫或重跑1A。v3加強例外時停止子程序、封存after inventory與stage結果，Stage 2使用v3。這只是cleanup run內監控腳本修訂，沒有改正式程式或測試；不能掩飾初次driver失敗，也不能誤報為目錄復發。

[monitor_revision.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/monitor_revision.json)；stage_monitor.py、stage_monitor_v2.py、stage_monitor_v3.py及root_commands.json保存原始脈絡。

## 22. 新增清單、最後驗證與停止

完整新增路徑、大小及SHA見[completion_manifest.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/completion_manifest.json)；範圍只有本cleanup run、唯一新Phase2C run與兩報告。

報告產生前[integrity_pre_report.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/integrity_pre_report.json)為PASS。457個既有一般檔案的SHA與已採集metadata（mode、size、mtime_ns、ctime_ns、inode、uid、gid、kind）保持；不包含atime、birth time或device比較。只移除四個批准目錄，modified existing files與未批准項目均為0。合法rmdir、新輸出及既有人工fixture建立/移除引起的父目錄mtime/ctime/size差異已逐項列明；directory identity、mode、owner仍核對，並非宣稱所有directory metadata完全不變。

兩報告產生後root另存[integrity_final.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/integrity_final.json)與[completion_manifest.json](/home/jason/quantum-hft/artifacts/phase2c_cleanup/20261019T000857Z/completion_manifest.json)。本產生器不捏造尚未執行的收尾結果；最終交付必須通過該檢查。

本次未進入Phase 2D，未建立Label、Target、split、模型、QUBO、QAOA、回測或Paper Trading；完成後停止並等待人工審核。
