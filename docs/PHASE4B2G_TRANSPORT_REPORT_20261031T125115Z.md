# Phase 4B-2G C++ Transport Offline Integration
狀態：**PASS_WITH_RESTRICTIONS**；run_id：20261031T125115Z。僅離線/隔離人工服務，NETWORK_ENABLED=OFF，LIVE_CAPTURE_AUTHORIZED=false。

## 實作與建置
新增src/live_transport.hpp，既有Adapter/Writer/OrderBook/Labels/Runner/Reference沿用；只改phase binding、介面選擇、receive clock/connection provenance與必要環境設定。WebSocketClient與REST exchange使用Boost.Beast/Asio SSL/OpenSSL，AF_UNIX及TCP TLS模板實際編譯；隔離fixture工廠提供已連接Unix socketpair，進行真正TLS握手、WS upgrade/frame/Ping-Pong與HTTP GET/response。不是將JSON假扮成已收到的HTTP。依賴均現存，沒有安裝；pkg-config缺失不影響CMake。
實際遠端TCP dial工廠、DNS/TCP環境、正式系統CA及端點白名單未接入/未授權；本輪不宣稱已可連Binance。完整操作見README.md。

## 正式Gate
Regression 149項；failures=0、errors=0、skips=0；CTest見logs/2.stdout。全程真正Supervisor→Child→人工TLS WS/HTTP→Capture→Raw→Replay→Python A/B→Oracle，正常/gap新段冷啟動Replay相同。所有命令/stdout/stderr/exit保存。
測試包含trusted/untrusted/wrong-host雙客戶端、真正masked Pong wire echo、abrupt drop與有界重連、file rotation不換物理connection、Snapshot等待buffer、overflow、429/5xx/weight/Retry-After數字及HTTP-date、HTTP framing/JSON錯誤、取消/timeout、Writer/磁碟故障。Raw Snapshot直接hash真正收到的HTTP entity body，保存safe headers、request/HTTP connection identity、CLOCK_REALTIME/MONOTONIC、解析狀態；raw字串空白排序保真。無效framing只保留失敗trace，不能聲稱取得完整Snapshot。
Seal與同步/qualification分離；SEALED_SYNC_CANDIDATE尚須非空Replay+A/B一致，失效段不跨Label。人工結果只證明已測範圍，沒有真實市場效能/來源完整性證明。

## 網路禁止與安全
Native capture在threads前安裝Linux x86_64 seccomp，拒絕Internet/其他domain sockets及connect；getaddrinfo link wrapper禁止DNS。負測實際證明AF_INET/IPv6創建EPERM、resolver只進wrapper而無查詢，remote_endpoint在DNS/dial前拒絕。AF_UNIX socketpair為已批准隔離fixture I/O。這是該child的網路syscall限制，不是整台主機或檔案系統OS隔離。
本輪真實Test open=0、Final Holdout未開/LOCKED；沒有市場連線/行情下載、模型/市場Kernel、QPU/QAOA、交易/Testnet/Paper/回測或套件安裝。歷史60次Test opaque open及F39 FAIL保留。

## 完整性與限制
核對27519筆受保護metadata、差異0；Dataset/Frozen/venv沒有fresh內容SHA。Core/Decimal/Python references/schema與Phase4B2F fresh SHA相同：True。新code/config SHA在正式前鎖定並正式後重驗，不覆寫歷史。
MALLOC_ARENA_MAX=2且RLIMIT_AS仍256MiB。HTTP body1MiB/header16KiB、WS64KiB與有界queue；fixture總連線deadline預設2s硬cap5s。Retry-After超過人工5s等待cap停止，不能提早重試。正式REST版本/weight、長時間idle/ping/lifetime/deadline與服務區域、OS帳戶/儲存/撤權、硬體故障仍須批准及實環境驗證；不以離線PASS代替。

## 開發證據與待批准
123450Z保留新增TLS thread資源失敗；123933Z保留Pong server callback證據不足；124129Z保留overflow被錯關另一fd掩蓋的失敗；124345Z通過146項，124651Z最終人工預檢。以MALLOC_ARENA_MAX=2保留記憶體cap；Pong改獨立wire驗證；取消改持有dup handle避免fd重用；未刪assertions或改寫歷史狀態。
F03沿用保守U<=L<u，U=L+1仍拒絕，APPROVAL_REQUIRED。F43角色/帳戶/窗口/端點/容量/停止/事故仍APPROVAL_REQUIRED。可以提交本實作與Pilot checklist供人工審核；仍需正式網路能力/CA/端點/政策/保管批准，不能直接啟動Pilot。完成後停止。
