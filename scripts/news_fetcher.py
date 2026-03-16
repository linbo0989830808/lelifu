#!/usr/bin/env python3
"""
news_fetcher.py (with query support)

- 從 RSS 抓新聞
- 支援 --q 關鍵字過濾（只保留標題/描述包含關鍵字的項目）
- 呼叫本地 ollama qwen2.5:7b 生成 5 條中等長度摘要
- 將結果寫入 workspace/news/YYYY-MM-DD-HH.md

用法範例：
python3 scripts/news_fetcher.py               # 一般抓取
python3 scripts/news_fetcher.py --q OpenClaw  # 只找包含 OpenClaw 的項目
"""

import sys
import subprocess
import datetime
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import argparse

# 配置：RSS 來源清單（可修改）
SOURCES = [
    # General / headlines (temporarily disabled)
    # "http://feeds.bbci.co.uk/news/rss.xml",
    # "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    # 中央社（國際） (temporarily disabled)
    # "https://feeds.feedburner.com/rsscna/intworld",
    # Hacker / developer / aggregator
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/programming/.rss",
    "https://lobste.rs/rss",
    # 科技、科學、財經（保留）
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    # Google News search example (可替換關鍵字)
    "https://news.google.com/rss/search?q=OpenClaw&hl=en-US&gl=US&ceid=US:en"
]

MAX_ITEMS_PER_SOURCE = 8
OUTPUT_DIR = "workspace/news"
MODEL_CMD_TEMPLATE = ['ollama', 'run', 'qwen2.5:7b']


def load_env_file(path):
    try:
        for raw_line in path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    except FileNotFoundError:
        return


def load_telegram_env():
    # Prefer already-exported environment variables; otherwise fall back to local .env files.
    if os.environ.get('TELEGRAM_BOT_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'):
        return

    script_dir = Path(__file__).resolve().parent
    candidates = [
        Path.cwd() / '.env',
        script_dir.parent / '.env',
        script_dir.parent.parent / 'workspace' / '.env',
        script_dir.parent.parent / 'workspace' / 'workspace' / '.env',
    ]

    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        load_env_file(candidate)
        if os.environ.get('TELEGRAM_BOT_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'):
            return


def fetch_rss_items(url, max_items=8, retries=3, backoff=2):
    for attempt in range(1, retries+1):
        try:
            req = Request(url, headers={'User-Agent': 'news-fetcher/1.0'})
            with urlopen(req, timeout=10) as resp:
                data = resp.read()
            root = ET.fromstring(data)
            items = []
            for item in root.findall('.//item')[:max_items]:
                title = item.findtext('title') or ''
                link = item.findtext('link') or ''
                desc = item.findtext('description') or ''
                items.append({'title': title.strip(), 'link': link.strip(), 'desc': desc.strip()})
            if not items:
                for entry in root.findall('.//entry')[:max_items]:
                    title = entry.findtext('title') or ''
                    link = ''
                    l = entry.find('link')
                    if l is not None and 'href' in l.attrib:
                        link = l.attrib['href']
                    summary = entry.findtext('summary') or entry.findtext('content') or ''
                    items.append({'title': title.strip(), 'link': link.strip(), 'desc': summary.strip()})
            return items
        except Exception as e:
            log(f"fetch_rss_items: attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                import time
                time.sleep(backoff ** attempt)
            else:
                return []


def filter_items(collected, query=None):
    if not query:
        return collected
    q = query.lower()
    filtered = []
    for src, items in collected:
        hits = [it for it in items if q in (it.get('title','').lower() + ' ' + it.get('desc','').lower())]
        if hits:
            filtered.append((src, hits))
    return filtered


def build_prompt(collected_items):
    lines = ["下面是抓到的新聞標題與連結，請把它們整理成 5 條中等長度的新聞播報，每條 1-2 句，並在每條後面提供來源 URL：\n"]
    for src, items in collected_items:
        lines.append(f"來源：{src}")
        for it in items:
            lines.append(f"- {it['title']} | {it['link']}")
    lines.append('\n請直接給出 5 條簡短分項，不要多餘前置說明。')
    return '\n'.join(lines)


def call_model(prompt_text, retries=2):
    cmd = MODEL_CMD_TEMPLATE + [prompt_text]
    for attempt in range(1, retries+1):
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
            out = proc.stdout.strip()
            if proc.returncode == 0 and out:
                return out
            log(f"call_model: attempt {attempt} returned non-zero or empty stdout; stderr: {proc.stderr.strip()}")
        except Exception as e:
            log(f"call_model: attempt {attempt} exception: {e}")
    return "ERROR: model failed after retries"


def save_output(text, outdir=OUTPUT_DIR, tag=None):
    os.makedirs(outdir, exist_ok=True)
    now = datetime.datetime.now()
    suffix = f"-{tag}" if tag else ""
    fname = now.strftime("%Y-%m-%d-%H") + suffix + ".md"
    path = os.path.join(outdir, fname)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# News Brief — {now.strftime('%Y-%m-%d %H:00')}\n\n")
        f.write(text)
        f.write('\n')
    return path


def log(msg):
    os.makedirs('workspace/logs', exist_ok=True)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ln = f"[{now}] {msg}\n"
    with open('workspace/logs/news_fetcher.log', 'a', encoding='utf-8') as lf:
        lf.write(ln)
    print(msg)


def find_latest_file(tag=None):
    d = OUTPUT_DIR
    if not os.path.isdir(d):
        return None
    files = [f for f in os.listdir(d) if f.endswith('.md')]
    files.sort(reverse=True)
    if tag:
        files = [f for f in files if ('-' + tag + '.') in f]
    return os.path.join(d, files[0]) if files else None


def send_file_to_telegram(path, tg_token, tg_chat):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        import urllib.parse, urllib.request
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        data = {'chat_id': tg_chat, 'text': content}
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded)
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
        log(f"Telegram: sent file {path}")
        return True
    except Exception as e:
        log(f"Telegram send_file failed: {e}")
        return False


def main():
    load_telegram_env()

    parser = argparse.ArgumentParser()
    parser.add_argument('--q', help='keyword to filter (case-insensitive)')
    parser.add_argument('--send-only', action='store_true', help='send latest saved file to Telegram')
    args = parser.parse_args()

    if args.send_only:
        tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        tg_chat = os.environ.get('TELEGRAM_CHAT_ID')
        if not (tg_token and tg_chat):
            log('send-only requested but TELEGRAM_BOT_TOKEN/CHAT not set')
            sys.exit(1)
        latest = find_latest_file()
        if not latest:
            log('send-only: no saved file found')
            sys.exit(1)
        send_file_to_telegram(latest, tg_token, tg_chat)
        print(f"SENT: {latest}")
        sys.exit(0)

    collected = []
    for src in SOURCES:
        items = fetch_rss_items(src, MAX_ITEMS_PER_SOURCE)
        if items:
            collected.append((src, items))
    if not collected:
        log("No RSS items fetched from any source.")
        print("目前無法抓到任何 RSS 項目，請檢查來源或網路。")
        sys.exit(1)

    filtered = filter_items(collected, args.q)
    if args.q and not filtered:
        log(f"No items match query '{args.q}'")
        print(f"在來源中找不到包含關鍵字 '{args.q}' 的項目。")
        sys.exit(0)

    prompt = build_prompt(filtered if args.q else collected)
    log("Calling model for summary generation...")
    model_out = call_model(prompt)

    if model_out.startswith("ERROR") or len(model_out) < 20:
        log("Model failed or returned too-short output; using fallback list")
        fallback_lines = []
        cnt = 0
        source_list = filtered if args.q else collected
        for src, items in source_list:
            for it in items:
                fallback_lines.append(f"{it['title']} — {it['link']}")
                cnt += 1
                if cnt >= 5:
                    break
            if cnt >= 5:
                break
        final_text = "\n".join([f"{i+1}. {l}" for i, l in enumerate(fallback_lines)])
    else:
        final_text = model_out

    tag = args.q.replace(' ', '_') if args.q else None
    outpath = save_output(final_text, tag=tag)
    log(f"SAVED: {outpath}")

    # 如果環境變數提供了 Telegram 設定，則嘗試發送（但改成短來源顯示）
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    tg_chat = os.environ.get('TELEGRAM_CHAT_ID')
    if tg_token and tg_chat:
        try:
            # 轉成短來源格式（若可能）
            short_lines = []
            count = 0
            source_list = filtered if args.q else collected
            for src, items in source_list:
                for it in items:
                    domain = it.get('link','')
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(it.get('link','')).netloc or src
                    except Exception:
                        domain = src
                    short_lines.append(f"{count+1}) {it.get('title','')}\n來源：{domain}")
                    count += 1
                    if count >= 5:
                        break
                if count >= 5:
                    break
            send_text = "早晨簡報（簡短）:\n\n" + "\n\n".join(short_lines)
            import urllib.parse, urllib.request
            url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            data = {'chat_id': tg_chat, 'text': send_text}
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_encoded)
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
            log("Telegram: sent")
        except Exception as e:
            log(f"Telegram send failed: {e}")


if __name__ == '__main__':
    main()
