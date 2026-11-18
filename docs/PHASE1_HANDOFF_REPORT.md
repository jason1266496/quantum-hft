# Phase 1 Research Handoff Report

**QUANTUM-HFT HANDOFF PASS**：本次只交接與規格建置。Phase 2尚未實作；等待人工審核。

## 1. handoff_run_id

20261018T214147Z；取自本次UTC時鐘，沒有重用既有run。目標原先不存在，已先確認後只建立指定目錄；create_unique_handoff_run以exclusive mkdir建立交接run。

## 2. 原始HFT工作副本

/home/jason/hft-realtime-codex。開始前pwd與realpath完全相同，findmnt為Linux ext4。預設WindowsApps應用目錄未用作來源。兩個保留資料夾 /home/jason/hft-realtime 與 /home/jason/hft-realtime-codex-incomplete-20261018T194544Z 未寫入。

## 3. 新專案與權限邊界

/home/jason/quantum-hft。獨立同層真實目錄，沒有symlink或可寫results mount。權限申請只涉及此新目錄的必要建立/寫入，沒有要求整個/home/jason無限制存取，沒有danger-full-access或--yolo。所有新增內容在新專案。

## 4. Phase 1 v2

PASS；run 20261018T210029Z。正式報告、protected baseline/final manifest、integrity summary、環境、Dataset Audit單元測試、九資料稽核、CMake安全摘要、Offline build摘要已核對內容後複製。此處未重新build或執行HFT binary。

## 5. Timestamp Review

WARNING；run 20261018T212122Z。269,284為local_timestamp_us−event_time_ms×1000<0，五檔合計單一警告；不代表負網路延遲。最大檔內event interval241ms；session3 local13.327507秒間隔不是市場資料缺口。歷史producer/clock根因仍UNKNOWN。

Recovery run20261018T202030Z的初次final_integrity_check為FAIL，後續review為PASS；兩者原樣保留，後續說明既有directory symlink誤判覆核，沒有將舊FAIL改寫。

## 6. Phase 2決策

PASS_WITH_RESTRICTIONS，只表示經審核event time可支持隔離Session的離線時間資料研究。標籤須保存actual horizon/error並排除缺口/尾端。此次沒有執行Phase2。新max_match_error_ms=null；舊25ms與200ms提案原樣封存但不是新project最終參數。

## 7. 複製清單

48份，共2822328 bytes。

| 來源相對路徑 | 目的相對路徑 | copy_status |
| --- | --- | --- |
| docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md | [reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md) | PASS |
| docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md | [reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md) | PASS |
| docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md | [reference/hft_phase1/20261018T214147Z/reports/PHASE1_RECOVERY_REPORT_20261018T202030Z.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/reports/PHASE1_RECOVERY_REPORT_20261018T202030Z.md) | PASS |
| artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.json | [reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_baseline_protected_files_manifest.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_baseline_protected_files_manifest.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.json | [reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_protected_files_manifest.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_protected_files_manifest.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/final/final_integrity_summary.json | [reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_integrity_summary.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_integrity_summary.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/environment/environment.json | [reference/hft_phase1/20261018T214147Z/environment/phase1_v2_environment.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/environment/phase1_v2_environment.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/tests/dataset_unit_test_summary.json | [reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_unit_test_summary.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_unit_test_summary.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json | [reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_execution_summary.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_execution_summary.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/audits/dataset_audit_verification.json | [reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_audit_verification.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_audit_verification.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/build/cmake_static_safety.json | [reference/hft_phase1/20261018T214147Z/environment/phase1_v2_cmake_static_safety.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/environment/phase1_v2_cmake_static_safety.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/build/build_execution.json | [reference/hft_phase1/20261018T214147Z/environment/phase1_v2_build_execution.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/environment/phase1_v2_build_execution.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session1/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session2/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_20260827_session3/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data_test_20260827/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_obi_market_data/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_50000/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.md) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.json) | PASS |
| artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.md | [reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.md) | PASS |
| artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_1000/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_1000/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_1000/audit_report.json) | PASS |
| artifacts/phase1_v2/20261018T210029Z/audits/snapshot_replay_pair_50000/audit_report.json | [reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_50000/audit_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_50000/audit_report.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/warning_definition.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/warning_definition.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/warning_definition.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/csv_timestamp_summary.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/csv_timestamp_summary.csv | [reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.csv](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.csv) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/clock_delta_statistics.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/clock_delta_statistics.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/clock_delta_statistics.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_gap_analysis.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/timestamp_gap_analysis.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/timestamp_gap_analysis.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/field_usage_matrix.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/field_usage_matrix.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/field_usage_matrix.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/phase2_time_rules.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/phase2_time_rules.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/phase2_time_rules.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/final_integrity_check.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/final_integrity_check.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/final_integrity_check.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/source_timestamp_semantics.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/source_timestamp_semantics.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/source_timestamp_semantics.json) | PASS |
| artifacts/phase1_timestamp_review/20261018T212122Z/warning_cause_classification.json | [reference/hft_phase1/20261018T214147Z/timestamp_review/warning_cause_classification.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/timestamp_review/warning_cause_classification.json) | PASS |
| artifacts/phase1_recovery/20261018T202030Z/recommended_action.json | [reference/hft_phase1/20261018T214147Z/manifests/recovery_recommended_action.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/manifests/recovery_recommended_action.json) | PASS |
| artifacts/phase1_recovery/20261018T202030Z/suspicious_file_report.json | [reference/hft_phase1/20261018T214147Z/manifests/recovery_suspicious_file_report.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/manifests/recovery_suspicious_file_report.json) | PASS |
| artifacts/phase1_recovery/20261018T202030Z/final_integrity_check.json | [reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_check.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_check.json) | PASS |
| artifacts/phase1_recovery/20261018T202030Z/final_integrity_review.json | [reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_review.json](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_review.json) | PASS |
| artifacts/phase1_recovery/20261018T202030Z/FINAL_INTEGRITY_REVIEW.md | [reference/hft_phase1/20261018T214147Z/reports/RECOVERY_FINAL_INTEGRITY_REVIEW_20261018T202030Z.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/reports/RECOVERY_FINAL_INTEGRITY_REVIEW_20261018T202030Z.md) | PASS |
| docs/DATASET_AUDIT.md | [reference/hft_phase1/20261018T214147Z/audits/DATASET_AUDIT.md](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/audits/DATASET_AUDIT.md) | PASS |

每份來源確認run與內容，不按檔名猜測；精確核對說明保存在discovery及Manifest。原報告中的絕對路徑連結保持原樣以確保hash，目的副本映射由Manifest提供。

## 8. 排除清單

- src/
- analysis/
- scripts/
- results/
- all raw market CSV/JSONL/snapshots
- ELF
- build products
- *.tar.gz
- *.7z
- .env
- credentials/private keys
- Testnet/Live/Capture programs
- kernel matrices
- models

沒有複製src/results、市場CSV/JSONL/Snapshot、ELF、build產物、壓縮檔、模型或憑證。明確例外是使用者指定的csv_timestamp_summary.csv：它是逐檔統計報告，非市場逐筆CSV。CMake/build兩份JSON是稽核摘要，並非build產物。

## 9. 來源與目的SHA-256

| 交接檔 | source_sha256 | destination_sha256 | 來源/目的bytes |
| --- | --- | --- | --- |
| reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md | f7463ee1cb9e7ed9a2c09b9547cc1efe0e06d508804d398d3d1f0428b09ead3c | f7463ee1cb9e7ed9a2c09b9547cc1efe0e06d508804d398d3d1f0428b09ead3c | 166029/166029 |
| reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md | 6c5f20c40daaa5311901e5c98688078690d76831172ff9936480f5cc25a91757 | 6c5f20c40daaa5311901e5c98688078690d76831172ff9936480f5cc25a91757 | 148541/148541 |
| reference/hft_phase1/20261018T214147Z/reports/PHASE1_RECOVERY_REPORT_20261018T202030Z.md | c792f1f99b05eaf6435e307519e69b6cbe24ed10700c93434cbe4986d72e679d | c792f1f99b05eaf6435e307519e69b6cbe24ed10700c93434cbe4986d72e679d | 632296/632296 |
| reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_baseline_protected_files_manifest.json | b6544c3b0736d2aebc44538854f6740332260505f4c33676bd493ae63d0ec78a | b6544c3b0736d2aebc44538854f6740332260505f4c33676bd493ae63d0ec78a | 151343/151343 |
| reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_protected_files_manifest.json | 439a63cc0f6376962909572ba2e09172755895608266307a32f8ddfa774ff9bc | 439a63cc0f6376962909572ba2e09172755895608266307a32f8ddfa774ff9bc | 151343/151343 |
| reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_integrity_summary.json | c63d04080ee5172ef2258599d7e20e65c7fc9da689dc0422b644bb3370fbcd99 | c63d04080ee5172ef2258599d7e20e65c7fc9da689dc0422b644bb3370fbcd99 | 912/912 |
| reference/hft_phase1/20261018T214147Z/environment/phase1_v2_environment.json | 109041ace3f31fbf1b12d0afe9171f9e6ae0b7c1fe2499fe22a896ace0db8153 | 109041ace3f31fbf1b12d0afe9171f9e6ae0b7c1fe2499fe22a896ace0db8153 | 4755/4755 |
| reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_unit_test_summary.json | b073ac556b3a416bd226ae240ab643d767e070d623c8d61347b3034ed3692d38 | b073ac556b3a416bd226ae240ab643d767e070d623c8d61347b3034ed3692d38 | 643/643 |
| reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_execution_summary.json | 2d5dd8af671aa32137c32ab1866960e1c020ddbde933c6ef426ef4dd14c9e74e | 2d5dd8af671aa32137c32ab1866960e1c020ddbde933c6ef426ef4dd14c9e74e | 112246/112246 |
| reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_audit_verification.json | 3f1236ee95b9ff819d465d1812dce9449c1c7299a0ffe00a1d96ed55e62d2024 | 3f1236ee95b9ff819d465d1812dce9449c1c7299a0ffe00a1d96ed55e62d2024 | 6156/6156 |
| reference/hft_phase1/20261018T214147Z/environment/phase1_v2_cmake_static_safety.json | 6945adaece1e5aa60de8cee767c9c57f34d23d70229c77dda9d453cd54997335 | 6945adaece1e5aa60de8cee767c9c57f34d23d70229c77dda9d453cd54997335 | 2820/2820 |
| reference/hft_phase1/20261018T214147Z/environment/phase1_v2_build_execution.json | 3462ac410d2717810383a63c6bbeafbea080fbb280839c9098ac42feaec2ebf0 | 3462ac410d2717810383a63c6bbeafbea080fbb280839c9098ac42feaec2ebf0 | 3239/3239 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.json | 51ae4e4b83c6ac1680de2fc8d0e2ba38daf9e13f4f802eac93a2d9b87cd0d263 | 51ae4e4b83c6ac1680de2fc8d0e2ba38daf9e13f4f802eac93a2d9b87cd0d263 | 13413/13413 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.md | c773a294debb283bb2ef2005cd5a5a7e50729da2dd065039f71816c02cc5e7eb | c773a294debb283bb2ef2005cd5a5a7e50729da2dd065039f71816c02cc5e7eb | 2932/2932 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.json | e422d50ae77e06cabbb4843171604de9b1723ff47dae76a3a08c1987bb20d3fc | e422d50ae77e06cabbb4843171604de9b1723ff47dae76a3a08c1987bb20d3fc | 13391/13391 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.md | 9fb01810cf817f5c7ca70e8fb3ee259d7ade5f73494b39381d49f2153bf83875 | 9fb01810cf817f5c7ca70e8fb3ee259d7ade5f73494b39381d49f2153bf83875 | 2913/2913 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.json | 3bce21bc147b82a55ab67dcab58e6cbcfff8ca2ae78f793d3ae4bba938fbcf1b | 3bce21bc147b82a55ab67dcab58e6cbcfff8ca2ae78f793d3ae4bba938fbcf1b | 13415/13415 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.md | f0bef4e7a85a5dbc5683870fa91507fc78994d4e88bdb5c93abb6b1d103ce186 | f0bef4e7a85a5dbc5683870fa91507fc78994d4e88bdb5c93abb6b1d103ce186 | 2935/2935 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.json | 6b22f7a8e2560f9a0504a25faed472cf35066e6e1e58366931ab0168b21b45c6 | 6b22f7a8e2560f9a0504a25faed472cf35066e6e1e58366931ab0168b21b45c6 | 13265/13265 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.md | 92da7f0cf00e005e1bd3af46366e4e4a777d0d67b6b34cca30c4f83b350f4521 | 92da7f0cf00e005e1bd3af46366e4e4a777d0d67b6b34cca30c4f83b350f4521 | 2875/2875 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.json | 0cd167eabf120387a7770132cf9d4580438ff8c35c0a17f21d9e76ebb752c9e6 | 0cd167eabf120387a7770132cf9d4580438ff8c35c0a17f21d9e76ebb752c9e6 | 12980/12980 |
| reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.md | 6f4d4a0104e05defa0fb4f56702a90f8e6b1eb8995eac1a24ae4b69d01796a4d | 6f4d4a0104e05defa0fb4f56702a90f8e6b1eb8995eac1a24ae4b69d01796a4d | 2877/2877 |
| reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.json | efc7033d0cab62a653e6decc94e4c1e696e3db8a71e30d4ddfeb86e7983f10b1 | efc7033d0cab62a653e6decc94e4c1e696e3db8a71e30d4ddfeb86e7983f10b1 | 3472/3472 |
| reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.md | f425c3f4a7771597b5c46162cb9055a3fe116c815529b3d90d6d16d5b5bab4fd | f425c3f4a7771597b5c46162cb9055a3fe116c815529b3d90d6d16d5b5bab4fd | 1933/1933 |
| reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.json | 66b0d30dc885108fb4a77d9bdcb919a740ef91a25e2c1907296b4616109cb3dc | 66b0d30dc885108fb4a77d9bdcb919a740ef91a25e2c1907296b4616109cb3dc | 4674/4674 |
| reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.md | c0b3138ddf98102662c3da269c73835c5d78ede2b43dbd77eb04b70c9fa31b18 | c0b3138ddf98102662c3da269c73835c5d78ede2b43dbd77eb04b70c9fa31b18 | 2552/2552 |
| reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.json | 0970ba5f1a8c0512cc8d7941e45b0fbe0a5204c6d9442d32e7f2db67341177ab | 0970ba5f1a8c0512cc8d7941e45b0fbe0a5204c6d9442d32e7f2db67341177ab | 3476/3476 |
| reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.md | f1cd20fb3c9d7fe37fa373279844ff60fef325fc1f71e929c18fad8d2af7c42e | f1cd20fb3c9d7fe37fa373279844ff60fef325fc1f71e929c18fad8d2af7c42e | 1936/1936 |
| reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.json | 3528b03b02393a69a9f5cc111ff59826cc78c98e2d40c940bdec11122036e6c2 | 3528b03b02393a69a9f5cc111ff59826cc78c98e2d40c940bdec11122036e6c2 | 4704/4704 |
| reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.md | 3fc27f7fdf20e624ff5a1e8d45bf660d20afe7a2999613c193fdfdee9351e6a8 | 3fc27f7fdf20e624ff5a1e8d45bf660d20afe7a2999613c193fdfdee9351e6a8 | 2581/2581 |
| reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_1000/audit_report.json | c74177a57b71509dcf78d543f0b076b55a40bcd0eb9e6c0a1a9c61ef631c65f6 | c74177a57b71509dcf78d543f0b076b55a40bcd0eb9e6c0a1a9c61ef631c65f6 | 7883/7883 |
| reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_50000/audit_report.json | 9dcc464801ca07244634c37b4f2cb8a88fd74c8b6aa34d042af171c3e41b62f9 | 9dcc464801ca07244634c37b4f2cb8a88fd74c8b6aa34d042af171c3e41b62f9 | 7919/7919 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/warning_definition.json | 5ffb784183646d1c320f850f1ce1b50abf2d7b3e4495b45653c586745316c626 | 5ffb784183646d1c320f850f1ce1b50abf2d7b3e4495b45653c586745316c626 | 46793/46793 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.json | 508d35b879863e2fe17d8f716f9112d99f19a62abb8762a42656ddabb1473331 | 508d35b879863e2fe17d8f716f9112d99f19a62abb8762a42656ddabb1473331 | 16685/16685 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.csv | 501f3eb4142993248b2584996300cb2c6104f013f1a207730ab641e0ef52fd30 | 501f3eb4142993248b2584996300cb2c6104f013f1a207730ab641e0ef52fd30 | 6860/6860 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/clock_delta_statistics.json | 3cfd42cbea8d52054662c47eebb05a6b46480e841de390dcc8c92ebb7e3d6a28 | 3cfd42cbea8d52054662c47eebb05a6b46480e841de390dcc8c92ebb7e3d6a28 | 582405/582405 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/timestamp_gap_analysis.json | 50f5f4ab3322f7dc4fca70911fc53bf9313093de628f3a74b08967dcbc239c2b | 50f5f4ab3322f7dc4fca70911fc53bf9313093de628f3a74b08967dcbc239c2b | 49832/49832 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/field_usage_matrix.json | b6d661941a78a413d4c737934d5a058a598bd0851582bd371f133d5359ad9d91 | b6d661941a78a413d4c737934d5a058a598bd0851582bd371f133d5359ad9d91 | 18971/18971 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/phase2_time_rules.json | fc9f5151193a94dd5b80f1a07f19e245e169fb87fd095e71c79605e892204db6 | fc9f5151193a94dd5b80f1a07f19e245e169fb87fd095e71c79605e892204db6 | 6107/6107 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/final_integrity_check.json | aa2d64a05fff93156bd4d77aa5c6cbe45df0207844826965dfdeca7a09ef975a | aa2d64a05fff93156bd4d77aa5c6cbe45df0207844826965dfdeca7a09ef975a | 3186/3186 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/source_timestamp_semantics.json | 565d5b39a5ef6a46806d8775d280c5a62a9229a3aa3e6a384a96991d0905bec1 | 565d5b39a5ef6a46806d8775d280c5a62a9229a3aa3e6a384a96991d0905bec1 | 145673/145673 |
| reference/hft_phase1/20261018T214147Z/timestamp_review/warning_cause_classification.json | e1e94ce320a5a45fcd720377db8f7f8866c47838711de5c34dde1aeb5ef59e44 | e1e94ce320a5a45fcd720377db8f7f8866c47838711de5c34dde1aeb5ef59e44 | 8536/8536 |
| reference/hft_phase1/20261018T214147Z/manifests/recovery_recommended_action.json | 2b6f30269d349d83bed84f7c19acb29da8272165fbcddef8a1bfd133b7c9b25d | 2b6f30269d349d83bed84f7c19acb29da8272165fbcddef8a1bfd133b7c9b25d | 4455/4455 |
| reference/hft_phase1/20261018T214147Z/manifests/recovery_suspicious_file_report.json | d687b92a9eec0ff6948f6e4e2ee86a85e25925796d7be4b1b412fc855db6ff8f | d687b92a9eec0ff6948f6e4e2ee86a85e25925796d7be4b1b412fc855db6ff8f | 25410/25410 |
| reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_check.json | b3038a307c4784c38b00adab9ae38f7b2591c383e94855614de7dde9bc8880b3 | b3038a307c4784c38b00adab9ae38f7b2591c383e94855614de7dde9bc8880b3 | 355357/355357 |
| reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_review.json | 93173785a78c922d1e60e048902c9f7b42ab11712a9361930a952755c71c1e4f | 93173785a78c922d1e60e048902c9f7b42ab11712a9361930a952755c71c1e4f | 42225/42225 |
| reference/hft_phase1/20261018T214147Z/reports/RECOVERY_FINAL_INTEGRITY_REVIEW_20261018T202030Z.md | 1ab770a000608c64195700ce156f013550fe0f7b2a5cf695e0193cc8f7c1d227 | 1ab770a000608c64195700ce156f013550fe0f7b2a5cf695e0193cc8f7c1d227 | 1375/1375 |
| reference/hft_phase1/20261018T214147Z/audits/DATASET_AUDIT.md | 955c010f38a504ca39e2b7c96a1bbbc147ad56e1dd6b8df764d2b2026a02acb2 | 955c010f38a504ca39e2b7c96a1bbbc147ad56e1dd6b8df764d2b2026a02acb2 | 6009/6009 |

全部一致，複製以xb拒覆寫，目的重新讀取雜湊。verify工具也只重新核對這些允許的報告/Manifest，沒有對市場來源重掃。

## 10. 缺失與未可用資料

必要交接檔缺失0，missing_files=[]。資料語義缺口仍保留：兩Snapshot無event time、歷史collector session_id/producer identity、真實receive/stage timestamp、逐字WebSocket payload及完整Book獨立重建證據均未補造。

## 11. data_sources.json

[data_sources.json](/home/jason/quantum-hft/configs/data_sources.json)：read_only，HFT write/network/real/testnet/cross-session均false，event_time_ms排序，九來源只登錄原唯讀路徑。hash/size/status/time全取既有Audit/Review，本次未開啟市場原檔。

| 來源 | 類型 | audit | 研究Session別名 | event起/末 ms |
| --- | --- | --- | --- | --- |
| results/obi_market_data_20260827_session1.csv | csv | WARNING | csv_file_obi_market_data_20260827_session1 | 1787767099114 / 1787773157814 |
| results/obi_market_data_20260827_session2.csv | csv | WARNING | csv_file_obi_market_data_20260827_session2 | 1787773384514 / 1787783377014 |
| results/obi_market_data_20260827_session3.csv | csv | WARNING | csv_file_obi_market_data_20260827_session3 | 1787808550014 / 1787814356615 |
| results/obi_market_data_test_20260827.csv | csv | WARNING | csv_file_obi_market_data_test_20260827 | 1787765781314 / 1787765876414 |
| results/obi_market_data.csv | csv | WARNING | csv_file_obi_market_data | 1791238160414 / 1791243186114 |
| results/replay_snapshot_1000.json | snapshot | PASS | replay_pair_1000 | None / None |
| results/replay_events_1000.jsonl | replay | PASS | replay_pair_1000 | 1789974146914 / 1789974246814 |
| results/replay_snapshot_50000.json | snapshot | PASS | replay_pair_50000 | None / None |
| results/replay_events_50000.jsonl | replay | PASS | replay_pair_50000 | 1789975886114 / 1789980886114 |

研究Session別名不是已證實collector session_id；Snapshot時間保持null/NOT_AVAILABLE。8月CSV、9月Replay、10月obi_market_data各自隔離。

## 12. timestamp_policy.json

[timestamp_policy.json](/home/jason/quantum-hft/configs/timestamp_policy.json)：event排序、Session隔離、不跨檔；local非receive、禁feature/network/Tick-to-Trade。四horizon為100/200/500/1000ms；必存requested/actual/target/error/valid/reason。

max_match_error_ms=null，selection_status=TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL；gap門檻同樣未定。不能用Final Holdout選門檻。舊提案不覆寫，以新政策為準。

## 13. 資料契約

[HFT_INPUT_DATA_CONTRACT.md](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)區分已證實、可計算、缺失、禁止、Phase2待驗證。CSV僅BBO與五檔總量/OBI，不能捏造逐檔價量。Snapshot+Replay條件可重建，需Phase2B逐事件與獨立實作驗證完整可知Book；非已完成結果。ACK≠fill、backtest≠Live Broker、affinity≠isolation均保留證據界限。

## 14. verify_handoff結果

第一次正式驗證exit=0；原始輸出：[verify_initial.stdout.txt](/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/verify_initial.stdout.txt)、[verify_initial.stderr.txt](/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/verify_initial.stderr.txt)、[verify_initial.json](/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/verify_initial.json)。

```text
[PASS] manifest: required metadata and fixed safety declarations
[PASS] copy: reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/reports/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/reports/PHASE1_RECOVERY_REPORT_20261018T202030Z.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_baseline_protected_files_manifest.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_protected_files_manifest.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/manifests/phase1_v2_final_integrity_summary.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/environment/phase1_v2_environment.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_unit_test_summary.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_execution_summary.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/phase1_v2_dataset_audit_verification.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/environment/phase1_v2_cmake_static_safety.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/environment/phase1_v2_build_execution.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session1/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session2/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_20260827_session3/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data_test_20260827/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/obi_market_data/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_1000/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_events_1000/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_snapshot_50000/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/replay_events_50000/audit_report.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_1000/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/snapshot_replay_pair_50000/audit_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/warning_definition.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/csv_timestamp_summary.csv
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/clock_delta_statistics.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/timestamp_gap_analysis.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/field_usage_matrix.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/phase2_time_rules.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/final_integrity_check.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/source_timestamp_semantics.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/timestamp_review/warning_cause_classification.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/manifests/recovery_recommended_action.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/manifests/recovery_suspicious_file_report.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_check.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/manifests/recovery_final_integrity_review.json
[PASS] copy: reference/hft_phase1/20261018T214147Z/reports/RECOVERY_FINAL_INTEGRITY_REVIEW_20261018T202030Z.md
[PASS] copy: reference/hft_phase1/20261018T214147Z/audits/DATASET_AUDIT.md
[PASS] copied_total_size_bytes: 2822328
[PASS] data_sources: nine metadata records; raw inputs were not opened
[PASS] timestamp_policy: event ordering and unresolved thresholds preserved
[PASS] experiment_defaults: execution and overwrite gates disabled
[PASS] project_scan_completed: 84 regular files inspected
[WARNING] inherited_timestamp_status: Timestamp Review remains WARNING; Phase 2 is PASS_WITH_RESTRICTIONS, not executed
HANDOFF VERIFICATION PASS; failures=0; warnings=1

```

報告與全部ledger完成後再執行一次相同唯讀verify，結果保存verify_final.json。最終聊天只以該次實際exit=0及末次來源metadata一致才宣告PASS；若失敗則停止並標FAIL，不刪除證據。驗證的credential檢查是已記錄格式的靜態偵測，不聲稱能證明任意未知編碼中沒有隱藏secret。

## 15. unittest結果

正式命令：PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_verify_handoff.py；cwd=/home/jason/quantum-hft；exit=0。

```text
.........................................
----------------------------------------------------------------------
Ran 41 tests in 0.116s

OK

```

人工資料只在tests/TemporaryDirectory建立並清理；沒有讀HFT市場檔。覆蓋正常、缺檔、hash不符、各安全旗標、receive誤用、.env、ELF、src/results混入、既有run與非空project拒覆寫，以及path/symlink/credential/raw資料例外等。完整紀錄：[unittest_initial.json](/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/unittest_initial.json)。這些是交接工具測試，不是交易/模型/Phase2測試。

## 16. HFT來源未修改

本次所有寫入限定新quantum-hft；來源1545既存葉節點的before/after metadata全一致（無新增/缺失/改名/大小、mode、mtime、ctime或link target變更），見[hft_source_metadata_before.json](/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/hft_source_metadata_before.json)與[hft_source_metadata_after.json](/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/hft_source_metadata_after.json)。兩保留資料夾未寫入。

尊重不得重新掃市場資料的限制，未重算市場檔hash；不能把metadata核對誤稱市場SHA重驗。交接報告與Manifest各自SHA均驗證。

## 17. 未複製市場原始資料

只複製48份非執行研究證據；九市場來源未開啟內容、未copy、不建立指向results的symlink、不改mount。新專案沒有src/或results/。

## 18. 專題網路活動

false。沒有連Binance REST/WebSocket/Testnet、查外部文獻網站、curl/wget、下載或套件安裝。Codex/OpenAI服務連線不屬專題網路活動。

## 19. 交易活動

false。沒有Testnet或真實下單、API/Secret使用、HFT binary、Live Collector、Capture、Benchmark或Replay binary執行。

## 20. 模型與實驗

model_training=false、backtesting=false、paper_trading=false。沒有Quantum Kernel、QSVC、QUBO、QAOA、kernel matrix或任何模型檔。文獻矩陣空白、研究缺口為PROVISIONAL RESEARCH GAP — REQUIRES LITERATURE VERIFICATION，沒有虛構DOI。experiment_defaults禁止所有當前研究執行。

## 21. Phase 2順序

2A唯讀Adapter/Registry → 2B獨立Order Book重建 → 2C特徵 → 2D標籤 → 2E時間切分與防洩漏 → 2F版本化資料集。只有計畫，沒有實作；Phase2完成仍不得訓練模型。[PHASE2_PLAN.md](/home/jason/quantum-hft/docs/PHASE2_PLAN.md)。

後續Phase3經典與統一回測、Phase4Kernel/QSVC、Phase5QUBO/QAOA、Phase6自動搜尋重訓、Phase7本機Paper，逐階人工驗收。

## 22. 尚未執行

沒有市場重掃、Book重建、feature/label生成、Training profile、threshold選定、split/dataset輸出、文獻查詢、模型/量子實驗、策略搜尋、回測或Paper Trading。新資料夾可供人工建立新的Codex Project，本次沒有自動建立或移動任何Codex chat/project。

## 23. 所有實際命令

[command_history.txt](/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/command_history.txt)及root/discovery/docs/verifier ledgers保存完整命令與工具結果；正式unittest與verify另分stdout/stderr與exit。工具Add File、權限不足的新增嘗試、過長argument未能啟動等均保留，不抹除開發歷程。

<details><summary>root #1 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os
p='/mnt/c/Users/jason/.codex/attachments/906fe69f-ee25-4fc9-8af5-9de6e180e02f/貼上的文字.txt'
with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r',encoding='utf-8') as f:
 print(f.read())
PY
```

</details>

<details><summary>root #2 / exit 0</summary>

```bash
pwd
realpath .
findmnt -T .
python3 -B - <<'PY'
import os,stat,json
p='/home/jason/quantum-hft'
print(json.dumps({'target':p,'lexists':os.path.lexists(p),'is_symlink':os.path.islink(p),'empty_if_directory':not os.listdir(p) if os.path.isdir(p) and not os.path.islink(p) else None},ensure_ascii=False))
PY
```

</details>

<details><summary>root #3 / exit 0</summary>

```bash
mkdir -- /home/jason/quantum-hft
```

</details>

<details><summary>root #4 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os,stat,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path('/home/jason/hft-realtime-codex')
print('AGENTS:')
with os.fdopen(os.open(root/'AGENTS.md',os.O_RDONLY|os.O_NOATIME),'r') as f:print(f.read())
def walk(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_NOATIME)
 try:
  with os.scandir(fd) as it:names=sorted(e.name for e in it)
 finally:os.close(fd)
 for n in names:
  q=p/n;s=q.lstat()
  if stat.S_ISDIR(s.st_mode):yield from walk(q)
  else:yield {'relative_path':str(q.relative_to(root)),'mode':s.st_mode,'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,'symlink_target':os.readlink(q) if stat.S_ISLNK(s.st_mode) else None}
entries=list(walk(root))
d={'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_root':str(root),'method':'lstat only; no raw market reads, no symlink traversal, no FIFO open','entries':entries,'entry_count':len(entries),'metadata_digest':hashlib.sha256(json.dumps(entries,sort_keys=True).encode()).hexdigest()}
p=Path('/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z')
p.mkdir(parents=True,exist_ok=True)
with open(p/'hft_source_metadata_before.json','x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in d.items() if k!='entries'},ensure_ascii=False))
PY
```

</details>

<details><summary>root #5 / exit 0</summary>

```bash
python3 -B - <<'PY'
from pathlib import Path
r=Path('/home/jason/quantum-hft')
assert r.is_dir() and not r.is_symlink() and r.resolve()==r
for d in ['configs','data_contract','data_pipeline','models/classical','models/quantum','optimization/classical','optimization/qubo','optimization/qaoa','backtesting','paper_trading','automation','tools','tests','artifacts','reports','references','docs','reference/hft_phase1']:
 p=r/d
 assert not p.is_symlink()
 p.mkdir(parents=True,exist_ok=True)
print('指定新專案結構目錄已建立；沒有新增HFT來源檔案。')
PY
```

</details>

<details><summary>root #6 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os,json
from pathlib import Path
for p in [Path('/home/jason/quantum-hft/tools/handoff_guard.py')]:
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:print(f.read())
r=Path('/home/jason/hft-realtime-codex')
p=r/'artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json'
with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:d=json.load(f)
print('TOP_KEYS',list(d))
for x in d['datasets']:
 print('DATASET_KEYS',list(x))
 a=x['file_audit'];print(json.dumps({k:v for k,v in a.items() if k not in ['checks','anomaly_samples','samples','examples']},ensure_ascii=False)[:2000])
PY
```

</details>

<details><summary>root #7 / exit 0</summary>

```bash
python3 -B - <<'PY'
import json,os
from pathlib import Path
p=Path('/home/jason/quantum-hft/artifacts/handoff_setup/20261018T214147Z/handoff_discovery.json')
with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:d=json.load(f)
print('TOP',list(d))
print('MAP0',d['copy_mapping'][0])
print('MAPS',json.dumps([{k:v for k,v in x.items() if k in ['source_relative_path','destination_relative_path','category','logical_item','id','required']} for x in d['copy_mapping']],ensure_ascii=False))
print('REGISTRY',json.dumps(d['dataset_registry_metadata'],ensure_ascii=False))
PY
```

</details>

<details><summary>root #8 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os,stat,json,hashlib,sys,time
from pathlib import Path
from datetime import datetime,timezone
SRC=Path('/home/jason/hft-realtime-codex');DST=Path('/home/jason/quantum-hft')
ID='20261018T214147Z';SETUP=DST/'artifacts/handoff_setup'/ID
assert Path.cwd()==SRC and SRC.resolve()==SRC and DST.resolve()==DST
def raw(p):
 for x in [p,*p.parents]:
  if x.is_symlink():raise RuntimeError('symlink source')
 if not stat.S_ISREG(p.lstat().st_mode):raise RuntimeError('not regular')
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME),'rb') as f:return f.read()
def j(p):return json.loads(raw(p))
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 with open(p,'x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
d=j(SETUP/'handoff_discovery.json')
extra=j(SETUP/'handoff_discovery_supplement.json')
mapping=d['copy_mapping']+extra['copy_mapping']
assert len({x['destination_relative_path'] for x in mapping})==len(mapping)
buffers=[]
for x in mapping:
 s=Path(x['source_absolute_path']);p=DST/x['destination_relative_path']
 assert s==SRC/x['source_relative_path'] and s.is_relative_to(SRC)
 assert s.parts[len(SRC.parts)] in ['docs','artifacts'] and s.suffix.lower() in ['.json','.md','.csv']
 if s.suffix=='.csv':assert s.name=='csv_timestamp_summary.csv' and 'phase1_timestamp_review' in s.parts
 assert p.is_relative_to(DST/'reference/hft_phase1'/ID) and '..' not in Path(x['destination_relative_path']).parts
 b=raw(s);h=hashlib.sha256(b).hexdigest()
 if h!=x['source_sha256'] or len(b)!=x['source_size_bytes']:
  write(SETUP/'copy_failure.json',{'status':'FAIL','source':str(s),'reason':'source differs since discovery'});raise RuntimeError('source hash changed')
 assert not b.startswith(b'\x7fELF')
 buffers.append((x,p,b))
sys.path.insert(0,str(DST/'tools'))
from handoff_guard import create_unique_handoff_run
r=create_unique_handoff_run(DST,ID)
for cat in ['reports','manifests','audits','timestamp_review','environment']:(r/cat).mkdir()
copied=[];start=time.monotonic()
for i,(x,p,b) in enumerate(buffers,1):
 p.parent.mkdir(parents=True,exist_ok=True)
 with open(p,'xb') as f:f.write(b)
 dh=hashlib.sha256(raw(p)).hexdigest()
 item={k:x[k] for k in ['source_absolute_path','source_relative_path','destination_relative_path','source_sha256','source_size_bytes']}
 item.update({'destination_sha256':dh,'destination_size_bytes':p.stat().st_size,'copy_status':'PASS' if dh==x['source_sha256'] else 'FAIL','category':x['category'],'evidence_run_id':x.get('expected_run_id'),'content_run_verification':x.get('run_id_verification'),'artifact_content_status':x.get('artifact_content_status'),'required':x.get('required',False)})
 copied.append(item)
 if item['copy_status']!='PASS':
  write(r/'HANDOFF_MANIFEST.json',{'schema_version':'1.0','handoff_run_id':ID,'status':'FAIL','copied_files':copied,'all_hashes_match':False});raise RuntimeError('copy mismatch; stopped')
 if i==len(buffers) or i%10==0:
  elapsed=time.monotonic()-start
  print(f'copy {i}/{len(buffers)} {100*i/len(buffers):.1f}% elapsed={elapsed:.3f}s ETA={elapsed*(len(buffers)-i)/i:.3f}s')
registry=[]
for x in d['dataset_registry_metadata']:
 row={k:x[k] for k in ['relative_path','absolute_path','file_type','sha256','size_bytes','audit_status','event_time_start','event_time_end']}
 row.update({'session_id':x['session_id_proposed_registry_alias'],'session_id_semantics':'research registry alias only; historical collector session_id NOT_AVAILABLE',
 'original_capture_session_id':'NOT_AVAILABLE','event_time_unit':'ms','event_time_availability':x['event_time_availability'],
 'metadata_evidence':{'source_audit_relative_path':x['source_audit_relative_path'],'copied_audit_relative_path':x['copied_audit_relative_path'],'phase1_v2_run_id':'20261018T210029Z'},
 'allowed_uses':['read_only_future_phase2_after_approval','event_time_order_within_research_session','conditional_feature_and_label_research'] if x['file_type']=='csv' else ['read_only_future_phase2_after_approval','paired_snapshot_replay_reference_book_validation'],
 'prohibited_uses':['source_write','cross_file_labels','cross_session_labels','network_latency','tick_to_trade_latency','live_or_testnet_order','training_or_backtesting_in_this_task'],
 'known_limitations':list(x['limits'])+(['aggregated five-level volume only; no individual five price/quantity levels','local timestamp not reliable receive; historical exact producer UNKNOWN','snapshot/Replay from September cannot be merged with August/October CSV'] if x['file_type']=='csv' else ['normalized market structure; original websocket bytes not preserved','full Book reconstruction correctness pending Phase 2B','paired snapshot identity is inferred from audited update-ID alignment, not collector session metadata'])})
 if x['file_type']=='snapshot':row['known_limitations'].append('Snapshot event_time_start/end unavailable; must stay null, not substitute Replay time')
 if x['file_type']=='csv':row['timestamp_review_evidence']='reference/hft_phase1/'+ID+'/timestamp_review/csv_timestamp_summary.json'
 registry.append(row)
missing=d['missing_files']+extra.get('missing_files',[])
manifest={'schema_version':'1.0','handoff_run_id':ID,'created_at_utc':datetime.now(timezone.utc).isoformat(),
 'source_project':str(SRC),'destination_project':str(DST),'phase1_v2_run_id':'20261018T210029Z','timestamp_review_run_id':'20261018T212122Z','recovery_run_id':'20261018T202030Z',
 'phase1_v2_status':'PASS','timestamp_review_status':'WARNING','phase2_decision':'PASS_WITH_RESTRICTIONS',
 'copied_files':copied,'missing_files':missing,
 'excluded_paths':['src/','analysis/','scripts/','results/','all raw market CSV/JSONL/snapshots','ELF','build products','*.tar.gz','*.7z','.env','credentials/private keys','Testnet/Live/Capture programs','kernel matrices','models'],
 'csv_summary_exception':'Only explicitly requested csv_timestamp_summary.csv is copied; it is an aggregate review report, never raw market CSV.',
 'read_only_input_paths':[x['absolute_path'] for x in registry],'copied_file_count':len(copied),'copied_total_size_bytes':sum(x['destination_size_bytes'] for x in copied),'all_hashes_match':True,
 'hft_source_modified':False,'network_activity_performed':False,'trading_activity_performed':False,'model_training_performed':False,'backtesting_performed':False,'paper_trading_performed':False,
 'market_data_copied':False,'market_data_rescanned':False,'raw_data_sha_verification_this_task':'NOT_PERFORMED; registry hashes taken from existing audited evidence as requested',
 'historical_status_caveats':d['historical_status_caveats'],'source_immutability_evidence':'artifacts/handoff_setup/'+ID+'/hft_source_metadata_before.json',
 'status':'HASH_VERIFIED_HANDOFF_EVIDENCE; final acceptance requires verifier, tests, report and source metadata check'}
write(r/'HANDOFF_MANIFEST.json',manifest)
data={'schema_version':'1.0','access_mode':'read_only','hft_project':str(SRC),'hft_results':str(SRC/'results'),'handoff_directory':str(r.relative_to(DST)),
 'phase1_v2_run_id':'20261018T210029Z','timestamp_review_run_id':'20261018T212122Z','allow_hft_write':False,'allow_network':False,'allow_real_trading':False,'allow_testnet_trading':False,'allow_cross_session_labels':False,
 'time_order_field':'event_time_ms','local_timestamp_policy':'not_receive_time_do_not_use_for_latency','sources':registry}
write(DST/'configs/data_sources.json',data)
policy={'schema_version':'1.0','ordering_field':'event_time_ms','session_isolation':True,'cross_session_labels':False,'cross_file_labels':False,
 'local_timestamp_is_receive_time':False,'local_timestamp_allowed_as_feature':False,'local_timestamp_allowed_for_network_latency':False,'local_timestamp_allowed_for_tick_to_trade':False,
 'record_actual_horizon':True,'record_match_error':True,'invalidate_on_large_gap':True,'invalidate_session_tail':True,'require_clock_source_metadata':True,'horizons_ms':[100,200,500,1000],
 'required_label_fields':['requested_horizon_ms','actual_horizon_ms','target_event_time_ms','match_error_ms','valid_label','invalid_reason'],
 'max_match_error_ms':None,'selection_status':'TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL','allow_final_holdout_for_selection':False,
 'large_gap_threshold_ms':None,'gap_selection_status':'TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL',
 'old_proposal_note':'Copied timestamp review preserves 25ms / >200ms as historical proposals; neither is a final parameter in this new project.',
 'matching_proposal':'first event at/after t+h inside same segment; actual horizon and match error explicit; no interpolation',
 'historical_local_semantics':'Not proven receive; current candidate source paths sample after book update. Policy forbids receive/latency use.',
 'implementation_status':'SPECIFICATION_ONLY; no Phase 2 dataset builder'}
write(DST/'configs/timestamp_policy.json',policy)
defaults={'schema_version':'1.0','current_stage':'HANDOFF_AND_SPECIFICATION_ONLY','allow_hft_write':False,'allow_network':False,'allow_real_trading':False,'allow_testnet_trading':False,
 'allow_model_training':False,'allow_backtesting':False,'allow_paper_trading':False,'allow_phase2_execution':False,'require_human_approval':True,'overwrite_existing_outputs':False,
 'random_seed':42,'current_execution_seed':None,'seed_note':'42 is a future configurable experiment default; no random experiment executed now.',
 'output_root':'/home/jason/quantum-hft','require_unique_run_id':True,'record_source_sha256':True,'record_code_version':True,'record_parameters':True,'record_environment':True,
 'time_split_only':True,'shuffle_before_split':False,'scaler_fit':'training_only','purge_overlapping_labels':True,'final_holdout_for_search':False,
 'model_approval':'human_only; Codex cannot approve its own model','max_match_error_ms':None}
write(DST/'configs/experiment_defaults.json',defaults)
print(json.dumps({'status':'COPIED_AND_CONFIGURED','run_id':ID,'files':len(copied),'bytes':manifest['copied_total_size_bytes'],'hashes_match':True,'sources':len(registry),'missing':missing},ensure_ascii=False))
PY
```

</details>

<details><summary>root #9 / exit 0</summary>

```bash
python3 -B - <<'PY'
from pathlib import Path
import os,json
r=Path('/home/jason/quantum-hft')
print('FILES')
for p in sorted(r.rglob('*')):
 if p.is_file() and 'reference/hft_phase1' not in str(p) and 'artifacts/handoff_setup' not in str(p): print(str(p.relative_to(r)),p.stat().st_size)
p=r/'tools/verify_handoff.py'
if p.exists():
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:s=f.read()
 print('VERIFIER_LINES',len(s.splitlines()))
 print(s)
PY
```

</details>

<details><summary>root #10 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os
from pathlib import Path
r=Path('/home/jason/quantum-hft')
for n in ['AGENTS.md','README.md','data_contract/HFT_INPUT_DATA_CONTRACT.md','docs/PHASE2_PLAN.md','docs/EXPERIMENT_PROTOCOL.md']:
 with os.fdopen(os.open(r/n,os.O_RDONLY|os.O_NOATIME),'r') as f:s=f.read()
 print('DOCUMENT',n)
 print(s)
PY
```

</details>

<details><summary>root #11 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os,subprocess,json,time
from pathlib import Path
from datetime import datetime,timezone
r=Path('/home/jason/quantum-hft');out=r/'artifacts/handoff_setup/20261018T214147Z'
commands=[('unittest_initial',['python3','-m','unittest','tests/test_verify_handoff.py']),('verify_initial',['python3','tools/verify_handoff.py','--manifest','reference/hft_phase1/20261018T214147Z/HANDOFF_MANIFEST.json'])]
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
for name,args in commands:
 assert all(not (out/(name+s)).exists() for s in ['.stdout.txt','.stderr.txt','.json'])
 started=datetime.now(timezone.utc).isoformat();t=time.monotonic()
 p=subprocess.run(args,cwd=r,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 for suffix,b in [('.stdout.txt',p.stdout),('.stderr.txt',p.stderr)]:
  with open(out/(name+suffix),'xb') as f:f.write(b)
 record={'command':args,'display_command':'PYTHONDONTWRITEBYTECODE=1 '+' '.join(args),'cwd':str(r),'started_utc':started,'elapsed_seconds':time.monotonic()-t,'exit_code':p.returncode,'stdout_file':str((out/(name+'.stdout.txt')).relative_to(r)),'stderr_file':str((out/(name+'.stderr.txt')).relative_to(r)),'stdout':p.stdout.decode('utf-8',errors='replace'),'stderr':p.stderr.decode('utf-8',errors='replace')}
 with open(out/(name+'.json'),'x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
 print(json.dumps({'name':name,'exit_code':p.returncode,'stdout':record['stdout'],'stderr':record['stderr']},ensure_ascii=False))
 if p.returncode!=0:raise SystemExit(p.returncode)
PY
```

</details>

<details><summary>handoff_discovery_commands.json #1 / exit 0</summary>

```bash
cat /mnt/c/Users/jason/.codex/attachments/906fe69f-ee25-4fc9-8af5-9de6e180e02f/貼上的文字.txt
```

</details>

<details><summary>handoff_discovery_commands.json #2 / exit 0</summary>

```bash
rg --files docs artifacts | rg '20261018T(210029|212122|202030)Z'
```

</details>

<details><summary>handoff_discovery_commands.json #3 / exit 0</summary>

```bash
python3 -B - <<'PY'
import pathlib,json,os
root=pathlib.Path('.')
paths=['docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md','docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md','docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md']
for p in paths:
 print('\n###',p)
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:
  for n,line in enumerate(f,1):
   if n<45 or any(t in line for t in ['environment.json','dataset_unit_test','cmake_static','build_execution','final_integrity','protected_files_manifest','snapshot','Snapshot','逐字','ACK','affinity','隔離','receive','Session','PASS_WITH_RESTRICTIONS']):print(f'{n}: {line.rstrip()}')
print('\nENV PATHS')
for p in (root/'artifacts/phase1_v2/20261018T210029Z').rglob('environment.json'): print(p)
PY
```

</details>

<details><summary>handoff_discovery_commands.json #4 / exit 0</summary>

```bash
python3 -B - <<'PY'
import json,os,pathlib
paths=['artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.json','artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.json','artifacts/phase1_v2/20261018T210029Z/final/final_integrity_summary.json','artifacts/phase1_v2/20261018T210029Z/environment/environment.json','artifacts/phase1_v2/20261018T210029Z/tests/dataset_unit_test_summary.json','artifacts/phase1_v2/20261018T210029Z/build/cmake_static_safety.json','artifacts/phase1_v2/20261018T210029Z/build/build_execution.json','artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json','artifacts/phase1_timestamp_review/20261018T212122Z/csv_timestamp_summary.json','artifacts/phase1_recovery/20261018T202030Z/recommended_action.json','artifacts/phase1_recovery/20261018T202030Z/suspicious_file_report.json','artifacts/phase1_recovery/20261018T202030Z/final_integrity_check.json']
for p in paths:
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:d=json.load(f)
 print('\n',p,'KEYS',list(d) if isinstance(d,dict) else type(d).__name__)
 if isinstance(d,dict):
  for k,v in d.items():
   if not isinstance(v,(dict,list)): print(k, str(v)[:400])
   elif k in ('files','datasets','executions','summaries'): print(k,'COUNT',len(v),'FIRST',str(v[0] if isinstance(v,list) and v else v)[:1400])
PY
```

</details>

<details><summary>handoff_discovery_commands.json #5 / exit 0</summary>

```bash
python3 -B - <<'PY'
import json,os
R='artifacts/phase1_v2/20261018T210029Z/'
paths=[R+'audits/dataset_execution_summary.json','artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json','artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.json',R+'baseline/protected_files_manifest.json','artifacts/phase1_recovery/20261018T202030Z/final_integrity_review.json']
for p in paths:
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:d=json.load(f)
 print('\n###',p)
 if 'dataset_execution' in p:
  for item in d['datasets']: print(json.dumps({k:v for k,v in item.items() if k!='execution'},ensure_ascii=False))
 elif 'protected_files' in p: print(json.dumps(d['context'],ensure_ascii=False))
 else: print(json.dumps(d,ensure_ascii=False)[:22000])
PY
```

</details>

<details><summary>handoff_discovery_commands.json #6 / exit 0</summary>

```bash
python3 -B - <<'PY'
import json,os

def rd(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:return json.load(f)
d=rd('artifacts/phase1_v2/20261018T210029Z/audits/dataset_execution_summary.json')
for x in d['datasets']:
 a=x['file_audit'];print(json.dumps({k:a[k] for k in ['path','kind','status','sha256','size_bytes','records','parse_errors','metrics']},ensure_ascii=False))
for p in ['artifacts/phase1_v2/20261018T210029Z/baseline/protected_files_manifest.json','artifacts/phase1_v2/20261018T210029Z/final/protected_files_manifest.json']:
 print(p,json.dumps(rd(p)['context'],ensure_ascii=False))
p='artifacts/phase1_recovery/20261018T202030Z/final_integrity_review.json';q=rd(p);print(p,json.dumps({k:v for k,v in q.items() if not isinstance(v,(list,dict))},ensure_ascii=False))
p='artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json';q=rd(p);print('AUDIT KEYS',list(q))
print('AUDITTOP',json.dumps({k:v for k,v in q.items() if not isinstance(v,(list,dict))},ensure_ascii=False))
PY
```

</details>

<details><summary>handoff_discovery_commands.json #7 / exit 0</summary>

```bash
python3 -B - <<'PY'
import json,os,pathlib

def rd(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:return f.read()
for p in ['artifacts/phase1_timestamp_review/20261018T212122Z/phase2_time_rules.json','artifacts/phase1_timestamp_review/20261018T212122Z/field_usage_matrix.json','artifacts/phase1_timestamp_review/20261018T212122Z/timestamp_gap_analysis.json']:
 d=json.loads(rd(p));print(p,'KEYS',list(d));print({k:v for k,v in d.items() if not isinstance(v,(dict,list))})
p='docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md'
for n,line in enumerate(rd(p).splitlines(),1):
 if n<240 and any(t in line for t in ['241','Session','local_timestamp','receive','逐','前五','gap','13.327','UNKNOWN','25ms','200ms']): print(n,line[:700])
print('DOC FILES')
for p in pathlib.Path('docs').iterdir():
 if p.is_file(): print(p.name)
PY
```

</details>

<details><summary>handoff_discovery_commands.json #8 / exit 0</summary>

```bash
python3 -B - <<'PY'
import json,os

def rd(p):
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOATIME),'r') as f:return f.read()
for p in ['docs/DATASET_AUDIT.md','docs/BUILD_BASELINE.md','docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md']:
 print('\n###',p)
 for n,line in enumerate(rd(p).splitlines(),1):
  if n<210 and any(t in line for t in ['receive','CSV','Snapshot','snapshot','JSONL','ACK','逐字','Paper','affinity','CPU','Session']):print(n,line[:900])
for p in ['artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json','artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_snapshot_1000/audit_report.json']:
 d=json.loads(rd(p));print('\n###',p);print(json.dumps(d.get('parameters'),ensure_ascii=False));print(json.dumps({k:v for k,v in d['metadata'].items() if not isinstance(v,(dict,list))},ensure_ascii=False));print('checks', list(d['files'][0]['checks']))
PY
```

</details>

<details><summary>handoff_discovery_commands.json #9 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os,json,pathlib,hashlib,datetime,stat
S=pathlib.Path('/home/jason/hft-realtime-codex'); D=pathlib.Path('/home/jason/quantum-hft'); rid='20261018T214147Z'; base='reference/hft_phase1/'+rid+'/'
V='artifacts/phase1_v2/20261018T210029Z/'; T='artifacts/phase1_timestamp_review/20261018T212122Z/'; R='artifacts/phase1_recovery/20261018T202030Z/'
def read(p):
 p=S/p
 if not stat.S_ISREG(p.lstat().st_mode): raise ValueError('nonregular '+str(p))
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME),'rb') as f:return f.read()
def js(p):return json.loads(read(p))
items=[]
def add(source,destination,category,run,justification,required=True):
 b=read(source); text=b.decode('utf-8'); parsed=json.loads(text) if source.endswith('.json') else None
 line_hits=[{'line':n,'text':line[:240]} for n,line in enumerate(text.splitlines(),1) if run in line][:5]
 items.append({'source_absolute_path':str(S/source),'source_relative_path':source,'destination_relative_path':base+destination,'category':category,'source_sha256':hashlib.sha256(b).hexdigest(),'source_size_bytes':len(b),'expected_run_id':run,'run_id_literal_present':run in text,'run_id_verification':justification,'run_id_evidence_lines':line_hits,'required':required,'discovery_status':'AVAILABLE','artifact_content_status':parsed.get('status') if isinstance(parsed,dict) else None})
add('docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md','reports/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md','reports','20261018T210029Z','正式報告第3、15行 run_id 與 PASS。')
add('docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md','reports/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md','reports','20261018T212122Z','正式報告第3、17行 WARNING/PASS_WITH_RESTRICTIONS 與 run_id。')
add('docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md','reports/PHASE1_RECOVERY_REPORT_20261018T202030Z.md','reports','20261018T202030Z','正式Recovery報告內容含相同run_id與方案B；保留歷史結論。')
for rel,dest in [('baseline/protected_files_manifest.json','manifests/phase1_v2_baseline_protected_files_manifest.json'),('final/protected_files_manifest.json','manifests/phase1_v2_final_protected_files_manifest.json'),('final/final_integrity_summary.json','manifests/phase1_v2_final_integrity_summary.json'),('environment/environment.json','environment/phase1_v2_environment.json'),('tests/dataset_unit_test_summary.json','audits/phase1_v2_dataset_unit_test_summary.json'),('audits/dataset_execution_summary.json','audits/phase1_v2_dataset_execution_summary.json'),('audits/dataset_audit_verification.json','audits/phase1_v2_dataset_audit_verification.json'),('build/cmake_static_safety.json','environment/phase1_v2_cmake_static_safety.json'),('build/build_execution.json','environment/phase1_v2_build_execution.json')]:
 add(V+rel,dest,dest.split('/')[0],'20261018T210029Z','已解析內容；run關聯由正式v2報告第31/72/84/123/159/558行對應路徑與同run執行摘要確認。',rel!='audits/dataset_audit_verification.json')
summary=js(V+'audits/dataset_execution_summary.json'); ts=js(T+'csv_timestamp_summary.json'); bypath={x['relative_path']:x for x in ts['files']}; datasets=[]
assert summary['run_id']=='20261018T210029Z' and ts['run_id']=='20261018T212122Z'
for x in summary['datasets']:
 report=pathlib.Path(x['report_path']).relative_to(S).as_posix(); audit=js(report); a=x['file_audit']; stem=pathlib.Path(a['path']).stem
 assert audit['run_id']=='phase1v2_20261018T210029Z_'+stem
 assert audit['files'][0]['sha256']==a['sha256'] and audit['files'][0]['size_bytes']==a['size_bytes'] and audit['status']==a['status']
 add(report,'audits/'+stem+'/audit_report.json','audits','20261018T210029Z','audit_report.run_id 精確等於 phase1v2_20261018T210029Z_'+stem+'；來源hash/size/status與執行摘要相同。')
 add(str(pathlib.PurePosixPath(report).with_suffix('.md')),'audits/'+stem+'/audit_report.md','audits','20261018T210029Z','同目錄JSON run_id與MD內容/執行摘要一致。',False)
 m=a['metrics']; t=bypath.get(a['path']); proposed_id='csv_file_'+stem if a['kind']=='csv' else 'replay_pair_'+('50000' if '50000' in stem else '1000')
 if t:assert t['sha256']==a['sha256'] and t['size_bytes']==a['size_bytes'] and t['total_rows']==a['records']
 dates={k:datetime.datetime.fromtimestamp(m[k]/1000,datetime.timezone.utc).isoformat() for k in ['first_event_time_ms','last_event_time_ms'] if k in m}
 datasets.append({'relative_path':a['path'],'absolute_path':str(S/a['path']),'file_type':a['kind'],'sha256':a['sha256'],'size_bytes':a['size_bytes'],'audit_status':a['status'],'records':a['records'],'parse_errors':a['parse_errors'],'event_time_start':m.get('first_event_time_ms'),'event_time_end':m.get('last_event_time_ms'),'event_time_unit':'unix_epoch_milliseconds','event_time_availability':'NOT_AVAILABLE' if 'first_event_time_ms' not in m else 'AVAILABLE','event_times_utc_display':dates,'session_id_proposed_registry_alias':proposed_id,'original_capture_session_id':'NOT_AVAILABLE','session_alias_is_capture_identity':False,'source_audit_relative_path':report,'copied_audit_relative_path':base+'audits/'+stem+'/audit_report.json','metrics':m,'timestamp_review_summary':t,'limits':['不得跨檔或跨Session建標籤','僅唯讀研究輸入；本次未開啟市場檔案','若是Snapshot，event_time null不以Replay時間填補','registry alias是隔離索引，非歷史capture身分證據']})
for size in ['1000','50000']:
 p=V+'audits/snapshot_replay_pair_'+size+'/audit_report.json'; d=js(p)
 assert d['status']=='PASS'
 add(p,'audits/snapshot_replay_pair_'+size+'/audit_report.json','audits','20261018T210029Z','v2報告第152/153/155行對應配對；JSON銜接結果PASS。',False)
for fn in ['warning_definition.json','csv_timestamp_summary.json','csv_timestamp_summary.csv','clock_delta_statistics.json','timestamp_gap_analysis.json','field_usage_matrix.json','phase2_time_rules.json','final_integrity_check.json','source_timestamp_semantics.json','warning_cause_classification.json']:
 add(T+fn,'timestamp_review/'+fn,'timestamp_review','20261018T212122Z','Timestamp Review正式報告引用，JSON run_id內容對應；summary.csv為指定允許的衍生統計，非市場原始CSV。',fn not in ['source_timestamp_semantics.json','warning_cause_classification.json'])
for fn in ['recommended_action.json','suspicious_file_report.json','final_integrity_check.json','final_integrity_review.json']:
 add(R+fn,'manifests/recovery_'+fn,'manifests','20261018T202030Z','Recovery JSON run_id/recovery_run_id 與內容相符；first final_integrity_check FAIL原樣保存，後續review PASS未覆寫前件。',fn!='final_integrity_review.json')
add(R+'FINAL_INTEGRITY_REVIEW.md','reports/RECOVERY_FINAL_INTEGRITY_REVIEW_20261018T202030Z.md','reports','20261018T202030Z','對應同run final_integrity_review.json.review_note_path；既有10個directory symlink覆核補充，非舊Phase1改判。',False)
result={'schema_version':'1.0','handoff_run_id':rid,'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_project':str(S),'destination_project':str(D),'discovery_only':True,'market_files_opened':False,'source_modified':False,'copy_mapping':items,'missing_files':[],'dataset_registry_metadata':datasets,'historical_status_caveats':['Recovery final_integrity_check.json status=FAIL原樣保留；後續final_integrity_review.json status=PASS，係既有directory symlink誤判覆核。','v2報告第137行local_receive術語由Timestamp報告第222行更正；不改舊報告。','Timestamp舊25ms match error與200ms gap僅提案；本次新policy須依使用者要求max_match_error_ms=null。'],'content_evidence':[{'path':'docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md','lines':[3,31,72,84,123,137,152,153,155,159,748]},{'path':'docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md','lines':[3,17,33,37,39,77,164,174,183,216,218,220,222]},{'path':'docs/DATASET_AUDIT.md','lines':[52,53,55,57,59,61]},{'path':'docs/BUILD_BASELINE.md','lines':[20,21,27,30]}]}
assert len(datasets)==9
out=D/'artifacts/handoff_setup'/rid
out.mkdir(parents=True,exist_ok=True)
with (out/'handoff_discovery.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':str(out/'handoff_discovery.json'),'copy_mapping_count':len(items),'dataset_count':len(datasets),'missing_files':[],'source_market_files_opened':False},ensure_ascii=False))
PY
```

</details>

<details><summary>handoff_discovery_commands.json #10 / exit 0</summary>

```bash
python3 -B - <<'PY'
import os,pathlib,json,hashlib,datetime
s=pathlib.Path('/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md')
with os.fdopen(os.open(s,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME),'rb') as f:b=f.read()
assert 'Snapshot' in b.decode() and 'event_time_ms' in b.decode()
rid='20261018T214147Z'
d={'schema_version':'1.0','handoff_run_id':rid,'copy_mapping':[{'source_absolute_path':str(s),'source_relative_path':'docs/DATASET_AUDIT.md','destination_relative_path':'reference/hft_phase1/'+rid+'/audits/DATASET_AUDIT.md','category':'audits','source_sha256':hashlib.sha256(b).hexdigest(),'source_size_bytes':len(b),'expected_run_id':None,'run_id_literal_present':False,'run_id_verification':'通用既有Dataset Audit工具契約；未宣稱由v2 run產生。v2 Dataset執行摘要確認沿用同工具；補充JSON schema與銜接條件的可攜證據。','run_id_evidence_lines':[],'required':False,'discovery_status':'AVAILABLE','artifact_content_status':None}],'evidence_lines':[52,53,55,57,59,61]}
p=pathlib.Path('/home/jason/quantum-hft/artifacts/handoff_setup')/rid/'handoff_discovery_supplement.json'
with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'output':str(p),'additional_copy_count':1,'sha256':d['copy_mapping'][0]['source_sha256']}))
PY
```

</details>

<details><summary>docs_development_commands.json #1 / exit 0</summary>

```bash
cat '/mnt/c/Users/jason/.codex/attachments/906fe69f-ee25-4fc9-8af5-9de6e180e02f/貼上的文字.txt'
```

</details>

<details><summary>docs_development_commands.json #2 / exit 0</summary>

```bash
ls -ld /home/jason/quantum-hft /home/jason/hft-realtime-codex/docs
```

</details>

<details><summary>docs_development_commands.json #3 / exit 0</summary>

```bash
rg --files docs artifacts/phase1_v2/20261018T210029Z artifacts/phase1_timestamp_review/20261018T212122Z | head -n 80
```

</details>

<details><summary>docs_development_commands.json #4 / exit 0</summary>

```bash
nl -ba docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md
nl -ba docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md
```

</details>

<details><summary>docs_development_commands.json #5 / exit 0</summary>

```bash
sed -n '1,230p' docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md | nl -ba
```

</details>

<details><summary>docs_development_commands.json #6 / exit 0</summary>

```bash
rg -n --glob '*.md' --glob '*.json' --glob '!command*' --glob '!root_commands*' '逐字|ACK|affinity|isolation|Paper Broker|逐檔|2026-09|2026-08|WebSocket原始|raw WebSocket' docs artifacts/phase1* artifacts/dataset_audit/phase1v2_20261018T210029Z* | head -n 100
```

</details>

<details><summary>docs_development_commands.json #7 / exit 0</summary>

```bash
rg --files -g '*.md' -g '!artifacts/build/**' -g '!artifacts/phase1_v2/**/dataset_artificial_tests/**' -g '!artifacts/test_runs/**' | head -n 100
rg -n '逐字|ACK|affinity|isolation|Paper|逐檔|WebSocket' docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md docs/DATASET_AUDIT.md docs/BUILD_BASELINE.md
```

</details>

<details><summary>docs_development_commands.json #8 / exit 0</summary>

```bash
nl -ba docs/DATASET_AUDIT.md | sed -n '35,80p'
nl -ba artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.md | head -n 100
nl -ba artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json | head -n 155
nl -ba artifacts/phase1_v2/20261018T210029Z/environment/environment.json | sed -n '95,125p'
nl -ba docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md | sed -n '315,350p'
```

</details>

<details><summary>docs_development_commands.json #9 / exit 0</summary>

```bash
python3 -B - <<'PY'
import json, os, stat
from pathlib import Path
root=Path('/home/jason/quantum-hft')
files=json.loads(r'''{"AGENTS.md":"# Quantum-HFT Research Rules\n\n## Project Separation\n\n- 這是獨立的量子計算、機器學習、策略研究、回測及模擬交易專案。\n- 不得修改、寫入、刪除、搬移或重新命名 `/home/jason/hft-realtime`。\n- 不得修改、寫入、刪除、搬移或重新命名 `/home/jason/hft-realtime-codex`。\n- 不得修改舊不完整副本 `/home/jason/hft-realtime-codex-incomplete-20261018T194544Z`。\n- HFT 市場資料全部是唯讀輸入；不得複製市場原始資料、src、results、ELF、build、壓縮檔或憑證進本專案。\n- 所有新輸出只能寫入 `/home/jason/quantum-hft`。不得建立導向 HFT results 的可寫 symlink 或 mount。\n- 本次交接只建立骨架、規格及交接驗證工具；Phase 2 尚未實作，須等待人工批准後才可開始。\n\n## Trading Safety\n\n- 不得連接真實下單 API。\n- 不得連接 Binance Testnet 下單 API。\n- 不得使用 API Key 或 Secret Key。\n- 只允許歷史研究與本機 Paper Trading；本機 Paper Trading 仍須完成前階段驗收及另獲批准，本次不執行。\n- 本次不得連接 Binance REST／WebSocket／Testnet、查文獻網站、下載或安裝套件。\n- 未經人工批准，不得更新啟用中的模擬策略。\n- Codex 不得批准自己建立的模型。\n- Testnet ACK 不等於成交；歷史回測不等於已驗證 Live Paper Broker。\n\n## Timestamp Rules\n\n- `event_time_ms` 可用於離線排序，但必須按 Session 分開。\n- `event_time_ms` 可用於未來價格標籤，但必須保存 actual horizon 和 match error。\n- 不得跨 Session、跨檔或跨失效區段建立標籤；檔名日期不能取代已稽核 event time。\n- `local_timestamp_us` 不是真正的 Local Receive Time：這是本專案的禁止使用規則。現存 producer 在 Book 更新後取時；五個歷史 CSV 的 exact producer 為 UNKNOWN，真實 receive 語義未證實，不可由欄名推定。\n- `local_timestamp_us` 不得用於網路延遲。\n- `local_timestamp_us` 不得用於 Tick-to-Trade 延遲。\n- `local_timestamp_us` 第一版不得作為模型特徵。\n- `event_time_ms` 第一版是排序、對齊與切分 metadata；不得默認將 raw epoch 當成預測特徵。\n- 大型資料缺口、尾端不足與 match error 超標時，標籤必須無效。\n- `max_match_error_ms=null`，selection_status=`TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL`。gap 閾值也待 Training profile 與 protocol 決定；不得用 Final Holdout 選值。\n- 未來 Live Recorder 必須新增真正 receive timestamp 及各處理階段 timestamp；wall clock 與 monotonic clock 的 clock source、單位、採樣位置要分開記錄。\n- 未證實跨時鐘同步與不確定度前，不得聲稱單向網路延遲。\n\n依據：[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214)、[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)、[Timestamp Review 檔內與跨檔間隔](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:139)。本次新政策不把先前提案中的 25ms 或 200ms 當成最終參數。\n\n## Research Integrity\n\n- 不得虛構模型、量子電路、回測或交易結果。\n- 不得預設量子方法優於經典方法。\n- 所有實驗記錄資料 SHA-256、程式版本、參數、環境與隨機種子；沒有 Git commit 時保存程式 SHA，缺失明列。\n- 訓練、驗證、測試必須按時間排序；不得隨機 shuffle 後切分時間序列。\n- Scaler 只能使用 Training fit。\n- 不得使用未來資訊；特徵只能依來源列當時及過去可見資料。\n- 重疊標籤跨 split 邊界時必須 purge；以實際標籤終點及 feature lookback 判斷。\n- Final Holdout 不得參與參數搜尋、模型選擇、gap／match error／交易門檻選擇。\n- 缺失資訊標記 NOT_AVAILABLE；歷史因果或來源無證據標 UNKNOWN。\n- Snapshot＋Replay 重建是待 Phase 2B 驗證的條件可行性，不能把銜接稽核 PASS 宣稱為完整 Book 已獨立驗證。\n- CPU affinity 不等於 CPU isolation。\n\n## Output Safety\n\n- 所有輸出使用唯一 run_id；不得覆寫既有 artifacts、reports 或 handoff run。\n- 已存在非空專案禁止初始化覆寫、刪除、合併或清空。\n- 每次執行記錄完整命令、stdout、stderr、exit code。\n- 長時間工作必須顯示已處理數量、總數、百分比、經過時間、ETA；無法估計 ETA 時明列 NOT_AVAILABLE。\n- 遇 hash 不一致停止，保存 FAIL 證據，禁止繼續把輸入標成可用。\n\n## Development Order\n\n1. Phase 2：資料契約、Order Book 重建、特徵與標籤。\n2. Phase 3：經典模型與統一回測。\n3. Phase 4：Quantum Kernel 與 QSVC。\n4. Phase 5：QUBO 與 QAOA。\n5. Phase 6：自動策略搜尋、重新訓練與模型退化檢查。\n6. Phase 7：本機 Live Paper Trading。\n\n不得跳過前一階段驗收。Phase 2 完成時仍不得訓練模型；本次交接完成後停止等待人工審核。\n","README.md":"# Quantum-HFT\n\n這是獨立的 Quantum-HFT 研究專案，位置為 `/home/jason/quantum-hft`。HFT C++ 來源專案位於 `/home/jason/hft-realtime-codex`；所有 HFT 輸入唯讀。這次只建立專案骨架、Phase 1 證據交接、資料契約、後續開發規格與交接驗證工具。\n\nPhase 1 v2（`20261018T210029Z`）為 PASS；Timestamp Review（`20261018T212122Z`）為 WARNING，資料決策為 PASS_WITH_RESTRICTIONS。Phase 2 可在限制條件及人工批准下開發，尚未開始。證據：[Phase 1 v2 正式報告](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:3)、[Timestamp Review 決策](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:3)。\n\n`local_timestamp_us` 不得用作網路延遲、Tick-to-Trade 或第一版模型特徵。歷史 exact producer 未證實，不能將該欄當真實 receive time。[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214)\n\n本專案尚未建立模型、進行量子實驗、執行回測或 Paper Trading；本次沒有 Testnet 或真實交易、專題網路連線或套件安裝。這些陳述只描述本專案與本次交接，不抹除來源專案歷史活動。[Recovery 歷史活動限制](/home/jason/hft-realtime-codex/docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md:315)\n\n## 證據與規格\n\n- [交接報告](/home/jason/quantum-hft/docs/PHASE1_HANDOFF_REPORT.md)\n- [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)\n- [Phase 2 計畫](/home/jason/quantum-hft/docs/PHASE2_PLAN.md)\n- [實驗計畫](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)\n- [資料來源登錄](/home/jason/quantum-hft/configs/data_sources.json)\n- [時間政策](/home/jason/quantum-hft/configs/timestamp_policy.json)\n- [交接 Manifest](/home/jason/quantum-hft/reference/hft_phase1/20261018T214147Z/HANDOFF_MANIFEST.json)\n\n市場資料只保存來源唯讀路徑，不複製 CSV、JSONL、Snapshot、src 或 results。交接證據的 CSV 統計摘要是研究報告，不是市場逐筆 CSV。Recovery 的歷史 FAIL 必須原樣保留，後續複核另列，不能回溯覆寫。\n\n## 驗證\n\n在 `/home/jason/quantum-hft` 執行下列命令。環境變數避免生成 pycache；測試人工暫存資料只能放在本專案 tests 中。\n\n```bash\nPYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_verify_handoff.py\nPYTHONDONTWRITEBYTECODE=1 python3 tools/verify_handoff.py --manifest reference/hft_phase1/20261018T214147Z/HANDOFF_MANIFEST.json\n```\n\n驗證工具不修改被檢查檔案。正常交接可以保留歷史資料 WARNING；FAIL 退出碼必須非零。實際 stdout、stderr、exit code 與結果見交接報告；README 不預填測試通過。\n\n## 後續順序\n\n1. Phase 2：唯讀 Adapter、Registry、獨立 Book 重建、特徵、標籤、時間切分、版本化資料集。\n2. Phase 3：經典模型與統一成本回測。\n3. Phase 4：Quantum Kernel 與 QSVC。\n4. Phase 5：QUBO 與 QAOA。\n5. Phase 6：自動策略搜尋、重新訓練、退化監測與人工審核。\n6. Phase 7：另經批准的本機 Live Paper Trading。\n\n目前沒有 Phase 2 Adapter、Rebuilder、Feature Builder 或 Label Builder 實作；各模組 README 只是職責和驗收規格。下一階段必須等待人工批准。\n","data_contract/HFT_INPUT_DATA_CONTRACT.md":"# HFT Input Data Contract\n\n版本：1.0（規格，尚未實作）。來源只允許 `/home/jason/hft-realtime-codex/results` 的九個已登錄輸入；本次沒有重新掃描市場資料。身份、SHA-256、size、audit status 與時間範圍必須從 [data_sources.json](/home/jason/quantum-hft/configs/data_sources.json) 及其證據取得。\n\n## 1. 已證實可用\n\n| 項目 | 已證實範圍 | 證據 |\n| --- | --- | --- |\n| CSV 欄位 | 五檔均有 local_timestamp_us、event_time_ms、update_id、best_bid、best_ask、mid_price、spread、bid_volume_5、ask_volume_5、obi_5 | [Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33) |\n| CSV 品質 | 共 269,416 列；本次引用的 v2 Audit 解析、數值、mid/spread/OBI 一致性檢查通過，五檔仍 WARNING | [v2 報告第 15–17 節](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:108) |\n| CSV event time | 五檔各自嚴格遞增，缺失／非法時間為零；可按獨立研究 Session 離線排序 | [Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67) |\n| CSV 時間間隔 | 最大檔內 event interval 為 241ms；13.327507 秒是 local 間隔，不是同等長度市場資料缺口 | [Timestamp Review 檔內與跨檔間隔](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:139) |\n| Snapshot／Replay 格式與銜接 | 兩組 Snapshot＋Replay 有效、初始銜接 PASS；Replay 1,000／50,000 事件的 gap、duplicate、backward 檢查皆為 0 | [Phase 1 v2 Snapshot／Replay 配對](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:148)；[v2 Replay 檢查](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:125) |\n\n上述是既有稽核的範圍，不等於新專案已驗證市場真實性、完整 Book 狀態或策略效益。[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63)\n\n## 2. 可由現有資料計算\n\n| 衍生項目 | 計算與依賴 | 狀態及限制 |\n| --- | --- | --- |\n| mid_price | (best_bid + best_ask) / 2 | 可重算；現有 CSV 已保存，仍需 Phase 2 adapter 驗證數值精度 |\n| spread | best_ask − best_bid | 可重算；crossed 或非法 Book 不能產生有效標籤 |\n| OBI 前五檔總量比例 | (bid_volume_5 − ask_volume_5) / (bid_volume_5 + ask_volume_5) | 分母零時依既有規則取 0，需在 feature schema 記錄規則 |\n| 未來報酬 | mid_price(t_target) / mid_price(t_source) − 1 | 待 Phase 2；100／200／500／1000ms，按 event time 配對，不得跨檔或 Session |\n| Replay Book | 合法 Snapshot 初始化後，依銜接且完整的 Replay 更新價位 | 條件可行；僅限保存 Snapshot 涵蓋且更新可知的錄製範圍，不能保證全交易所無限深度 |\n\n公式與格式來源：[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50)。Snapshot＋Replay 可以作為錄製期間 Order Book 重建的輸入，但本交接尚未重建；初始 Snapshot 範圍外未更新價位仍不可知，前五檔充足性與完整可知 Book 狀態必須由 Phase 2B 驗證。銜接 PASS 不取代重建測試或第二個獨立參考實作。[Phase 1 v2 Snapshot／Replay 配對](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:148)、[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63)\n\n## 3. 缺失或證據不足\n\n| 項目 | 狀態 | 證據邊界 |\n| --- | --- | --- |\n| CSV 每側逐檔五組價格／數量 | NOT_AVAILABLE | 十欄 schema 只有 best bid/ask 及五檔總量，不能逆推出逐檔分布；[Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33) |\n| 真實 Local Receive Time | NOT_AVAILABLE | 現存來源在 Book 更新後取時；歷史 CSV exact producer 為 UNKNOWN，不得當成 receive；[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214) |\n| 真實 collector session_id、producer binary/source identity | NOT_AVAILABLE | 檔案研究 Session 是隔離識別，不等同已知連線生命週期；[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)、[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214) |\n| 原始 WebSocket JSON 逐字紀錄 | NOT_AVAILABLE | 此九來源提供 CSV 摘要及 normalized Replay（eventTime／firstUpdateId／finalUpdateId／bids／asks）與 Snapshot，沒有建立逐字 wire payload 保存證據；不能宣稱能還原原始 WebSocket bytes。[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50) |\n| 網路、parse、queue、Book、decision 各階段延遲 | NOT_AVAILABLE | CSV 只有晚期 local 採樣與 exchange time，沒有完整同一事件階段端點；[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214) |\n| Testnet ACK 對應實際成交 | NOT_AVAILABLE | Testnet ACK 不等於成交；此九來源稽核不含成交回報／fill verification，不能拿 ACK 推論成交品質。[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63) |\n| Live Paper Broker | NOT_AVAILABLE | 現有歷史回測不等於 Live Paper Broker；本交接的稽核沒有驗證 broker 狀態機、持倉、成交、重連或風控。[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63) |\n| CPU isolation 完整驗證 | NOT_AVAILABLE | CPU affinity 不等於 CPU isolation；v2 environment 明列隔離未完整驗證。[Phase 1 v2 環境限制](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:50) |\n\n「沒有逐字保存」只限本契約九個已登錄來源的可用證據，不推論未檢視檔案一概不存在。歷史 Testnet 或交易曾否發生也不能由本次無交易倒推；Recovery 保留相關 UNVERIFIED CLAIM。[Recovery 歷史活動限制](/home/jason/hft-realtime-codex/docs/PHASE1_RECOVERY_REPORT_20261018T202030Z.md:315)\n\n## 4. 禁止使用\n\n- 不得修改 HFT 輸入或寫回 results，不得複製原始資料到 quantum-hft。\n- 不得將 `local_timestamp_us` 當成可靠 Local Receive Time，或用於網路延遲、Tick-to-Trade、第一版模型特徵；禁止將負差解讀成負網路延遲。[Timestamp Review 警告定義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:35)、[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214)\n- 不得用 CSV 捏造逐檔價量、深度斜率或 Level 1 microprice；總量不能識別各 level。\n- 不得跨檔或跨 Session 建立標籤。四個日期為 20260827 的 CSV 在 8 月，Replay eventTime 在 9 月；`obi_market_data.csv` 的 event 範圍實為 10 月，亦獨立。檔名或相同商品不構成同 Session 證據。[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)；[Replay 1000 稽核時間](/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_1000/audit_report.json:129)；[Replay 50000 稽核](/home/jason/hft-realtime-codex/artifacts/dataset_audit/phase1v2_20261018T210029Z_replay_events_50000/audit_report.json:129)\n- 跨檔 event interval 不具備檔內市場資料缺口的意義。各檔間未涵蓋期間不得插值、補造或跨越建標籤。[Timestamp Review 檔內與跨檔間隔](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:139)\n- raw epoch 不默認是模型預測變數；event time 第一版只作排序、切分與對齊 metadata。\n- 不得用 Final Holdout 決定 split、gap、match error、特徵、成本或策略參數。\n\n## 5. 尚待 Phase 2 驗證\n\n1. Adapter 唯讀開啟、拒絕寫回與路徑跳轉、SHA 不符中止；audit status WARNING 的可用範圍要保留。\n2. Snapshot 檔本身若無 event time，不得把 Replay 首時間寫成 Snapshot 原生時間；研究 pair_id 與 collector session_id 分開。\n3. Book 初始化、過期事件跳過、首有效事件銜接、quantity=0 刪除、quantity>0 覆寫、gap／重複／倒退隔離。\n4. 每步完整可知 Book 狀態與第二個獨立參考實作比較，不只驗 best bid/ask 或終態摘要；前五檔不足、crossed 或空側都要標示。\n5. 價量採可重現的精確十進位或明確 tick/lot 轉換政策，不能不加說明沿用浮點誤差。\n6. 每個 horizon 保存 requested_horizon_ms、actual_horizon_ms、target_event_time_ms、match_error_ms、valid_label、invalid_reason。\n7. 配對候選為同 Session／segment 第一個 event time >= source_time + requested_horizon；actual horizon 為兩 event time 差，match error 為 actual − requested。缺目標、跨 gap、尾端不足、非法 Book 或超標全部無效，不能填 0 假裝有效報酬。\n8. max_match_error_ms 與 gap 閾值尚未定案；只用 Training profile 及人工審核研究 protocol 選定後凍結。舊 Timestamp Review 的 25ms／200ms 僅提案，不是本契約 final 值。\n9. 時間切分、Training-only scaler、重疊標籤 purge、Final Holdout 隔離與資料集版本 manifest。\n\n以上是驗收要求，並無實作或測試結果。本次不進行 Phase 2。\n","docs/PHASE2_PLAN.md":"# Phase 2：統一 Order Book、特徵、標籤與版本化資料集\n\n狀態：SPECIFICATION_ONLY／NOT_IMPLEMENTED。這份文件只定義待批准的開發與驗收順序。本次不讀原始市場資料、不重建 Book、不產生特徵或標籤、不訓練模型、不回測、不啟動 Paper Trading。\n\n依據：Phase 1 v2 PASS 與 Timestamp Review WARNING／PASS_WITH_RESTRICTIONS。[Phase 1 v2 正式報告](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:3)；[Timestamp 決策](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:3)。資料契約是 [HFT_INPUT_DATA_CONTRACT.md](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)。\n\n## Phase 2A：Read-only Data Adapter 與 Dataset Registry\n\n工作：讀取已登錄 CSV、Snapshot、Replay JSONL，所有 HFT 輸入唯讀開啟，SHA-256／size 與登錄值完全相同才接受。每個 CSV 使用獨立 research_session_id；兩組 Snapshot／Replay 各用明示 pair_id，真實 collector session_id 不明時標 UNKNOWN。不得跨 Session，不寫回 HFT results。\n\n輸出：版本化來源登錄、schema、唯讀讀取結果及錯誤報告，只放 quantum-hft 新 run。驗收：人工小檔覆蓋缺檔、hash 錯、非法欄位、symlink/path escape、唯讀來源、非空輸出拒覆寫；真實九來源只在 Phase 2 獲批後驗證。\n\n依據：[Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33)、[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50)、[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)。\n\n## Phase 2B：Order Book Reference Rebuilder\n\n1. Snapshot 初始化已知 bid/ask 價位與 lastUpdateId。\n2. 跳過 finalUpdateId <= lastUpdateId 的過期事件並記錄；首個有效事件必須滿足 firstUpdateId <= lastUpdateId + 1 <= finalUpdateId。\n3. quantity=0 刪除價位；quantity>0 覆寫絕對數量，不是增量相加。負數、非有限、非法價格拒絕。\n4. 依 high-water ID 偵測 gap、重複與倒退。不能靜默跳過 gap 後宣稱連續重建；失效區段及重新初始化策略須明記。\n5. 輸出 Best Bid、Best Ask、前五檔價量與 Book 摘要；少於五檔、空側或 crossed book 明列無效，不補造。\n6. 小型人工事件測試覆蓋 snapshot 初始化、過期事件、跨 snapshot event、插入／覆寫／刪除、未知價位刪除、價位排序、重複／倒退／gap。\n7. 與第二個獨立參考實作逐事件比較完整可知 Book 狀態，含所有側別價位／數量／lastUpdateId；不能只比較 top-5 或共用同一 applyEvent 核心。\n8. 記錄初始 Snapshot 深度涵蓋限制；全交易所簿的未知價位不能被叫作完整重建。\n\n驗收前只稱「Snapshot＋Replay 條件可重建」。既有配對 PASS 僅證明 payload／序列銜接，未在新專案執行 Book 重建。[Phase 1 v2 Snapshot／Replay 配對](/home/jason/hft-realtime-codex/docs/PHASE1_V2_REPRODUCIBILITY_REPORT_20261018T210029Z.md:148)、[Dataset Audit 解讀限制](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:63)\n\n## Phase 2C：Feature Builder\n\n第一版保存 best_bid、best_ask、mid_price、spread、bid_volume_5、ask_volume_5、obi_5 與 event_time_ms。前七項是數值特徵候選；event_time_ms 是排序／對齊／切分 metadata，不默認將 raw epoch 輸入模型。local_timestamp_us 保留於診斷 provenance 時也不得加入特徵。\n\nReplay 重建及 Phase 2B 驗收後，才可加入 bid_price_level_1 至 5、bid_quantity_level_1 至 5、ask_price_level_1 至 5、ask_quantity_level_1 至 5、level-wise imbalance、microprice、depth slope。每項寫清公式、缺值、分母零、價位不足及來源時間；microprice 必須用實際 Level 1 數量，不以五檔總量冒充。\n\n驗收：人工已知 Book 手算對照、價差／OBI 重算一致、來源 row/event 可追溯、只用當時與過去資訊；不得為 CSV 捏造不存在的逐檔價量。[Timestamp Review 欄位表](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:33)、[Dataset Audit 格式規則](/home/jason/hft-realtime-codex/docs/DATASET_AUDIT.md:50)、[Timestamp Review 欄位語義](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:214)\n\n## Phase 2D：Label Builder\n\n候選標籤為 future_return_100ms、future_return_200ms、future_return_500ms、future_return_1000ms；每筆報酬為目標有效 mid／來源有效 mid − 1。\n\n每筆保存 requested_horizon_ms、actual_horizon_ms、target_event_time_ms、match_error_ms、valid_label、invalid_reason，另保存 source_event_time_ms、source/target row identity、research_session_id、segment_id。\n\n在同 Session 與同有效 segment 中，選第一個 event time >= source time + requested horizon；match error = actual horizon − requested horizon。禁止跨檔／Session、禁止時間插值與未來回填。找不到未來價格、資料缺口、超過 match error、Session 尾端不足、crossed 或 invalid book 均排除並保留明確原因。\n\nmax_match_error_ms=null，selection_status=TO_BE_DETERMINED_FROM_TRAINING_DATA_PROFILE_AND_RESEARCH_PROTOCOL；gap 閾值同樣未定案。不得把舊提案 25ms 或 200ms 當成 final 值。Training profile、候選政策與保留率分析完成並審核後凍結，再套 Validation／Test／Final Holdout。\n\n驗收：人工不規則 event time、精確匹配、超標、gap、跨 Session、尾端、非法 Book；核算 actual horizon 與 match error；驗證每一無效原因有測試。實際有效標籤數目前 NOT_AVAILABLE。[Timestamp Review 檔內與跨檔間隔](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:139)、[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)\n\n## Phase 2E：Time Split 與 Leakage Protection\n\n按 event time 建立 Train、Validation、Test，另封存 Final Holdout；不隨機 shuffle。來源檔隔離不等於已經有正確時間切分，必須檢查跨資料來源日期與來源重疊。\n\nScaler 僅 Training fit；選參只用 Training 及事先宣告的 Validation。對 label 的實際 future endpoint 觸及後一 split 者 purge；feature lookback 若跨邊界也須遵循明確歷史可用規則。Final Holdout 不參與特徵、gap、match error、模型、成本或交易門檻搜尋。\n\n保存每個 split 的起訖時間、row identity、來源 SHA-256、資料 SHA-256、purge 數量與原因；禁止依測試結果重選日期。驗收包含故意跨邊界重疊標籤、scaler 洩漏偵測與 holdout 使用審計。依據：[Timestamp Review Session 範圍](/home/jason/hft-realtime-codex/docs/PHASE1_V2_TIMESTAMP_REVIEW_20261018T212122Z.md:67)、[Timestamp Review 使用規則](/home/jason/hft-realtime-codex/artifacts/phase1_timestamp_review/20261018T212122Z/phase2_time_rules.json)。\n\n## Phase 2F：版本化資料集\n\n只有 Phase 2A–2E 驗收後建立唯一 `/home/jason/quantum-hft/artifacts/datasets/<dataset_run_id>/`。必須拒絕覆寫既有 run；HFT inputs 仍只記唯讀路徑與 hash。\n\n至少包含 dataset_manifest.json、source_files.json、feature_schema.json、label_schema.json、quality_report.json、train/、validation/、test/。Final Holdout 的封存位置、hash、存取紀錄另在 manifest 明記；不允許作日常調參輸入。\n\nmanifest 記錄程式版本／SHA、環境、參數、原始資料 SHA、schema、timestamp policy、split、invalid／purged 數量及執行命令。未實際產出的指標標 NOT_AVAILABLE，不預填 PASS。\n\n## 完成驗收與停止點\n\n完成需有唯讀與隔離證據、兩個獨立 Book 實作逐事件一致、人工及實際資料品質報告、特徵／標籤 lineage、時間切分無洩漏、版本資料集完整性與人工審核。任何一項未通過保留 FAIL／NOT_AVAILABLE，不推進下階段。\n\nPhase 2 完成時仍不得訓練模型。後續 Phase 3 需另獲批准；本次骨架交接完成即停止。\n","docs/LITERATURE_REVIEW.md":"# Literature Review\n\n狀態：NOT_AVAILABLE／待人工批准後查證。本次沒有查詢外部文獻網站、下載文獻或新增 DOI。下表只是待填矩陣；不是已找到或讀過的研究。\n\n| Citation | Research question | Dataset | Features | Classical baseline | Quantum method | Optimization method | Transaction costs | Validation design | Metrics | Main result | Limitation | Relevance to this project |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| NOT_AVAILABLE | 待查證 | 待查證 | 待查證 | 待查證 | 待查證 | 待查證 | 待查證 | 待查證 | 待查證 | NOT_AVAILABLE | 待查證 | 待查證 |\n\n後續每筆須核對原始文獻、作者／年份、可驗證來源、DOI（若有）、資料時間範圍、費用與滑價、時間驗證設計、經典比較預算、量子資源及限制。文獻主張、作者結果與本專案實驗結果必須分開；缺資料明列 NOT_AVAILABLE。\n\n候選檢索議題僅為研究規劃：Order Book imbalance 與短期價格預測、時間序列資料洩漏、Quantum Kernel／QSVC 的公平比較、QUBO 交易決策及 exact solver／QAOA 最佳化比較。這些議題名稱不構成文獻或新穎性證據。\n","docs/RESEARCH_GAP.md":"# Research Gap\n\n**PROVISIONAL RESEARCH GAP — REQUIRES LITERATURE VERIFICATION**\n\n本文件只列待文獻核對的研究問題，不聲稱尚無任何既有研究，不宣稱量子優勢。\n\n| 暫定研究問題 | 所需驗證 | 目前狀態 |\n| --- | --- | --- |\n| 具 Session、gap、match error 與時間洩漏保護的短 horizon 資料，是否改變經典與量子 kernel 的比較？ | 文獻是否已處理；相同資料、split、特徵及搜尋預算下的對照 | PROVISIONAL；實驗 NOT_AVAILABLE |\n| 成本後績效與分類指標是否一致？ | 文獻成本模型；固定費用／滑價／執行時點規格與敏感度 | PROVISIONAL；實驗 NOT_AVAILABLE |\n| 小型 QUBO 中 QAOA 與經典 exact solver 的可行率、目標值差距與計算成本如何？ | 相同 objective、constraints、instances 與預算；小型 exact reference | PROVISIONAL；實驗 NOT_AVAILABLE |\n| 自動重新訓練的退化偵測與人工批准是否能提高可重現性？ | 先驗 protocol、固定 holdout、模型版本與審核紀錄 | PROVISIONAL；實驗 NOT_AVAILABLE |\n\n資料已知限制是本專案的工程條件，不能直接稱為學術研究缺口。參見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)；目前文獻驗證未執行，參見 [文獻矩陣](/home/jason/quantum-hft/docs/LITERATURE_REVIEW.md)。\n","docs/EXPERIMENT_PROTOCOL.md":"# Experiment Protocol\n\n狀態：PROPOSAL_ONLY／NOT_EXECUTED。本次只鎖定候選比較架構與最低紀錄要求。尚未建立模型、量子電路、kernel matrix、QUBO、QAOA、回測或 Paper Trading；所有實驗結果 NOT_AVAILABLE。任何實驗要在前階段驗收與人工批准後執行。\n\n## 比較架構\n\n| 階段 | 候選方法 | 公平比較要求 |\n| --- | --- | --- |\n| Phase 3 | 固定 OBI ±0.6 規則 | 正側／負側／中立區規則預先固定；建倉、平倉、持有、成本另明定，不把閾值直接當成完整交易策略 |\n| Phase 3 | Logistic Regression | 同資料、特徵、label、時間 splits、scaler 與搜尋預算 |\n| Phase 3 | Linear SVM | 同上；搜尋空間與選擇依據事前記錄 |\n| Phase 3 | RBF-SVM | 同上；與 kernel 方法比較時記錄 pairwise 計算及記憶體成本 |\n| Phase 4 | Fixed Fidelity Quantum Kernel | feature encoding、qubits、depth、shots、seed、backend 與測量政策待明確批准；不得預設優勢 |\n| Phase 4 | Trainable Quantum Kernel | 參數訓練只用 Training；kernel learning／搜尋成本完整計入 |\n| Phase 4 | QSVC | 明確指定搭配哪種 kernel；不將 QSVC 與其 kernel 視作獨立不相干證據 |\n| Phase 5 | Classical exact QUBO solver | 小型相同 QUBO instance 的精確目標值與可行性參考；規模限制明列 |\n| Phase 5 | QAOA | 與 exact solver 同 objective／constraints／instances；記錄 shots、depth、seed、iteration、總成本 |\n\n以上是候選清單，沒有套件、程式或結果。分類預測與決策最佳化分開驗收；QAOA 不直接與分類器以同一分類分數排名。\n\n## 資料、標籤與切分\n\n遵守 [Phase 2 計畫](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)。100／200／500／1000ms 標籤保存 actual horizon、match error 與有效性。不同 horizon 的有效樣本集合不同時，主比較使用同一明確交集，另報 coverage，不能靠排除困難樣本美化結果。\n\nmax_match_error_ms=null；gap 閾值、return classification 門檻及訓練區間只在 Training profile 與研究 protocol 中決定並經人工審核後凍結。原始 epoch 為 metadata；local_timestamp_us 不作模型特徵或延遲。Validation 用於事先定義的模型選擇，Final Holdout 全程封存直到唯一最終評估。\n\nTrain／Validation／Test 按時間排序，不 shuffle；Scaler 僅 Training fit。以實際 label future endpoint purge split 重疊，記錄 feature lookback。時間相關樣本的統計推論方法另預註冊，不能將逐筆資料當獨立觀測而不說明。\n\n## 指標與計量邊界\n\n| 指標 | 定義／必要紀錄 |\n| --- | --- |\n| Balanced Accuracy | 各類 recall 平均；類別定義、樣本數、缺類情況明列 |\n| Macro-F1 | 各類 F1 平均；零分母政策與 support 明列 |\n| Precision／Recall | 逐類報告並附混淆矩陣；不能只報單一平均掩蓋少數類 |\n| 成本後報酬 | 明定 fee、spread、slippage、交易時點、持倉與資本尺度；不得假設無限可成交 |\n| 最大回撤 | 依成本後 equity curve；取樣時間與定義固定 |\n| 交易次數 | 定義 order、fill、round trip 或持倉變化；不能混用 |\n| 推論時間 | 實測本機 pipeline／model 邊界，warmup、batch、hardware、分位數；不能由舊 CSV local−event 推得 |\n| 訓練時間 | 含 scaler、特徵選擇、kernel 計算與調參者需清楚拆分及總計 |\n| Qubit 數 | 邏輯 qubits、實際 backend 規模與 ancillary 分開 |\n| 電路深度 | 編譯前後、gate set、connectivity 及 transpilation 設定 |\n| QAOA 可行率 | 所有測得候選中符合原始 constraints 的比例；constraint／penalty 固定 |\n| QAOA 目標值差距 | 與同 instance exact optimum 比較 absolute gap；相對 gap 分母為零時明列不適用 |\n\n費用、滑價、延遲與 fill 假設不能由現有來源憑空推定。Phase 3 統一回測須先定義再使用；Testnet ACK 不等於 fill，CSV local 時間不是網路延遲證據。當階段不適用指標標 NOT_APPLICABLE；未量測標 NOT_AVAILABLE，均不可填 0。\n\n## 可重現性、資源及報告\n\n每次保存唯一 run_id、原始資料與資料集 SHA-256、程式版本／SHA、環境、所有參數、random seeds、split 時間及 hash、訓練／驗證／測試樣本數、invalid/purge 數量、完整命令／stdout／stderr／exit code、搜尋空間及總試驗數。\n\n量子方法另保存 encoding、kernel PSD／數值處理規則、shots、noise/backend、qubits、depth、最佳化預算；小型 pilot 的樣本及 kernel matrix 大小須先核准，避免無上限 O(n²) 記憶體。CPU affinity 不等於 isolation，模擬器時間不等於量子硬體時間。不得只挑最好的 seed 報告。\n\nPhase 6 自動搜尋及重新訓練須保留 champion/challenger、退化判準、模型版本與人工批准紀錄。Codex 不得批准自己的模型，不可自動更新啟用中的模擬策略。\n\n## 驗收與停止\n\nPhase 2 只驗收資料與 lineage；Phase 3 再建立經典基線與成本回測；Phase 4、5 才研究量子方法；Phase 6、7 各有獨立人工 gate。本次不得執行任何上述實驗，完成交接後停止。\n","data_pipeline/README.md":"# Data Pipeline\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 2。\n\n職責：唯讀 Adapter、Dataset Registry、兩套獨立 Book 重建參考、Feature Builder、Label Builder、時間切分及版本化資料集。\n\n限制：不得寫回 HFT；禁止跨檔／Session labels、local timestamp 特徵與未經核准 gap／match error 門檻。\n\n未來驗收：人工事件逐步完整 Book 對照、來源 SHA、標籤有效性、purge 與 feature lineage。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","models/classical/README.md":"# Classical Models\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 3。\n\n職責：候選 Logistic Regression、Linear SVM、RBF-SVM，及固定 OBI ±0.6 規則比較。\n\n限制：先完成 Phase 2；相同資料、splits、特徵與成本 protocol；Scaler 僅 Training fit，Final Holdout 不調參。\n\n未來驗收：事前固定搜尋預算、多 seed 紀錄、分類及成本後績效、推論與訓練時間。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","models/quantum/README.md":"# Quantum Models\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 4。\n\n職責：候選 Fixed Fidelity Quantum Kernel、Trainable Quantum Kernel 與 QSVC。\n\n限制：先驗收經典基線；本次不得建立電路、kernel matrix、模型或安裝 Qiskit；不得預設量子優勢。\n\n未來驗收：同一輸入與預算公平比較，保存 qubits、depth、shots、backend、seed、成本與資源限制。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","optimization/classical/README.md":"# Classical Optimization\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 5。\n\n職責：為相同小型 QUBO instance 提供 Classical exact solver 參考。\n\n限制：本次不建立 QUBO 或 solver；必須先固定 objective、constraints、cost 及規模上限。\n\n未來驗收：可行性、精確最優值、時間、記憶體與規模限制；作 QAOA 同題比較參考。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","optimization/qubo/README.md":"# QUBO Specification\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 5。\n\n職責：未來將已明確定義的交易決策、成本與風險限制轉成可驗證小型 QUBO。\n\n限制：本次不建 QUBO；penalty 不能以 Final Holdout 搜尋，不得把分類機率直接當已驗證交易價值。\n\n未來驗收：人工枚舉真值表對照原始 objective／constraints、可行解與 penalty 行為。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","optimization/qaoa/README.md":"# QAOA Research\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 5。\n\n職責：待批准後與 Classical exact solver 比較同一 QUBO 的可行率及目標值差距。\n\n限制：本次不得建立 QAOA、量子電路或訓練；不使用帳戶／憑證或外部 backend。\n\n未來驗收：相同 instances、預算、shots、depth、seeds、採樣及端到端成本；結果須與 exact optimum 對照。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","backtesting/README.md":"# Backtesting\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 3。\n\n職責：未來統一事件順序、策略輸出、持倉、費用、滑價及成交假設的歷史回測。\n\n限制：本次未回測；歷史回測不等同 Live Paper Broker；不得跨 Session 搬移持倉而無明確政策。\n\n未來驗收：人工交易序列可手算的持倉／現金／費用／equity、成本後報酬、最大回撤與交易次數。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","paper_trading/README.md":"# Local Paper Trading\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 7。\n\n職責：另獲批准後的本機模擬 Broker、持倉、現金、風控及策略生命週期。\n\n限制：目前沒有 Paper Trading 實作或執行；不得連真實／Testnet 下單 API、不得使用 API／Secret Key。未經人工批准不得更新啟用中的模擬策略。\n\n未來驗收：人工狀態機、重連／重複事件、風控與成交假設；任何未來行情連線須另經批准；真實 receive timestamp 與階段採樣先驗收。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","automation/README.md":"# Research Automation\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：Phase 6。\n\n職責：未來策略搜尋、重新訓練、退化檢查與 champion／challenger 版本紀錄。\n\n限制：本次未啟動排程、訓練或模型更新。Final Holdout 不搜尋；Codex 不得批准自己建立的模型。\n\n未來驗收：搜尋預算、時間切分、模型版本、退化判準、失敗回復方案及人工 gate；保留所有試驗。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","artifacts/README.md":"# Artifacts\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：交接與後續獲批階段。\n\n職責：保存唯一 run_id 的交接驗證證據、人工測試紀錄與未來獲批的研究輸出。\n\n限制：禁止覆寫既有 run；不得複製 HFT 原始市場 CSV／JSONL／Snapshot、ELF 或模型進交接。人工測試 fixture 只在 tests 下。\n\n未來驗收：每輪保存 manifest、SHA、參數、環境、完整命令／stdout／stderr／exit code；失敗證據保留。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","reports/README.md":"# Reports\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：交接與後續獲批階段。\n\n職責：保存唯一 run_id 對應的研究報告；目前正式交接報告位於 docs/PHASE1_HANDOFF_REPORT.md。\n\n限制：不能把規格寫成實作、候選寫成結果、WARNING 或 NOT_AVAILABLE 寫成 PASS；不得覆寫歷史 FAIL。\n\n未來驗收：所有結論附實際證據、資料版本與限制；報告與機器可讀輸出一致。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n","references/README.md":"# References\n\n狀態：骨架／SPECIFICATION_ONLY，尚未實作。預定階段：文獻驗證待批准。\n\n職責：未來保存可核查的文獻索引與引用 metadata；文獻矩陣先放 docs/LITERATURE_REVIEW.md。\n\n限制：本次未查詢網站或下載論文；不得虛構 Citation、作者、DOI 或研究缺口。HFT 交接證據在單數 reference/hft_phase1/，不要混淆。\n\n未來驗收：逐篇原始來源核對、研究問題／資料／成本／驗證設計／限制；沒有證據寫 NOT_AVAILABLE。\n\n共同規則見 [AGENTS.md](/home/jason/quantum-hft/AGENTS.md)，資料限制見 [資料契約](/home/jason/quantum-hft/data_contract/HFT_INPUT_DATA_CONTRACT.md)，後續計畫見 [Phase 2](/home/jason/quantum-hft/docs/PHASE2_PLAN.md) 與 [實驗 Protocol](/home/jason/quantum-hft/docs/EXPERIMENT_PROTOCOL.md)。本次沒有執行本模組的研究流程。\n"}''')
assert root.is_dir() and not root.is_symlink()
for rel in files:
 p=root/rel
 if p.exists() or p.is_symlink(): raise SystemExit('REFUSE_EXISTING '+str(p))
 for parent in p.parents:
  if parent==root.parent: break
  if parent.is_symlink(): raise SystemExit('REFUSE_SYMLINK '+str(parent))
for rel,content in files.items():
 p=root/rel
 p.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
 with os.fdopen(fd,'w',encoding='utf-8') as stream: stream.write(content)
print(json.dumps({'status':'CREATED','count':len(files),'paths':list(files)},ensure_ascii=False))
PY
```

</details>

<details><summary>docs_development_commands.json #10 / exit 0</summary>

```bash
python3 -B - <<'PY'
from pathlib import Path
import json
root=Path('/home/jason/quantum-hft')
paths=['AGENTS.md','README.md','data_contract/HFT_INPUT_DATA_CONTRACT.md','docs/PHASE2_PLAN.md','docs/LITERATURE_REVIEW.md','docs/RESEARCH_GAP.md','docs/EXPERIMENT_PROTOCOL.md','data_pipeline/README.md','models/classical/README.md','models/quantum/README.md','optimization/classical/README.md','optimization/qubo/README.md','optimization/qaoa/README.md','backtesting/README.md','paper_trading/README.md','automation/README.md','artifacts/README.md','reports/README.md','references/README.md']
for rel in paths:
 p=root/rel
 assert p.is_file() and not p.is_symlink()
 content=p.read_text(encoding='utf-8')
 assert content.endswith('\n') and len(content)>100
print(json.dumps({'status':'PASS','documents_checked':len(paths),'market_input_read':False,'hft_written':False},ensure_ascii=False))
PY
```

</details>

<details><summary>正式驗證命令 / exit 0</summary>

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_verify_handoff.py
```

</details>

<details><summary>正式驗證命令 / exit 0</summary>

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/verify_handoff.py --manifest reference/hft_phase1/20261018T214147Z/HANDOFF_MANIFEST.json
```

</details>

目前report整合命令全文在root_commands.json.final_report_command；最終verify及末次metadata命令全文與結果在verification_closeout.json，不預填未執行結果。

## 24. 研究誠信與停止

所有PASS來自此次真實檔案hash、schema/安全檢查與人工單元測試；歷史WARNING/FAIL與UNKNOWN未改寫。規格不是完成實驗，沒有虛構模型、電路、回測、成交或延遲。

全部完成後停止等待人工審核；不進Phase2、不訓練、不回測、不開始Paper Trading。
