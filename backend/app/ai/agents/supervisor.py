import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings

INTENT_CLASSIFIER_PROMPT = """你是一个电商客服意图分类器。分析用户消息，将意图归类为以下之一：

- presales: 商品咨询（想买什么、有什么推荐、价格多少、有没有货、功能对比）。注意：只要是询问具体商品（手机、耳机、电脑等消费电子产品），都归为 presales
- aftersales: 订单查询、物流追踪、退换货、退款申请、查单号
- complaint: 投诉、不满、情绪宣泄、要求人工服务
- mixed: 同时包含售前和售后问题（如"我刚买的耳机坏了，有没有其他推荐"）

请只返回一个 JSON 对象：
{{"intent": "presales|aftersales|complaint|mixed", "confidence": 0.0-1.0, "reason": "简短说明"}}

用户消息：{user_message}"""


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        temperature=0,
    )


async def classify_intent(user_message: str) -> dict[str, Any]:
    llm = get_llm()
    prompt = INTENT_CLASSIFIER_PROMPT.format(user_message=user_message)
    resp = await llm.ainvoke([SystemMessage(content=prompt)])
    try:
        content = resp.content.strip()
        if "```" in content:
            content = content.split("```")[1].split("```")[0].replace("json", "").strip()
        return json.loads(content)
    except (json.JSONDecodeError, KeyError):
        return {"intent": "presales", "confidence": 0.5, "reason": "fallback"}


def route_by_intent(intent: str) -> list[str]:
    if intent == "presales":
        return ["presales"]
    elif intent == "aftersales":
        return ["aftersales"]
    elif intent == "complaint":
        return ["complaint"]
    elif intent == "mixed":
        return ["presales", "aftersales"]
    return ["presales"]
