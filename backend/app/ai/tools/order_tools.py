"""Order & logistics tools for AfterSales Agent."""

import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.order import Order
from app.models.refund import Refund
from app.config import settings


async def query_order(db: AsyncSession, user_id: int, order_id: int | None = None) -> str:
    """Query order details. If order_id provided, query specific order; otherwise list user's recent orders."""
    if order_id is not None:
        order_id = int(order_id)
    stmt = select(Order).where(Order.user_id == user_id)
    if order_id:
        stmt = stmt.where(Order.id == order_id)
    stmt = stmt.order_by(Order.created_at.desc()).limit(10)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    if not orders:
        return "未找到相关订单。"
    return json.dumps(
        [
            {
                "id": o.id,
                "seq": i + 1,
                "status": o.status,
                "total_amount": o.total_amount,
                "payment_method": o.payment_method,
                "logistics_no": o.logistics_no,
                "logistics_status": o.logistics_status,
                "items": o.items,
                "created_at": str(o.created_at),
            }
            for i, o in enumerate(orders)
        ],
        ensure_ascii=False,
        indent=2,
    )


async def track_logistics(db: AsyncSession, order_id: int) -> str:
    """Track logistics status for an order."""
    order_id = int(order_id)
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return "订单不存在。"
    if not order.logistics_no:
        return "该订单暂无物流信息。"
    return json.dumps(
        {
            "order_id": order.id,
            "logistics_no": order.logistics_no,
            "status": order.logistics_status,
        },
        ensure_ascii=False,
        indent=2,
    )


async def apply_refund(db: AsyncSession, user_id: int, order_id: int, reason: str) -> str:
    """Apply for a refund. Triggers HITL if amount exceeds threshold."""
    order_id = int(order_id)
    if order_id == 0:
        return "请指定要退款的订单编号。"
    result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    order = result.scalar_one_or_none()
    if not order:
        return "订单不存在或不属于当前用户。"

    existing = await db.execute(select(Refund).where(Refund.order_id == order_id, Refund.status == "pending"))
    if existing.scalar_one_or_none():
        return "该订单已有待处理的退款申请。"

    refund = Refund(
        order_id=order_id,
        user_id=user_id,
        reason=reason,
        amount=order.total_amount,
        status="pending",
        review_status="pending" if order.total_amount > settings.refund_approval_threshold else "approved",
    )
    db.add(refund)
    await db.commit()
    await db.refresh(refund)

    if refund.review_status == "approved":
        order.status = "refunded"
        await db.commit()
        return json.dumps({"status": "approved", "refund_id": refund.id, "message": "退款已自动审批通过。"}, ensure_ascii=False)

    return json.dumps(
        {
            "status": "pending_review",
            "refund_id": refund.id,
            "message": f"退款金额 {order.total_amount} 元超过审批阈值，已提交管理员审批，请耐心等待。",
        },
        ensure_ascii=False,
    )
