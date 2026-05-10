import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.ai.tools.order_tools import query_order, track_logistics, apply_refund

AFTERSALES_SYSTEM = """你是 OmniSupport 电商平台的售后处理专员。你的职责：
1. 帮助用户查询订单状态和物流信息
2. 处理退换货和退款申请
3. 解答支付相关问题

核心规则：
- 用户问你"订单到哪了""物流进度""我的订单"等，你必须直接使用 [工具查询结果] 中的真实数据回答，绝对不能索要订单号或让用户提供额外信息——系统已自动根据 user_id 查出订单
- 保持耐心、共情的中文语气
- 展示订单列表时，使用 seq 字段作为订单序号（从 1 开始），不要使用 id 字段
- 退款金额超过 {threshold} 元需要管理员审批，请如实告知用户
- 不要编造任何订单号、物流单号或用户 ID 格式
- 如果工具返回"未找到相关订单"，告知用户暂无订单记录即可"""


def _extract_json(text: str) -> dict | None:
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    if "```" in text:
        parts = text.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                continue

    m = re.search(r'\{[^{}]*"action"\s*:\s*"[^"]+"[^{}]*\}', text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return None


def _classify_action(user_message: str) -> dict:
    msg = user_message.lower()
    if any(kw in msg for kw in ["退款", "退钱", "退货", "退换"]):
        return {"action": "request_refund", "order_id": None, "reason": user_message}
    if any(kw in msg for kw in ["物流", "到哪", "快递", "运输", "发货", "送达", "签收", "什么时候到"]):
        return {"action": "query_orders", "order_id": None, "reason": "logistics_query"}
    if any(kw in msg for kw in ["订单", "买了", "购买的", "我的macbook", "我的iphone"]):
        return {"action": "query_orders", "order_id": None, "reason": "order_query"}
    return {"action": "general", "order_id": None, "reason": ""}


async def run_aftersales(
    db: Any,
    user_id: int,
    conversation_id: int,
    user_message: str,
    chat_history: list[dict],
    historical_context: str = "",
    stream_callback: callable = None,
    token_callback: callable = None,
) -> dict:
    llm = ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        temperature=0,
    )

    action_prompt = f"""你是一个售后操作分类器。只返回一行 JSON，不要任何解释。

用户消息：{user_message}

可选操作: query_orders(查订单), track_logistics(查物流), request_refund(申请退款), general(其他)

只返回: {{"action":"操作名","order_id":null,"reason":"原因"}}"""

    action_info = None
    try:
        resp = await llm.ainvoke([SystemMessage(content=action_prompt)])
        action_info = _extract_json(resp.content)
    except Exception:
        pass

    if action_info is None:
        action_info = _classify_action(user_message)

    action = action_info.get("action", "query_orders")
    raw_order_id = action_info.get("order_id")
    try:
        order_id = int(raw_order_id) if raw_order_id is not None else None
    except (ValueError, TypeError):
        order_id = None

    tool_result = ""
    requires_human = False
    refund_id = None

    if action in ("query_orders", "query_specific_order", "track_logistics"):
        if stream_callback:
            await stream_callback("aftersales", "running",
                "正在查询物流..." if action == "track_logistics" else "正在查询订单信息...")

        if order_id and action == "track_logistics":
            tool_result = await track_logistics(db, order_id)
        else:
            tool_result = await query_order(db, user_id, order_id)

    elif action == "request_refund":
        if stream_callback:
            await stream_callback("aftersales", "running", "正在处理退款申请...")
        reason = action_info.get("reason", user_message)
        tool_result = await apply_refund(db, user_id, order_id or 0, reason)
        try:
            result_data = json.loads(tool_result)
            if result_data.get("status") == "pending_review":
                requires_human = True
                refund_id = result_data.get("refund_id")
        except json.JSONDecodeError:
            pass

    system_prompt = AFTERSALES_SYSTEM.format(threshold=settings.refund_approval_threshold)
    if historical_context:
        system_prompt += f"\n\n[客户历史记录]\n{historical_context}\n请结合以上历史记录提供个性化服务。"
    if tool_result:
        system_prompt += f"\n\n[工具查询结果]\n{tool_result}"
    else:
        system_prompt += "\n\n[工具查询结果]\n未找到相关订单。请告知用户暂无订单记录，不要索要任何信息。"

    messages = [SystemMessage(content=system_prompt)]
    for msg in chat_history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    if stream_callback:
        await stream_callback("aftersales", "running", "正在生成回复...")

    if token_callback:
        full_response = ""
        async for chunk in llm.astream(messages):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                await token_callback(token)
                full_response += token
        return {"response": full_response, "requires_human": requires_human, "refund_id": refund_id}

    resp = await llm.ainvoke(messages)

    return {"response": resp.content, "requires_human": requires_human, "refund_id": refund_id}
