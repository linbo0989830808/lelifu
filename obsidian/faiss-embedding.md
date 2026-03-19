# faiss-embedding

向量化索引（已完成）

- 環境：.venv（已安裝 sentence-transformers, faiss-cpu）
- 腳本：scripts/build_faiss_index.py（將 memory/telegram_history 內文本轉向量並建 index）
- 儲存：memory/vecindex/index.faiss + meta.pkl

效果：語意檢索、速度快，可擴充

注意：需 periodic rebuild 或增量 upsert，並備份 index
