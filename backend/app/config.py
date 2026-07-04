from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    embed_model: str = "bge-m3"
    llm_model: str = "qwen3.5"
    # Kho vector: Postgres + pgvector. database_url lấy từ env (KHÔNG hardcode),
    # vd postgresql://postgres:postgres@localhost:5432/vn_legal
    database_url: str | None = None
    retrieval_top_k: int = 8
    # Số ứng viên dense lấy trước khi hợp nhất hybrid (RRF + lexical).
    vector_pool: int = 30
    # bge-m3 supports up to 8192 tokens, enough for a whole article in most
    # cases; cap as a safety net and keep full text for display and LLM context.
    max_embed_chars: int = 8000
    frontend_origin: str = "http://localhost:3000"

    # Provider selection (hybrid AI). Default "ollama" giữ hành vi PoC.
    chat_provider: str = "ollama"  # ollama | claude
    embedding_provider: str = "ollama"  # ollama
    claude_api_key: str | None = None  # từ env, KHÔNG hardcode
    claude_model: str = "claude-sonnet-4-6"
    claude_timeout: float = 300.0
    claude_max_tokens: int = 4096  # Anthropic API yêu cầu max_tokens

    model_config = {"env_prefix": "VN_LEGAL_", "env_file": ".env"}


settings = Settings()
