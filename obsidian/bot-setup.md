# bot-setup

內容摘要：如何建立本地 agent 與 Telegram bot

檔案與腳本

- scripts/agent_qwen.sh — local CLI wrapper to call ollama qwen2.5:7b
- scripts/telegram_agent.py — Telegram long-polling bot (main service)
- .venv — Python virtualenv for any required packages

主要步驟

1. (已完成) 建立 agent wrapper 並測試基本 prompt 回應。
2. (已完成) 在 Telegram 上建立 bot（t.me/Qman01_bot），並把 token 設為環境變數 TELEGRAM_BOT_TOKEN。
3. (已完成) 啟動 telegram_agent.py 及 reminder_daemon.py，背景運行。

注意事項

- Bot token 非常敏感，切勿把 token 存入 repo。若疑似洩露，請立即在 BotFather 重新生成。
