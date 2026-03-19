#!/usr/bin/env python3
# Simple reminder checker: looks at memory/reminders.json and fires reminders
import time, json
from pathlib import Path
import urllib.request, urllib.parse, os
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
API = f'https://api.telegram.org/bot{TOKEN}'

rfile = Path('memory/reminders.json')

while True:
    try:
        if rfile.exists():
            rems = json.loads(rfile.read_text(encoding='utf-8'))
            now = __import__('datetime').datetime.now(__import__('pytz').timezone('Asia/Taipei'))
            remaining = []
            for r in rems:
                t = __import__('dateutil.parser').isoparse(r['time'])
                if t <= now:
                    # send reminder
                    try:
                        data = urllib.parse.urlencode({'chat_id': r['chat_id'], 'text': f"提醒：{r['text']}"}).encode()
                        urllib.request.urlopen(API + '/sendMessage', data=data, timeout=10)
                    except Exception:
                        pass
                else:
                    remaining.append(r)
            rfile.write_text(json.dumps(remaining, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass
    time.sleep(30)
