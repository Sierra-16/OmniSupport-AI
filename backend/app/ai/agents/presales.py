from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import select

from app.config import settings
from app.ai.tools.product_tools import query_product, check_stock, _resolve_aliases
from app.ai.rag.chroma_store import search_products
from app.models.product import Product

PRESALES_SYSTEM = """你是 OmniSupport 电商平台的售前咨询专员。你所在的平台主营消费电子产品（手机、电脑、耳机、无人机、家电等）。

你的职责：
1. 回答商品相关的问题（规格、价格、功能对比）
2. 根据用户需求推荐适合的商品
3. 查询商品库存
4. 当用户问题超出商品咨询范围时，礼貌引导到相应渠道

重要规则：
- 始终保持热情、专业的中文语气
- 商品数据会以 [商品库查询结果] 提供，你必须基于这些数据回答，不得使用任何训练数据中关于商品是否发布、是否存在的知识
- 只要 [商品库查询结果] 中有匹配的商品，就直接介绍该商品，绝对不能说"该商品尚未发布"或"暂未上线"
- 同一产品线不同型号（如 iPhone 16 与 iPhone 16 Pro Max）视为相关商品，可以推荐
- 不要编造商品信息，只基于工具返回的真实数据回答
- 如果商品库中确实没有用户想要的商品，诚实地告知用户"暂时没有该商品"
- 你不是在推销 OmniSupport AI 系统本身——OmniSupport 只是这个电商平台的名称"""


async def _extract_keyword(user_message: str) -> str:
    llm = ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        temperature=0,
    )
    resp = await llm.ainvoke([
        SystemMessage(content="从用户消息中提取商品搜索关键词，只返回关键词（2-10个字），不要任何解释。如果是完整句子，提取核心商品名词。"),
        HumanMessage(content=user_message),
    ])
    keyword = resp.content.strip()
    return keyword if keyword else user_message


async def _search_products_semantic(db: Any, query: str, top_k: int = 5) -> str:
    product_ids = search_products(query, top_k=top_k)
    if not product_ids:
        expanded = " ".join(_resolve_aliases(query))
        if expanded != query:
            product_ids = search_products(expanded, top_k=top_k)
    if not product_ids:
        return ""

    ids = [pid for pid, _ in product_ids]
    result = await db.execute(select(Product).where(Product.id.in_(ids)))
    products = {p.id: p for p in result.scalars().all()}

    items = []
    for pid, similarity in product_ids:
        p = products.get(pid)
        if p:
            items.append({
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "stock": p.stock_quantity,
                "description": p.description,
                "relevance": round(similarity, 2),
            })

    if not items:
        return ""

    import json
    return json.dumps(items, ensure_ascii=False, indent=2)


async def run_presales(
    db: Any,
    user_id: int,
    conversation_id: int,
    user_message: str,
    chat_history: list[dict],
    historical_context: str = "",
    stream_callback: callable = None,
    token_callback: callable = None,
) -> str:
    llm = ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        temperature=0.3,
    )

    if stream_callback:
        await stream_callback("presales", "running", "正在检索商品库...")

    keyword = await _extract_keyword(user_message)
    semantic_results = await _search_products_semantic(db, user_message)
    ilike_results = await query_product(db, keyword=keyword)

    product_info = semantic_results
    if not product_info and ilike_results != "未找到匹配的商品。":
        product_info = ilike_results

    if not product_info:
        return "很抱歉，我们商城暂时没有您想要的这类商品。您可以尝试搜索其他关键词，或联系人工客服获取更多帮助。如有其他需求，随时告诉我～"

    context_parts = [PRESALES_SYSTEM]

    if historical_context:
        context_parts.append(f"\n[客户历史记录]\n{historical_context}\n请结合以上历史记录提供个性化服务。")

    context_parts.append(f"\n[商品库查询结果]\n{product_info}")

    system_prompt = "\n\n".join(context_parts)

    messages = [SystemMessage(content=system_prompt)]
    for msg in chat_history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    if stream_callback:
        await stream_callback("presales", "running", "正在生成回复...")

    if token_callback:
        full_response = ""
        async for chunk in llm.astream(messages):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                await token_callback(token)
                full_response += token
        return full_response

    resp = await llm.ainvoke(messages)
    return resp.content
