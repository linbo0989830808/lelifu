#!/usr/bin/env python3
# Telegram bot with simple per-chat memory (last N messages)
import os, sys, time, json, subprocess, urllib.request, urllib.parse
from pathlib import Path

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print('TELEGRAM_BOT_TOKEN not set')
    sys.exit(1)
API = f'https://api.telegram.org/bot{TOKEN}'
MEM_DIR = Path('memory/telegram_history')
MEM_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_LEN = 6

def get_updates(offset=None, timeout=30):
    url = API + '/getUpdates?timeout=%d' % timeout
    if offset:
        url += '&offset=%d' % offset
    with urllib.request.urlopen(url, timeout=timeout+10) as r:
        return json.load(r)

def send_message(chat_id, text):
    data = urllib.parse.urlencode({'chat_id': chat_id, 'text': text}).encode()
    req = urllib.request.Request(API + '/sendMessage', data=data)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)

def load_history(chat_id):
    p = MEM_DIR / f'{chat_id}.json'
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            return []
    return []

def save_history(chat_id, hist):
    p = MEM_DIR / f'{chat_id}.json'
    p.write_text(json.dumps(hist, ensure_ascii=False), encoding='utf-8')

print('telegram_agent (with memory): starting')
offset = None
while True:
    try:
        res = get_updates(offset)
        if not res.get('ok'):
            time.sleep(1)
            continue
        for u in res.get('result', []):
            offset = u['update_id'] + 1
            if 'message' not in u: continue
            m = u['message']
            chat_id = m['chat']['id']
            text = m.get('text','')
            if not text: continue

            # load history and append user message
            hist = load_history(chat_id)
            hist.append({'role':'user','text':text,'ts':int(time.time())})
            # keep last N entries
            hist = hist[-HISTORY_LEN:]
            save_history(chat_id, hist)

            # build system + history prompt
            import dateparser, datetime, pytz
            tz = pytz.timezone('Asia/Taipei')
            now = datetime.datetime.now(tz)
            now_str = now.strftime('%Y-%m-%d %H:%M (%Z)')
            system_prompt = f'你是 Lelifu 的本地代理，回覆要簡短、中文、口語化。現在時間：{now_str}。'
            # allow quick scheduling: if user says 提醒我..., parse time and schedule
            if text.startswith('提醒我') or text.startswith('提醒 我'):
                # parse phrase like "提醒我 明天上午9點 去跑步"
                rest = text.replace('提醒我','').strip()
                # try parsing a datetime from the rest
                # try to find a date/time substring in the text (handles phrases like '1分鐘後', '今天19:33')
                from dateparser.search import search_dates
                found = None
                try:
                    found = search_dates(rest, languages=['zh'], settings={'TIMEZONE':'Asia/Taipei','RETURN_AS_TIMEZONE_AWARE':True,'PREFER_DATES_FROM':'future','RELATIVE_BASE': datetime.datetime.now(tz)})
                except Exception:
                    found = None
                dt = None
                if found:
                    # search_dates returns list of (matched_text, datetime)
                    dt = found[0][1]
                # fallback to single parse
                if dt is None:
                    dt = dateparser.parse(rest, languages=['zh'], settings={'TIMEZONE':'Asia/Taipei','RETURN_AS_TIMEZONE_AWARE':True,'PREFER_DATES_FROM':'future','RELATIVE_BASE': datetime.datetime.now(tz)})
                if dt:
                    # ensure timezone-aware and in Asia/Taipei
                    if dt.tzinfo is None:
                        dt = tz.localize(dt)
                    else:
                        dt = dt.astimezone(tz)
                    # store reminder
                    reminders = []
                    rfile = Path('memory/reminders.json')
                    if rfile.exists():
                        try:
                            reminders = json.loads(rfile.read_text(encoding='utf-8'))
                        except Exception:
                            reminders = []
                    reminders.append({'chat_id':chat_id,'text':rest,'time':dt.isoformat()})
                    rfile.write_text(json.dumps(reminders, ensure_ascii=False), encoding='utf-8')
                    send_message(chat_id, f'已幫你排程提醒：{dt.strftime("%Y-%m-%d %H:%M（%Z）")}')
                    continue
                else:
                    send_message(chat_id, '我沒抓到時間，請用「提醒我 明天上午9點 做X」的格式。')
                    continue

            history_text = '\n'.join([f"USER: {h['text']}" if h['role']=='user' else f"ASSISTANT: {h['text']}" for h in hist])
            # retrieve relevant memory snippets
            try:
                from scripts.retriever import retrieve_similar
                relevant = retrieve_similar(chat_id, text, topk=3)
            except Exception:
                relevant = []
            mem_text = ''
            if relevant:
                mem_text = '\n'.join([f"MEMORY (score {s:.3f}): {d}" for d,s in relevant])
            if mem_text:
                full_prompt = system_prompt + '\n\n' + 'RELATED MEMORY:\n' + mem_text + '\n\n' + history_text + '\n\nUSER: ' + text + '\nASSISTANT:'
            else:
                full_prompt = system_prompt + '\n\n' + history_text + '\n\nUSER: ' + text + '\nASSISTANT:'

            # send typing action and optional placeholder while model runs
            def send_typing_repeat(stop_flag):
                try:
                    while not stop_flag['stop']:
                        urllib.request.urlopen(API + f"/sendChatAction?chat_id={chat_id}&action=typing")
                        time.sleep(6)
                except Exception:
                    pass

            stop_flag = {'stop': False}
            import threading
            t = threading.Thread(target=send_typing_repeat, args=(stop_flag,), daemon=True)
            t.start()

            placeholder_id = None
            try:
                # send a placeholder message that we'll edit later
                ph = urllib.request.urlopen(API + '/sendMessage', data=urllib.parse.urlencode({'chat_id': chat_id, 'text': '💭 我在思考，等一下給你完整回覆…'}).encode(), timeout=10)
                ph_res = json.load(ph)
                if ph_res.get('ok'):
                    placeholder_id = ph_res['result']['message_id']
            except Exception:
                placeholder_id = None

            # call local agent
            try:
                p = subprocess.run(['/Users/yoyo/.openclaw/workspace-lalifu/scripts/agent_qwen.sh', full_prompt], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
                reply = p.stdout.strip() or 'No reply from model.'
            except subprocess.TimeoutExpired:
                logp = Path('workspace/logs/model_timeouts')
                logp.parent.mkdir(parents=True, exist_ok=True)
                import uuid
                fname = logp.parent / f'timeout_{int(time.time())}_{uuid.uuid4().hex}.txt'
                fname.write_text(full_prompt, encoding='utf-8')
                reply = '抱歉，模型回應超時了，我會再試一次或你可以稍後再問。'
            except Exception as e:
                logp = Path('workspace/logs/model_errors')
                logp.parent.mkdir(parents=True, exist_ok=True)
                import uuid
                fname = logp.parent / f'error_{int(time.time())}_{uuid.uuid4().hex}.txt'
                fname.write_text(full_prompt + '\n\nERROR:\n' + str(e), encoding='utf-8')
                reply = '系統錯誤：模型回應失敗，已記錄錯誤，稍後查看。'

            # stop typing thread
            stop_flag['stop'] = True
            try:
                t.join(timeout=1)
            except Exception:
                pass

            # append assistant reply to history and save
            hist.append({'role':'assistant','text':reply,'ts':int(time.time())})
            hist = hist[-HISTORY_LEN:]
            save_history(chat_id, hist)

            # send or edit placeholder
            if placeholder_id is not None:
                try:
                    data = urllib.parse.urlencode({'chat_id': chat_id, 'message_id': placeholder_id, 'text': reply}).encode()
                    urllib.request.urlopen(API + '/editMessageText', data=data, timeout=10)
                except Exception:
                    send_message(chat_id, reply)
            else:
                send_message(chat_id, reply)
    except KeyboardInterrupt:
        print('stopped')
        sys.exit(0)
    except Exception as e:
        print('loop error:', e)
        time.sleep(2)
