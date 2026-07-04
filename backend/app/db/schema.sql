-- Schema kho vector — idempotent (áp lại nhiều lần an toàn).
-- Áp bằng: uv run python scripts/init_db.py

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS legal_chunks (
    id             bigserial PRIMARY KEY,
    document_id    text         NOT NULL,
    article_number int          NOT NULL,
    article_title  text         NOT NULL,
    chapter        text         NOT NULL,
    content        text         NOT NULL,     -- nguyên văn Điều (Constitution II)
    embedding      vector(1024) NOT NULL,      -- bge-m3, cosine
    UNIQUE (document_id, article_number)       -- khoá tự nhiên cho upsert idempotent
);

-- Index ANN cosine (bge-m3). HNSW cho recall tốt.
CREATE INDEX IF NOT EXISTS legal_chunks_embedding_hnsw
    ON legal_chunks USING hnsw (embedding vector_cosine_ops);
