"""Ollama providers — chat (qwen3.5) và embedding (bge-m3).

Port nguyên hành vi từ services/llm.py (PoC) sang lớp provider. Giữ đúng: chat
với think=false + temperature 0.1; embedding cắt theo max_embed_chars.
"""

import json
from collections.abc import AsyncIterator

import httpx

from app.config import settings


class OllamaEmbeddingProvider:
    """Sinh embedding qua Ollama /api/embeddings."""

    async def embed_text(self, text: str) -> list[float]:
        # Cắt độ dài: model embedding từ chối input quá dài. Phần đầu một điều
        # luật (tiêu đề + khoản mở) rất đại diện cho chủ đề, nên cắt không hại
        # chất lượng khớp.
        prompt = text[: settings.max_embed_chars]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={"model": settings.embed_model, "prompt": prompt},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(t) for t in texts]


class OllamaChatProvider:
    """Streaming chat qua Ollama /api/chat (thinking tắt)."""

    async def stream(
        self, system_prompt: str, user_message: str
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": True,
                    "think": False,
                    "options": {"temperature": 0.1, "num_ctx": 4096},
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if content := data.get("message", {}).get("content", ""):
                        yield content
                    if data.get("done", False):
                        break
