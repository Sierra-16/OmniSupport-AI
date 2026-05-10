import json
import redis.asyncio as aioredis

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import settings
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message


class MemoryEngine:
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis | None = None):
        self.db = db
        self.redis = redis_client

    async def get_short_term(self, conversation_id: int) -> list[dict]:
        if not self.redis:
            return []
        key = f"chat:{conversation_id}"
        data = await self.redis.lrange(key, 0, -1)
        return [json.loads(msg) for msg in data]

    async def append_short_term(self, conversation_id: int, role: str, content: str):
        if not self.redis:
            return
        key = f"chat:{conversation_id}"
        entry = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        await self.redis.rpush(key, entry)
        await self.redis.ltrim(key, -20, -1)
        await self.redis.expire(key, 1800)

    async def get_long_term(self, user_id: int) -> dict:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {}

        conv_result = await self.db.execute(
            select(Conversation.summary)
            .where(Conversation.user_id == user_id, Conversation.summary.isnot(None))
            .order_by(Conversation.created_at.desc())
            .limit(5)
        )
        summaries = [row.summary for row in conv_result.fetchall()]

        return {
            "name": user.name,
            "tags": json.loads(user.tags) if user.tags else [],
            "recent_summaries": summaries,
        }

    async def get_historical_context(self, user_id: int) -> str:
        long_term = await self.get_long_term(user_id)
        if not long_term:
            return ""

        parts = []
        name = long_term.get("name", "")
        tags = long_term.get("tags", [])
        summaries = long_term.get("recent_summaries", [])

        if name:
            parts.append(f"当前客户: {name}")
        if tags:
            parts.append(f"客户标签: {', '.join(tags)}")
        if summaries:
            parts.append("历史对话记录:")
            for i, s in enumerate(summaries, 1):
                parts.append(f"  {i}. {s}")

        return "\n".join(parts) if parts else ""

    async def save_conversation_summary(self, conversation_id: int, summary: str):
        await self.db.execute(
            update(Conversation).where(Conversation.id == conversation_id).values(summary=summary)
        )
        await self.db.commit()

    async def generate_and_save_summary(self, conversation_id: int, user_message: str, assistant_response: str):
        """Generate a concise summary of this exchange and persist it."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage
        try:
            llm = ChatOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                temperature=0,
            )
            prompt = f"""将以下客服对话压缩成一句简短摘要（20字以内），只返回摘要文本。

用户: {user_message}
客服: {assistant_response[:200]}

摘要:"""
            resp = await llm.ainvoke([SystemMessage(content=prompt)])
            summary = resp.content.strip()[:200]
        except Exception:
            summary = f"用户询问: {user_message[:50]}"

        await self.save_conversation_summary(conversation_id, summary)
        return summary

    async def _summarize(self, messages: list[dict]) -> str:
        user_msgs = [m["content"] for m in messages if m["role"] == "user"]
        return f"用户之前询问了: {'; '.join(user_msgs[-3:])}"
