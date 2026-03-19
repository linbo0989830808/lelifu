#!/usr/bin/env python3
import os
import sys
from datetime import datetime

try:
    import markdown
except Exception:
    markdown = None

SITE_DIR = 'site'
POSTS_IN = 'content/posts'
NOVEL_IN = 'content/novel'
POSTS_OUT = os.path.join(SITE_DIR, 'posts')
NOVEL_OUT = os.path.join(SITE_DIR, 'novel')

TEMPLATE = '''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="/styles.css">
</head>
<body>
<header class="site-header"><a href="/index.html">首頁</a></header>
<main class="content">
{content}
</main>
<footer><p>© Lelifu</p></footer>
</body>
</html>'''

os.makedirs(POSTS_OUT, exist_ok=True)
os.makedirs(NOVEL_OUT, exist_ok=True)

def md_to_html(text):
    if markdown:
        return markdown.markdown(text)
    # naive fallback
    lines = text.split('\n')
    out = []
    for ln in lines:
        if ln.startswith('# '): out.append('<h1>%s</h1>'%ln[2:])
        elif ln.startswith('## '): out.append('<h2>%s</h2>'%ln[3:])
        elif ln.strip()=='' : out.append('<p></p>')
        else: out.append('<p>%s</p>'%ln)
    return '\n'.join(out)

# build posts
posts = []
for fn in sorted(os.listdir(POSTS_IN)):
    if not fn.endswith('.md'): continue
    path = os.path.join(POSTS_IN, fn)
    with open(path, encoding='utf-8') as f:
        txt = f.read()
    # simple frontmatter parse
    title = fn.replace('.md','')
    if txt.startswith('---'):
        parts = txt.split('---',2)
        meta = parts[1]
        body = parts[2]
        for line in meta.splitlines():
            if line.startswith('title:'):
                title = line.split(':',1)[1].strip()
    else:
        body = txt
    html = md_to_html(body)
    out = TEMPLATE.format(title=title, content=f'<h1>{title}</h1>\n'+html)
    outfn = os.path.join(POSTS_OUT, fn.replace('.md','.html'))
    with open(outfn,'w',encoding='utf-8') as o:
        o.write(out)
    posts.append((title, 'posts/'+os.path.basename(outfn)))

# build novel
chapters = []
for fn in sorted(os.listdir(NOVEL_IN)):
    if not fn.endswith('.md'): continue
    path = os.path.join(NOVEL_IN, fn)
    with open(path, encoding='utf-8') as f:
        txt = f.read()
    title = fn.replace('.md','')
    if txt.startswith('---'):
        parts = txt.split('---',2)
        meta = parts[1]
        body = parts[2]
        for line in meta.splitlines():
            if line.startswith('title:'):
                title = line.split(':',1)[1].strip()
    else:
        body = txt
    html = md_to_html(body)
    out = TEMPLATE.format(title=title, content=f'<h1>{title}</h1>\n'+html)
    outfn = os.path.join(NOVEL_OUT, fn.replace('.md','.html'))
    with open(outfn,'w',encoding='utf-8') as o:
        o.write(out)
    chapters.append((title, 'novel/'+os.path.basename(outfn)))

# index links
idx_path = os.path.join(SITE_DIR,'index.html')
if os.path.exists(idx_path):
    with open(idx_path,'r',encoding='utf-8') as f:
        idx = f.read()
    # insert posts list
    posts_html = '<ul>' + ''.join([f"<li><a href='/{p[1]}'>{p[0]}</a></li>" for p in posts]) + '</ul>'
    novel_html = '<ul>' + ''.join([f"<li><a href='/{c[1]}'>{c[0]}</a></li>" for c in chapters]) + '</ul>'
    idx = idx.replace('<section>\n      <h2>最新動態</h2>', '<section>\n      <h2>最新動態</h2>')
    idx = idx.replace('</section>\n', f'</section>\n<section>\n<h2>文章</h2>\n{posts_html}\n</section>\n<section>\n<h2>連載小說</h2>\n{novel_html}\n</section>\n')
    with open(idx_path,'w',encoding='utf-8') as f:
        f.write(idx)

print('Built', len(posts), 'posts and', len(chapters), 'chapters')
