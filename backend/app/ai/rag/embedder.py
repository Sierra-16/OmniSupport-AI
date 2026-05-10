"""Embedding service via OpenAI-compatible API (DashScope / OpenAI / etc.).

Also provides a ChromaDB-compatible embedding function for auto-embedding.
"""

from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def get_embedding_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    return _client


async def embed_text(text: str) -> list[float]:
    client = get_embedding_client()
    resp = await client.embeddings.create(model=settings.embedding_model, input=[text])
    return resp.data[0].embedding


async def embed_texts(texts: list[str]) -> list[list[float]]:
    client = get_embedding_client()
    resp = await client.embeddings.create(model=settings.embedding_model, input=texts)
    return [d.embedding for d in resp.data]


class OpenAIEmbeddingFunction:
    """ChromaDB-compatible embedding function that uses the project's configured LLM."""

    def __call__(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        return asyncio.run(embed_texts(texts))
