"""ChromaDB vector store for documents and products."""

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction as ChromaOpenAIEF

from app.config import settings

_client: chromadb.ClientAPI | None = None
_embedding_fn: ChromaOpenAIEF | None = None


def get_chroma() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_embedding_fn() -> ChromaOpenAIEF:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = ChromaOpenAIEF(
            api_key=settings.llm_api_key,
            api_base=settings.llm_base_url,
            model_name=settings.embedding_model,
        )
    return _embedding_fn


def get_or_create_collection(name: str) -> chromadb.Collection:
    client = get_chroma()
    ef = get_embedding_fn()
    return client.get_or_create_collection(
        name=name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


# ── Document retrieval ──────────────────────────────────────

DOC_COLLECTION = "knowledge_base"
PRODUCT_COLLECTION = "products"


async def index_documents(docs: list[tuple[int, str, str]]):
    """Index documents into ChromaDB.

    Args:
        docs: list of (id, title, content)
    """
    if not docs:
        return
    collection = get_or_create_collection(DOC_COLLECTION)
    ids = [str(d[0]) for d in docs]
    documents = [d[2] for d in docs]
    metadatas = [{"title": d[1], "source_id": d[0]} for d in docs]
    collection.add(ids=ids, documents=documents, metadatas=metadatas)


async def index_products(products: list[tuple[int, str, str, str]]):
    """Index products into ChromaDB.

    Args:
        products: list of (id, name, category, description)
    """
    if not products:
        return
    collection = get_or_create_collection(PRODUCT_COLLECTION)
    ids = [f"prod_{p[0]}" for p in products]
    documents = [f"{p[1]} ({p[2]}) - {p[3]}" for p in products]
    metadatas = [{"name": p[1], "category": p[2], "source_id": p[0]} for p in products]
    # Upsert: remove existing then add
    try:
        collection.delete(ids=ids)
    except Exception:
        pass
    collection.add(ids=ids, documents=documents, metadatas=metadatas)


def search_documents(query: str, top_k: int = 20) -> list[tuple[int, float]]:
    """Search knowledge base documents. Returns [(source_id, distance), ...]"""
    try:
        collection = get_or_create_collection(DOC_COLLECTION)
    except Exception:
        return []
    results = collection.query(query_texts=[query], n_results=top_k)
    if not results["ids"] or not results["ids"][0]:
        return []
    items = []
    for i, doc_id in enumerate(results["ids"][0]):
        source_id = int(results["metadatas"][0][i].get("source_id", doc_id))
        distance = results["distances"][0][i] if results["distances"] else 0.0
        similarity = 1.0 - min(distance, 1.0)
        items.append((source_id, similarity))
    return items


def search_products(query: str, top_k: int = 5) -> list[tuple[int, float]]:
    """Search products by semantic similarity."""
    try:
        collection = get_or_create_collection(PRODUCT_COLLECTION)
    except Exception:
        return []
    results = collection.query(query_texts=[query], n_results=top_k)
    if not results["ids"] or not results["ids"][0]:
        return []
    items = []
    for i, doc_id in enumerate(results["ids"][0]):
        source_id = int(results["metadatas"][0][i].get("source_id", doc_id.split("_")[-1]))
        distance = results["distances"][0][i] if results["distances"] else 0.0
        similarity = 1.0 - min(distance, 1.0)
        items.append((source_id, similarity))
    return items
