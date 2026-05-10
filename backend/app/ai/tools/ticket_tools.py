"""Complaint & escalation tools for Complaint Agent."""

import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.order import Order


async def create_ticket(db: AsyncSession, user_id: int, title: str, description: str) -> str:
    """Create a complaint/support ticket."""
    # In production, integrate with actual CRM system
    return json.dumps(
        {
            "ticket_id": f"TK-{user_id}-{hash(title) % 100000:05d}",
            "title": title,
            "status": "created",
            "message": "工单已创建，我们的客服团队将在24小时内与您联系。",
        },
        ensure_ascii=False,
        indent=2,
    )


async def escalate_to_human(user_id: int, reason: str) -> str:
    """Escalate the conversation to a human agent (triggers HITL)."""
    return json.dumps(
        {
            "action": "escalate_to_human",
            "user_id": user_id,
            "reason": reason,
            "message": "正在为您转接人工坐席，请稍候...",
        },
        ensure_ascii=False,
    )
