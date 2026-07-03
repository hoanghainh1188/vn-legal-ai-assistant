"""Ollama LLM client — embedding and streaming chat."""

from collections.abc import AsyncIterator

import httpx

from app.config import settings


async def embed_text(text: str) -> list[float]:
    # Cap length: the embedding model rejects very long inputs. A prefix of a
    # legal article (heading + opening clauses) is highly representative of its
    # topic, so truncating for retrieval does not hurt match quality.
    prompt = text[: settings.max_embed_chars]
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/embeddings",
            json={"model": settings.embed_model, "prompt": prompt},
        )
        response.raise_for_status()
        return response.json()["embedding"]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    return [await embed_text(t) for t in texts]


async def chat_stream(
    system_prompt: str,
    user_message: str,
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
            import json

            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if content := data.get("message", {}).get("content", ""):
                    yield content
                if data.get("done", False):
                    break
