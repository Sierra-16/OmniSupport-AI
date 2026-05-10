import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.middleware.auth import decode_token
from app.models.human_review import HumanReview
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.refund import Refund
from app.models.checkpoint import Checkpoint
from app.schemas.admin import ReviewAction
from app.ai.graph import get_graph
from app.services.review_queue import pending_reviews, admin_clients, user_clients, notify_user
from langgraph.types import Command

router = APIRouter(prefix="/api/admin", tags=["admin"])
ws_router = APIRouter()


@router.get("/reviews")
async def list_pending_reviews(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HumanReview).where(HumanReview.status == "pending").order_by(HumanReview.created_at.desc())
    )
    reviews = result.scalars().all()
    return [
        {
            "id": r.id,
            "action_type": r.action_type,
            "status": r.status,
            "created_at": str(r.created_at),
        }
        for r in reviews
    ]


@router.get("/reviews/{review_id}")
async def get_review_detail(review_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HumanReview).where(HumanReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        return {"error": "Review not found"}

    conversation_id = review.checkpoint_id
    messages = []
    if conversation_id:
        msg_result = await db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
        messages = [
            {"role": m.role, "content": m.content, "created_at": str(m.created_at)}
            for m in msg_result.scalars().all()
        ]

    return {
        "review": {
            "id": review.id,
            "action_type": review.action_type,
            "status": review.status,
        },
        "messages": messages,
    }


@router.post("/reviews/{review_id}/action")
async def handle_review_action(review_id: int, action: ReviewAction, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HumanReview).where(HumanReview.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        return {"error": "Review not found"}

    review.status = action.action
    if action.action in ("approved", "rejected"):
        review.reviewed_at = __import__("datetime").datetime.now()

    await db.commit()

    if review.action_type == "refund_approval":
        cp_result = await db.execute(select(Checkpoint).where(Checkpoint.id == review.checkpoint_id))
        checkpoint = cp_result.scalar_one_or_none()
        if checkpoint:
            cp_data = json.loads(checkpoint.checkpoint)
            refund_id = cp_data.get("refund_id")
            if refund_id:
                ref_result = await db.execute(select(Refund).where(Refund.id == refund_id))
                refund = ref_result.scalar_one_or_none()
                if refund:
                    refund.review_status = "approved" if action.action == "approved" else "rejected"
                    refund.reviewer_id = None
                    await db.commit()

    conversation_id = review.checkpoint_id
    final_response = ""
    try:
        graph = get_graph()
        config = {"configurable": {"thread_id": str(conversation_id)}}
        resume_cmd = Command(resume={
            "action": action.action,
            "message": action.message or "",
        })
        result = graph.invoke(resume_cmd, config)
        if result and "final_response" in result:
            final_response = result["final_response"]
    except Exception:
        pass

    response_text = final_response or action.message or ""
    if response_text:
        await notify_user(conversation_id, {
            "type": "final",
            "content": response_text,
        })
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
        )
        db.add(assistant_msg)
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if conv:
            conv.status = "closed"
        await db.commit()

    return {"status": "ok", "action": action.action}


@ws_router.websocket("/ws/admin")
async def admin_websocket(ws: WebSocket):
    await ws.accept()

    try:
        auth_msg = await ws.receive_text()
        auth_data = json.loads(auth_msg)
        token = auth_data.get("token", "")
        payload = decode_token(token)
        if payload["role"] != "admin":
            await ws.send_json({"type": "error", "content": "需要管理员权限"})
            await ws.close()
            return
    except Exception:
        await ws.send_json({"type": "error", "content": "认证失败"})
        await ws.close()
        return

    admin_clients.append(ws)

    try:
        await ws.send_json({
            "type": "pending_queue",
            "reviews": pending_reviews,
        })

        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "review_action":
                review_id = msg.get("review_id")
                action_name = msg.get("action")
                admin_message = msg.get("message", "")

                async for db in get_db():
                    await handle_review_action(
                        review_id,
                        ReviewAction(review_id=review_id, action=action_name, message=admin_message),
                        db,
                    )
                    break

                pending_reviews[:] = [r for r in pending_reviews if r.get("id") != review_id]

                for client in admin_clients:
                    try:
                        await client.send_json({
                            "type": "pending_queue",
                            "reviews": pending_reviews,
                        })
                    except Exception:
                        pass

    except WebSocketDisconnect:
        admin_clients.remove(ws)
