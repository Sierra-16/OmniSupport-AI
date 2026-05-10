"""Vector store adapter — delegates to ChromaDB."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.chroma_store import search_documents, search_products, index_documents, index_products


class VectorStore:
    """pgvector-compatible interface backed by ChromaDB."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        return search_documents(query, top_k=top_k)

    async def index_document(self, doc_id: int, content: str):
        """No-op: indexing is done in batch via ChromaDB."""
        pass

    async def index_documents_batch(self, docs: list[tuple[int, str, str]]):
        """Index a batch of (id, title, content)."""
        await index_documents(docs)

    async def index_products_batch(self, products: list[tuple[int, str, str, str]]):
        """Index a batch of (id, name, category, description)."""
        await index_products(products)
