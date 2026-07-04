"""Ollama providers — chat (qwen3.5) và embedding (bge-m3).

Port nguyên hành vi từ services/llm.py (PoC) sang lớp provider. Giữ đúng: chat
với think=false + temperature 0.1; embedding cắt theo max_embed_chars.
"""

import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider:
    """Sinh embedding qua Ollama /api/embeddings."""

    async def embed_text(self, text: str) -> list[float]:
        # Cắt độ dài: model embedding từ chối input quá dài. Phần đầu một điều
        # luật (tiêu đề + khoản mở) rất đại diện cho chủ đề, nên cắt không hại
        # chất lượng khớp.
        base = text[: settings.max_embed_chars]
        # bge-m3 giới hạn ~8192 token; một số điều tiếng Việt dày đặc (nhiều số/
        # danh sách) vẫn vượt giới hạn dù đã cắt theo KÝ TỰ → Ollama trả 500. Thử
        # lại với độ dài ngắn dần để vẫn embed được — chỉ ảnh hưởng đúng điều bị
        # lỗi, các điều khác vẫn embed ở độ dài đầy đủ (không đổi hành vi).
        limits = [len(base), *[n for n in (6000, 4000, 2000) if n < len(base)]]
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, limit in enumerate(limits):
                response = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json={"model": settings.embed_model, "prompt": base[:limit]},
                )
                if response.is_success:
                    return response.json()["embedding"]
                # CHỈ lùi độ dài khi 500 (input quá dài). Lỗi khác (503 down, 429,
                # 4xx) → raise ngay: thử ngắn hơn không giải quyết, chỉ che lỗi thật.
                is_last = i == len(limits) - 1
                if response.status_code != 500 or is_last:
                    response.raise_for_status()
                logger.warning(
                    "embed_text: Ollama 500 ở %d ký tự, thử lại với %d ký tự",
                    limit,
                    limits[i + 1],
                )
        # Không tới được: vòng lặp luôn return (thành công) hoặc raise (lỗi).
        raise RuntimeError("embed_text: không embed được sau khi thử mọi độ dài")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(t) for t in texts]


class OllamaChatProvider:
    """Streaming chat qua Ollama /api/chat (thinking tắt)."""

    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
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
