#!/usr/bin/env python3
from pathlib import Path
import json, os
memdir = Path('memory/telegram_history')
outdir = Path('memory/vecindex')
outdir.mkdir(parents=True, exist_ok=True)
all_texts = []
meta = []
for p in memdir.glob('*.json'):
    cid = p.stem
    try:
        arr = json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    for i,entry in enumerate(arr):
        txt = entry.get('text','').strip()
        if not txt: continue
        all_texts.append(txt)
        meta.append({'chat_id':cid,'idx':i,'text':txt})
if not all_texts:
    print('no texts to index')
    exit(0)

# compute embeddings
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
emb = model.encode(all_texts, show_progress_bar=True)

# build faiss
import faiss
import numpy as np
xb = np.array(emb).astype('float32')
d = xb.shape[1]
index = faiss.IndexFlatIP(d)
# normalize for cosine
faiss.normalize_L2(xb)
index.add(xb)

# save
faiss.write_index(index, str(outdir/'index.faiss'))
import pickle
with open(outdir/'meta.pkl','wb') as f:
    pickle.dump(meta,f)
print('built index with', len(meta), 'items')
