"""Hybrid retriever orchestrating vector search + BM25 + RRF + rerank."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.ai.rag.vector_store import VectorStore
from app.ai.rag.chroma_store import search_products
from app.ai.rag.bm25 import BM25Retriever
from app.ai.rag.reranker import rerank


def reciprocal_rank_fusion(
    vector_results: list[tuple[int, float]],
    keyword_results: list[tuple[int, float]],
    top_k: int = 10,
    k: int = 60,
) -> list[int]:
    """Merge two ranked lists using RRF (Reciprocal Rank Fusion)."""
    scores: dict[int, float] = {}

    for rank, (doc_id, _) in enumerate(vector_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
    for rank, (doc_id, _) in enumerate(keyword_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return sorted_ids[:top_k]


class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = VectorStore(db)
        self.bm25 = BM25Retriever()

    async def _ensure_bm25_index(self):
        """Build BM25 index from all documents in DB if not already built."""
        result = await self.db.execute(select(Document.id, Document.content))
        docs = [(row.id, row.content) for row in result.fetchall()]
        if docs:
            self.bm25.index(docs)

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Run full hybrid retrieval pipeline and return top-k document contents."""
        await self._ensure_bm25_index()

        # Step 1: parallel vector + keyword retrieval
        vector_results = await self.vector_store.search(query, top_k=20)
        keyword_results = self.bm25.search(query, top_k=20)

        # Step 2: RRF fusion → top-10
        fused_ids = reciprocal_rank_fusion(vector_results, keyword_results, top_k=10)

        if not fused_ids:
            return []

        # Step 3: fetch document contents
        result = await self.db.execute(select(Document).where(Document.id.in_(fused_ids)))
        doc_map = {doc.id: doc for doc in result.scalars().all()}
        candidates = [(did, doc_map[did].content) for did in fused_ids if did in doc_map]

        # Step 4: rerank → top-k
        reranked = await rerank(query, candidates, top_k=top_k)

        return [
            {
                "id": did,
                "title": doc_map[did].title,
                "content": doc_map[did].content,
                "score": score,
            }
            for did, score in reranked
        ]
