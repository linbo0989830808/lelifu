# reminder-system

提醒功能概覽

- 使用 dateparser 解析中文自然語言時間
- 指令格式範例："提醒我 1 分鐘後 喝水"、"提醒我 明天上午9點 開會"
- 儲存位置：memory/reminders.json
- 守護程式：scripts/reminder_daemon.py（每 30s 檢查並發通知）

注意：若時區或解析失敗，會詢問使用者重述時間
