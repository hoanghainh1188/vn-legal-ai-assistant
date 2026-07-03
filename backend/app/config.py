from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    embed_model: str = "bge-m3"
    llm_model: str = "qwen3.5"
    chroma_persist_dir: str = "./chroma_data"
    collection_name: str = "vn_housing_law"
    retrieval_top_k: int = 8
    # bge-m3 supports up to 8192 tokens, enough for a whole article in most
    # cases; cap as a safety net and keep full text for display and LLM context.
    max_embed_chars: int = 8000
    frontend_origin: str = "http://localhost:3000"

    model_config = {"env_prefix": "VN_LEGAL_", "env_file": ".env"}


settings = Settings()
