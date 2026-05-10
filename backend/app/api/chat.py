import json
import asyncio
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import decode_token
from app.models.conversation import Conversation
from app.models.message import Message
from app.ai.graph import get_graph
from app.ai.memory import MemoryEngine
from app.services.review_queue import user_clients

router = APIRouter()


async def stream_graph(user_id: int, conversation_id: int, message: str, db, memory):
    token_queue: asyncio.Queue = asyncio.Queue()
    graph = get_graph()
    config = {
        "configurable": {
            "thread_id": str(conversation_id),
            "db_session": db,
            "memory": memory,
            "token_queue": token_queue,
        }
    }

    initial_state = {
        "messages": [],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "user_message": message,
        "intent": "",
        "agents_to_call": [],
        "agent_results": {},
        "requires_human": False,
        "human_review_id": None,
        "human_action": None,
        "human_message": None,
        "final_response": "",
        "node_status": {},
    }

    final_state_ref = {}
    graph_error = None

    async def _run_graph():
        nonlocal graph_error
        try:
            async for event in graph.astream(initial_state, config, stream_mode="values"):
                await token_queue.put(("graph_event", event))
            st = graph.get_state(config)
            if st and st.values:
                final_state_ref["state"] = st.values
        except Exception as e:
            traceback.print_exc()
            graph_error = str(e)
        finally:
            await token_queue.put(("graph_done", None))

    task = asyncio.create_task(_run_graph())

    try:
        while True:
            kind, payload = await token_queue.get()

            if kind == "graph_done":
                break

            if kind == "graph_event":
                yield json.dumps(payload, ensure_ascii=False, default=str)

            elif kind == "node_status":
                yield json.dumps({"type": "node_status", "content": payload}, ensure_ascii=False)

            elif kind == "token":
                yield json.dumps({"type": "token", "content": payload}, ensure_ascii=False)

        await task

        if graph_error:
            yield json.dumps({"type": "error", "content": graph_error}, ensure_ascii=False)
            return

        final_state = final_state_ref.get("state", {})
        final_response = final_state.get("final_response", "")
        requires_human = final_state.get("requires_human", False)

        if final_response:
            yield json.dumps({"type": "final", "content": final_response}, ensure_ascii=False)
            msg = Message(conversation_id=conversation_id, role="user", content=message)
            db.add(msg)
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_response,
            )
            db.add(assistant_msg)
            await db.commit()

        elif requires_human:
            human_msg = "您的请求已提交，正在为您转接人工坐席，请稍候..."
            yield json.dumps({"type": "final", "content": human_msg}, ensure_ascii=False)
            msg = Message(conversation_id=conversation_id, role="user", content=message)
            db.add(msg)
            system_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=human_msg,
            )
            db.add(system_msg)
            await db.commit()

    except Exception as e:
        traceback.print_exc()
        yield json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)


@router.websocket("/ws/chat")
async def chat_websocket(ws: WebSocket):
    await ws.accept()

    try:
        auth_msg = await ws.receive_text()
        auth_data = json.loads(auth_msg)
        token = auth_data.get("token", "")
        payload = decode_token(token)
        user_id = int(payload["sub"])
        role = payload["role"]

        if role != "user":
            await ws.send_json({"type": "error", "content": "管理员请使用管理后台"})
            await ws.close()
            return

    except Exception:
        await ws.send_json({"type": "error", "content": "认证失败"})
        await ws.close()
        return

    async for db in get_db():
        conv = Conversation(user_id=user_id, status="active", channel="web")
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conversation_id = conv.id
        break

    user_clients[conversation_id] = ws

    import redis.asyncio as aioredis
    from app.config import settings as app_settings

    try:
        redis_client = aioredis.from_url(app_settings.redis_url, decode_responses=True)
    except Exception:
        redis_client = None

    async for db in get_db():
        memory = MemoryEngine(db, redis_client)

        try:
            while True:
                data = await ws.receive_text()
                msg_data = json.loads(data)
                user_message = msg_data.get("message", "")

                if not user_message.strip():
                    continue

                async for event_str in stream_graph(user_id, conversation_id, user_message, db, memory):
                    await ws.send_text(event_str)

        except WebSocketDisconnect:
            conv_status = Conversation.__table__.update().where(
                Conversation.id == conversation_id
            ).values(status="closed")
            await db.execute(conv_status)
            await db.commit()
        finally:
            user_clients.pop(conversation_id, None)
            if redis_client:
                await redis_client.close()
