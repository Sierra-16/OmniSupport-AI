from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.middleware.auth import decode_token, require_role
from app.models.conversation import Conversation
from app.models.message import Message
from fastapi import Header

router = APIRouter(prefix="/api", tags=["history"])


async def get_user_id(authorization: str = Header(...)) -> int:
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    return int(payload["sub"])


@router.get("/conversations")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    user_id = await get_user_id(authorization)
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.created_at))
        .limit(50)
    )
    conversations = result.scalars().all()
    return [
        {
            "id": c.id,
            "status": c.status,
            "channel": c.channel,
            "summary": c.summary,
            "created_at": str(c.created_at),
        }
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    user_id = await get_user_id(authorization)

    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    if not conv_result.scalar_one_or_none():
        return {"error": "Conversation not found", "messages": []}

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": str(m.created_at),
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    user_id = await get_user_id(authorization)

    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        return {"error": "Conversation not found"}

    from sqlalchemy import delete as sa_delete
    await db.execute(sa_delete(Message).where(Message.conversation_id == conversation_id))
    await db.delete(conversation)
    await db.commit()
    return {"ok": True}
