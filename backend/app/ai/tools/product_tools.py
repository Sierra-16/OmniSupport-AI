"""Product-related tools for PreSales Agent."""

import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.product import Product
from app.ai.rag.retriever import HybridRetriever


async def search_knowledge_base(db: AsyncSession, query: str) -> str:
    """Search the product knowledge base / FAQ using hybrid RAG retrieval."""
    retriever = HybridRetriever(db)
    results = await retriever.retrieve(query, top_k=3)
    if not results:
        return "未找到相关知识库内容。"
    parts = []
    for r in results:
        parts.append(f"### {r['title']} (相关度: {r['score']:.2f})\n{r['content']}")
    return "\n\n".join(parts)


# Common Chinese aliases → product name keywords
PRODUCT_ALIASES: dict[str, list[str]] = {
    "苹果电脑": ["MacBook", "iMac", "Mac"],
    "苹果笔记本": ["MacBook", "MacBook Air", "MacBook Pro"],
    "苹果手机": ["iPhone"],
    "华为手机": ["HUAWEI", "Mate"],
    "三星手机": ["Samsung", "Galaxy"],
    "小米手机": ["Xiaomi"],
    "安卓手机": ["Samsung", "Xiaomi", "OPPO", "HUAWEI"],
    "手机": ["iPhone", "Samsung", "Galaxy", "Xiaomi", "HUAWEI", "Mate", "OPPO", "手机"],
    "平板": ["iPad", "Pad"],
    "苹果平板": ["iPad"],
    "耳机": ["AirPods", "耳机", "Bose", "Sony", "QuietComfort"],
    "手表": ["Watch", "手表"],
    "无人机": ["DJI", "Mini", "无人机"],
    "笔记本": ["MacBook", "ThinkPad", "ASUS", "笔记本"],
    "电脑": ["MacBook", "ThinkPad", "ASUS", "笔记本", "电脑"],
    "家电": ["Dyson", "吸尘器", "扫地", "咖啡"],
    "音箱": ["音箱", "Marshall", "Stanmore"],
    "阅读器": ["Kindle", "Scribe"],
}


def _resolve_aliases(keyword: str) -> list[str]:
    """Expand a Chinese alias into brand/product name keywords for search."""
    terms = [keyword]
    # Match longest alias first to avoid overly broad expansions
    # (e.g., "苹果电脑" should match specifically, not "电脑" → all brands)
    best_match = None
    for alias in sorted(PRODUCT_ALIASES.keys(), key=len, reverse=True):
        if alias in keyword:
            best_match = alias
            break
    if best_match:
        terms.extend(PRODUCT_ALIASES[best_match])
    return list(set(terms))  # dedup


async def query_product(db: AsyncSession, keyword: str | None = None, category: str | None = None) -> str:
    """Search products by keyword or category."""
    from sqlalchemy import func, or_

    products = []
    if keyword:
        keyword_no_space = keyword.replace(" ", "")
        expanded_terms = _resolve_aliases(keyword)

        # Try 1: search with all expanded terms (alias → brand names)
        conditions = []
        for term in expanded_terms:
            conditions.append(Product.name.ilike(f"%{term}%"))
            conditions.append(Product.description.ilike(f"%{term}%"))
        stmt = select(Product).where(or_(*conditions))
        if category:
            stmt = stmt.where(Product.category == category)
        stmt = stmt.limit(10)
        result = await db.execute(stmt)
        products = result.scalars().all()

        # Try 2: space-normalized fallback
        if not products:
            conds2 = []
            for term in expanded_terms:
                t = term.replace(" ", "")
                conds2.append(func.replace(Product.name, " ", "").ilike(f"%{t}%"))
                conds2.append(func.replace(Product.description, " ", "").ilike(f"%{t}%"))
            stmt2 = select(Product).where(or_(*conds2))
            if category:
                stmt2 = stmt2.where(Product.category == category)
            stmt2 = stmt2.limit(10)
            result = await db.execute(stmt2)
            products = result.scalars().all()
    else:
        stmt = select(Product)
        if category:
            stmt = stmt.where(Product.category == category)
        stmt = stmt.limit(5)
        result = await db.execute(stmt)
        products = result.scalars().all()

    if not products:
        return "未找到匹配的商品。"
    return json.dumps(
        [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "stock": p.stock_quantity,
                "description": p.description,
            }
            for p in products
        ],
        ensure_ascii=False,
        indent=2,
    )


async def check_stock(db: AsyncSession, product_id: int) -> str:
    """Check stock quantity for a specific product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return "商品不存在。"
    return json.dumps(
        {"product_id": product.id, "name": product.name, "stock_quantity": product.stock_quantity},
        ensure_ascii=False,
    )
