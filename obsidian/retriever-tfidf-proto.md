# retriever-tfidf-proto

快速原型（TF-IDF）

- 檔案：scripts/retriever.py（支援 TF-IDF 與 fallback substring）
- 行為：在無向量索引時，用 per-chat TF-IDF 查找相關記憶

優點：快速、不需額外安裝大型套件
缺點：語意相似度弱，對長文本效果有限
