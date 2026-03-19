#!/usr/bin/env python3
# Retriever: use Faiss if available, else fall back to TF-IDF / substring
from pathlib import Path
import os
import json

INDEX_DIR = Path('memory/vecindex')
HIST_DIR = Path('memory/telegram_history')

def faiss_retrieve(query, topk=3):
    try:
        import faiss, pickle, numpy as np
        from sentence_transformers import SentenceTransformer
    except Exception:
        return []
    idx_path = INDEX_DIR / 'index.faiss'
    meta_path = INDEX_DIR / 'meta.pkl'
    if not idx_path.exists() or not meta_path.exists():
        return []
    # load
    index = faiss.read_index(str(idx_path))
    with open(meta_path,'rb') as f:
        meta = pickle.load(f)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    emb = model.encode([query])
    xb = np.array(emb).astype('float32')
    faiss.normalize_L2(xb)
    D, I = index.search(xb, topk)
    res = []
    for score, i in zip(D[0], I[0]):
        if i < 0 or i >= len(meta): continue
        entry = meta[i]
        # read role from stored history
        try:
            hist = json.loads(Path('memory/telegram_history') / f"{entry['chat_id']}.json" .read_text(encoding='utf-8'))
            role = hist[entry['idx']].get('role','user')
        except Exception:
            role = 'user'
        res.append((meta[i]['text'], float(score), role))
    # prefer user-role items first
    user_items = [ (t,s) for t,s,r in res if r=='user']
    other_items = [ (t,s) for t,s,r in res if r!='user']
    out = user_items[:topk]
    if len(out) < topk:
        out += other_items[:(topk-len(out))]
    return out


def retrieve_similar(chat_id, query, topk=3):
    # try faiss first
    r = faiss_retrieve(query, topk=topk)
    if r:
        return r
    # fallback to per-chat TF-IDF or substring
    p = HIST_DIR / f'{chat_id}.json'
    if not p.exists():
        return []
    hist = json.loads(p.read_text(encoding='utf-8'))
    docs = [h['text'] for h in hist]
    if not docs:
        return []
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vec = TfidfVectorizer().fit_transform(docs + [query])
        sims = cosine_similarity(vec[-1], vec[:-1])[0]
        idx = sims.argsort()[::-1][:topk]
        return [(docs[i], float(sims[i])) for i in idx if sims[i] > 0]
    except Exception:
        scores = []
        q = query.lower()
        for d in docs:
            s = d.lower().count(q.split()[0]) if q.split() else 0
            scores.append(s)
        idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:topk]
        return [(docs[i], float(scores[i])) for i in idx if scores[i]>0]

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: retriever.py <chat_id> <query>')
        sys.exit(1)
    cid = sys.argv[1]
    q = ' '.join(sys.argv[2:])
    print(retrieve_similar(cid, q))
