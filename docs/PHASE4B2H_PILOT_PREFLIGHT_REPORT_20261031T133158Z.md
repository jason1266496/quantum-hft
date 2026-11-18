# Phase 4B-2H Pilot Preflight

狀態：**BLOCKED — TCP_TEST_BLOCKED**。run_id：20261031T133158Z。

開發環境預檢在socket.socket(AF_INET, SOCK_STREAM)就被sandbox以PermissionError/EPERM拒絕；未進入bind、DNS、connect或TLS。依使用者明示「若sandbox不允許loopback TCP，不得繞過限制，記錄TCP_TEST_BLOCKED」停止該驗收鏈。未要求解除sandbox、未改用其他程序或主機繞過。

本目錄是開發前置阻擋證據封存，**不是已通過開發預檢後的正式工程Gate**。正式Supervisor/build/Regression/CTest/E2E/Determinism均NOT_RUN。沒有新C++ Transport或runtime Budget/Deadline實作，不把候選JSON當作已生效控制器，也不重建既有Runner/Writer/Reference。149/149僅引用G歷史證據，本輪測試0項。

已交付待審草案：network_policy.json、pilot_candidate_config.json、global_budget_controller.json（NOT_IMPLEMENTED）、timestamp_identity_schema.json、f03_decision_matrix.json及pilot_approval_sheet.md。所有600秒/3Snapshot/2WS/1恢復/30秒/256MiB等為PROPOSED_NOT_APPROVED。分離deadline僅候選設定，尚無實際執行驗證。REST固定官方版本/weight未補足；沒有網路查證，不能標記完成。

F03保留U<=L<u，A/B/C由人工決定；F43所有具名人員、儲存、保留、時窗及事故安排仍APPROVAL_REQUIRED。Pilot不得追認Confirmation，LIVE_CAPTURE_AUTHORIZED=false。最新Astra審核來源為本對話上一則回覆，未找到對應獨立檔案，未假造其文件SHA。

完整性只對integrity_report明列26個非市場程式/規格/報告檔作前後SHA且一致。Dataset/Frozen/兩venv未修改、未重新內容hash或全樹驗證，不宣稱新完整性PASS。真Test/Final Holdout內容open0，歷史60次opaque-hash open與F39 FAIL保留；新No-Open runtime Gate未執行。原時間戳與identity限制仍見G封存說明。

實際socket操作沒有建立成功，無DNS或外部連線；沒有真行情、模型fit/predict、正式Kernel、QPU、QAOA、交易、回測或套件安裝。私有開發tmp為0700，但child TMPDIR傳遞與UNIT_WRITE_SCOPE新Gate為NOT_RUN；沒有新增OS帳戶、quota、CA或防火牆設定。

下一步：由使用者安排符合原授權、允許隔離loopback TCP的執行環境，再另行恢復原2H工程；不得把本次BLOCKED當成可提交最終Pilot執行批准的就緒證明。已可審閱候選表，但不能執行Pilot。所有未完成項完整列在implementation_status/regression/E2E/fault/determinism/storage JSON中。
