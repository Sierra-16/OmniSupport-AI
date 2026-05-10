import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.ai.tools.ticket_tools import create_ticket, escalate_to_human

COMPLAINT_SYSTEM = """你是 OmniSupport 的投诉处理专员。你的职责：
1. 安抚用户情绪，表达真诚的歉意和理解
2. 记录投诉内容并创建工单
3. 在需要时升级到人工坐席

注意事项：
- 始终保持耐心和同理心
- 先安抚情绪，再解决问题
- 如果用户明确要求转人工，立即触发转接
- 记录投诉时提取关键信息（订单号、问题类型等）"""


async def run_complaint(
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
        temperature=0.5,
    )

    human_keywords = ["转人工", "人工客服", "人工服务", "找人工", "真人", "投诉你", "叫你们领导"]
    user_wants_human = any(kw in user_message for kw in human_keywords)

    if user_wants_human:
        if stream_callback:
            await stream_callback("complaint", "running", "正在转接人工坐席...")
        escalate_result = json.loads(await escalate_to_human(user_id, "用户主动要求人工服务"))
        return {"response": escalate_result["message"], "requires_human": True}

    tool_result = ""
    if "投诉" in user_message or "不满意" in user_message or "差评" in user_message:
        if stream_callback:
            await stream_callback("complaint", "running", "正在创建投诉工单...")
        tool_result = await create_ticket(db, user_id, "用户投诉", user_message)

    system_prompt = COMPLAINT_SYSTEM
    if historical_context:
        system_prompt += f"\n\n[客户历史记录]\n{historical_context}\n请结合以上历史记录了解客户背景。"
    if tool_result:
        system_prompt += f"\n\n[工单创建结果]\n{tool_result}"

    messages = [SystemMessage(content=system_prompt)]
    for msg in chat_history[-6:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    if stream_callback:
        await stream_callback("complaint", "running", "正在生成回复...")

    if token_callback:
        full_response = ""
        async for chunk in llm.astream(messages):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            if token:
                await token_callback(token)
                full_response += token
        requires_human = "转人工" in full_response or "升级" in full_response
        return {"response": full_response, "requires_human": requires_human}

    resp = await llm.ainvoke(messages)
    requires_human = "转人工" in resp.content or "升级" in resp.content

    return {"response": resp.content, "requires_human": requires_human}
