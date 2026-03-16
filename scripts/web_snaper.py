#!/usr/bin/env python3
# web_snaper.py - fetch page title and first image URL
import sys
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print('Usage: web_snaper.py <url>')
    sys.exit(1)
url = sys.argv[1]
req = Request(url, headers={'User-Agent':'python-web-snaper/1.0'})
with urlopen(req, timeout=10) as r:
    html = r.read()
soup = BeautifulSoup(html, 'html.parser')
title = soup.title.string.strip() if soup.title else 'No title'
img = soup.find('img')
imgsrc = img.get('src') if img else 'No image'
print('Title:', title)
print('First image:', imgsrc)
