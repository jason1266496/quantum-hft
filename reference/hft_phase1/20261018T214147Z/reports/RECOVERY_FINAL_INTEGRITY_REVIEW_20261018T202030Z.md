# 最終完整性檢查覆核

首次 final_integrity_check.json 保持原狀，其 FAIL 沒有被覆寫。

首次檢查的內容結果為968/968 SHA-256相同、缺少0、內容差異0。路徑掃描使用 is_file() OR is_symlink()，比開始前及使用者968檔清單的檔案範圍多納入directory symlink，因而將10個測試用既有符號連結列為unexpected_added_files。

本覆核逐一用lstat、readlink與GNU stat查驗工作副本、原保留資料夾及舊不完整副本。是否證實前存，以final_integrity_review.json中每一列的preexisting_proven與原生birth/ctime為準；沒有將這些連結加入或重建任何Phase1基線。

10/10連結均已證實早於本次鑑識前存在，且原保留副本有相同連結目標；全部是指向目錄的符號連結，不是本次新增的檔案。首次路徑FAIL為掃描範圍不一致的誤判。

寫入本覆核說明後，再以使用者原有968檔基線計算所有hash，並檢查額外一般檔案及符號連結是否只有核准輸出或已證實前存的10項。實際完成結果見同目錄final_integrity_review.json。覆核與首次FAIL皆保留，沒有修改主Recovery Report或任何既有檔案。

本次原有968檔的鑑識完整性結果，不代表歷史Phase1已通過；原Phase1 FAIL與方案B僅供人工審核的狀態保持不變。沒有執行修復。
