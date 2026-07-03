"""LLM/embedding provider abstraction.

Nhà cung cấp chat và embedding nằm sau interface (base.py) và được chọn qua
factory theo cấu hình — để đổi provider (Ollama ↔ Claude) mà không sửa business
logic RAG. Xem specs/001-llm-provider-abstraction/.
"""
