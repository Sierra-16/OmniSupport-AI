"""BM25 keyword-based retrieval using rank-bm25."""

from rank_bm25 import BM25Okapi


class BM25Retriever:
    def __init__(self, corpus: list[list[str]] | None = None):
        self._corpus: list[list[str]] = corpus or []
        self._bm25: BM25Okapi | None = None
        if self._corpus:
            self._bm25 = BM25Okapi(self._corpus)

    def index(self, documents: list[tuple[int, str]]):
        """Build BM25 index from (doc_id, content) pairs."""
        self._doc_ids = [doc[0] for doc in documents]
        tokenized = [doc[1].lower().split() for doc in documents]
        self._corpus = tokenized
        self._bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        """Return list of (doc_id, score)."""
        if self._bm25 is None:
            return []
        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self._doc_ids[idx], float(score)) for idx, score in ranked]
