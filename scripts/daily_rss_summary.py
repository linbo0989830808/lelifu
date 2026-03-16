#!/usr/bin/env python3
"""daily_rss_summary.py
簡單腳本：抓取設定來源的 RSS，取每來源前 5 條標題，合成一個 Markdown 檔。
"""
import os
import datetime
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

SOURCES = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
]
OUTPUT_DIR = "workspace/news"
MAX = 5

os.makedirs(OUTPUT_DIR, exist_ok=True)
now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
fpath = os.path.join(OUTPUT_DIR, f"daily-summary-{now}.md")
lines = [f"# Daily RSS Summary — {now}\n"]

for src in SOURCES:
    try:
        req = Request(src, headers={'User-Agent':'fetcher/1.0'})
        with urlopen(req, timeout=10) as r:
            data = r.read()
        root = ET.fromstring(data)
        items = root.findall('.//item')[:MAX]
        lines.append(f"## Source: {src}\n")
        if not items:
            lines.append("(no items)\n")
        for it in items:
            t = it.findtext('title') or ''
            l = it.findtext('link') or ''
            lines.append(f"- {t.strip()} — {l.strip()}\n")
    except Exception as e:
        lines.append(f"- Failed to fetch {src}: {e}\n")

with open(fpath, 'w', encoding='utf-8') as f:
    f.writelines([ln + "\n" if not ln.endswith('\n') else ln for ln in lines])

print(f"Saved: {fpath}")
