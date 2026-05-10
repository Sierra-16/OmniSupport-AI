"""Cross-encoder style reranker using LLM-based scoring.

Uses the project's configured LLM (default: Qwen via DashScope) to score passage relevance.
For production, swap with bge-reranker-v2-m3 or Cohere Rerank.
"""

from openai import AsyncOpenAI

from app.config import settings


async def rerank(query: str, documents: list[tuple[int, str]], top_k: int = 5) -> list[tuple[int, float]]:
    """Rerank candidate documents using an LLM relevance score (1-10).

    For production use, swap this with a dedicated reranker model.
    """
    if not documents:
        return []

    client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)

    scored: list[tuple[int, float]] = []
    for doc_id, content in documents:
        prompt = f"""Rate how relevant this passage is to the user's query on a scale of 1-10.
Reply with only a number.

Query: {query}
Passage: {content[:1200]}
Relevance (1-10):"""

        try:
            resp = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0,
            )
            score_text = resp.choices[0].message.content.strip()
            score = float(score_text) / 10.0
        except Exception:
            score = 0.5  # fallback on error

        scored.append((doc_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
