import asyncio
from typing import Any

pending_reviews: list[dict[str, Any]] = []
admin_clients: list[Any] = []
user_clients: dict[int, Any] = {}


async def notify_admin_clients(message: dict):
    disconnected = []
    for client in admin_clients:
        try:
            await client.send_json(message)
        except Exception:
            disconnected.append(client)
    for c in disconnected:
        admin_clients.remove(c)


async def notify_user(conversation_id: int, message: dict):
    ws = user_clients.get(conversation_id)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            user_clients.pop(conversation_id, None)


def add_pending_review(review: dict):
    pending_reviews.append(review)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(notify_admin_clients({
            "type": "new_review",
            "review": review,
        }))
    except RuntimeError:
        pass
