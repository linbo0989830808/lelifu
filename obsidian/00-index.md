# Qman (Telegram bot) — 更新紀錄總覽

以下為從開始到最新的更新紀錄（按時間順序），點擊連結閱讀細節：

- 2026-03-17 — 初始架構與部署
  - [[bot-setup]]：建立 agent wrapper、Telegram bot、啟動服務。 
  - [[site-deploy]]：個人網站建立與 GH Pages 部署（含自動化 workflow）。
- 2026-03-17 — 記憶與檢索
  - [[memory-arch]]：聊天記憶存放規則與檔案路徑（memory/telegram_history）。
  - [[retriever-tfidf-proto]]：TF-IDF 原型檢索（快速上線）。
  - [[faiss-embedding]]：升級到向量索引（.venv、sentence-transformers、faiss）。
- 2026-03-17 — 安全與維運
  - [[git-scrub]]：從 Git 歷史刪除洩露憑證、建立備份分支。 
  - [[timeouts-and-logs]]：模型超時處理、錯誤日誌與隱私保護。 
- 2026-03-17 — 互動與 UX 改善
  - [[thinking-ux]]：typing 與 placeholder（思考中顯示）功能。
  - [[reminder-system]]：自然語言提醒解析與提醒守護程式。

---

更新說明：各頁面含操作指令、重要檔案路徑與未來升級建議。需要我把這些筆記也同步到 Obsidian vault 或以 Markdown 打包給你嗎？
