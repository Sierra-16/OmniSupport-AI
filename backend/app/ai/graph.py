import json
from typing import Any, TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langgraph.types import RunnableConfig

from app.ai.agents.supervisor import classify_intent, route_by_intent
from app.ai.agents.presales import run_presales
from app.ai.agents.aftersales import run_aftersales
from app.ai.agents.complaint import run_complaint
from app.ai.memory import MemoryEngine
from app.models.human_review import HumanReview
from app.services.review_queue import add_pending_review


class AgentState(TypedDict):
    messages: Annotated[list[dict], add]
    user_id: int
    conversation_id: int
    user_message: str
    intent: str
    agents_to_call: list[str]
    agent_results: dict[str, Any]
    requires_human: bool
    human_review_id: int | None
    human_action: str | None
    human_message: str | None
    final_response: str
    node_status: dict[str, str]


def _get_db(state: AgentState, config: RunnableConfig):
    return config.get("configurable", {}).get("db_session")


def _get_memory(state: AgentState, config: RunnableConfig):
    return config.get("configurable", {}).get("memory")


async def _emit_node_status(config: RunnableConfig, node: str, status: str, message: str = ""):
    token_queue = config.get("configurable", {}).get("token_queue")
    if token_queue:
        payload = json.dumps({"node": node, "status": status, "message": message}, ensure_ascii=False)
        await token_queue.put(("node_status", payload))


async def _emit_token(config: RunnableConfig, token: str):
    token_queue = config.get("configurable", {}).get("token_queue")
    if token_queue:
        await token_queue.put(("token", token))


def _make_token_callback(config: RunnableConfig):
    async def cb(token: str):
        await _emit_token(config, token)
    return cb

async def supervisor_node(state: AgentState, config: RunnableConfig) -> dict:
    await _emit_node_status(config, "supervisor", "running", "正在分析意图...")

    intent_info = await classify_intent(state["user_message"])
    agents = route_by_intent(intent_info["intent"])

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "supervisor", "status": "completed", "intent": intent_info["intent"]}),
    })

    await _emit_node_status(config, "supervisor", "completed", f"意图: {intent_info['intent']}")

    return {
        "intent": intent_info["intent"],
        "agents_to_call": agents,
        "node_status": {"supervisor": f"completed: {intent_info['intent']}"},
    }


async def presales_node(state: AgentState, config: RunnableConfig) -> dict:
    await _emit_node_status(config, "presales", "running", "售前 Agent 处理中...")

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "presales", "status": "running", "message": "售前 Agent 处理中..."}),
    })

    async def stream_cb(agent: str, status: str, message: str):
        state["messages"].append({
            "role": "node_status",
            "content": json.dumps({"node": agent, "status": status, "message": message}),
        })
        await _emit_node_status(config, agent, status, message)

    token_cb = _make_token_callback(config)

    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in state.get("messages", [])
        if m["role"] in ("user", "assistant")
    ]

    memory = _get_memory(state, config)
    historical_context = await memory.get_historical_context(state["user_id"]) if memory else ""

    db = _get_db(state, config)
    response = await run_presales(
        db=db,
        user_id=state["user_id"],
        conversation_id=state["conversation_id"],
        user_message=state["user_message"],
        chat_history=chat_history,
        historical_context=historical_context,
        stream_callback=stream_cb,
        token_callback=token_cb,
    )

    state["agent_results"]["presales"] = response

    await _emit_node_status(config, "presales", "completed")

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "presales", "status": "completed"}),
    })

    return {
        "agent_results": state["agent_results"],
        "node_status": {"presales": "completed"},
        "requires_human": False,
    }


async def aftersales_node(state: AgentState, config: RunnableConfig) -> dict:
    await _emit_node_status(config, "aftersales", "running", "售后 Agent 处理中...")

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "aftersales", "status": "running", "message": "售后 Agent 处理中..."}),
    })

    async def stream_cb(agent: str, status: str, message: str):
        state["messages"].append({
            "role": "node_status",
            "content": json.dumps({"node": agent, "status": status, "message": message}),
        })
        await _emit_node_status(config, agent, status, message)

    token_cb = _make_token_callback(config)

    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in state.get("messages", [])
        if m["role"] in ("user", "assistant")
    ]

    memory = _get_memory(state, config)
    historical_context = await memory.get_historical_context(state["user_id"]) if memory else ""

    db = _get_db(state, config)
    result = await run_aftersales(
        db=db,
        user_id=state["user_id"],
        conversation_id=state["conversation_id"],
        user_message=state["user_message"],
        chat_history=chat_history,
        historical_context=historical_context,
        stream_callback=stream_cb,
        token_callback=token_cb,
    )

    state["agent_results"]["aftersales"] = result["response"]

    await _emit_node_status(config, "aftersales", "completed")

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "aftersales", "status": "completed"}),
    })

    return {
        "agent_results": state["agent_results"],
        "node_status": {"aftersales": "completed"},
        "requires_human": result.get("requires_human", False),
        "human_review_id": result.get("refund_id"),
    }


async def complaint_node(state: AgentState, config: RunnableConfig) -> dict:
    await _emit_node_status(config, "complaint", "running", "投诉 Agent 处理中...")

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "complaint", "status": "running", "message": "投诉 Agent 处理中..."}),
    })

    async def stream_cb(agent: str, status: str, message: str):
        state["messages"].append({
            "role": "node_status",
            "content": json.dumps({"node": agent, "status": status, "message": message}),
        })
        await _emit_node_status(config, agent, status, message)

    token_cb = _make_token_callback(config)

    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in state.get("messages", [])
        if m["role"] in ("user", "assistant")
    ]

    memory = _get_memory(state, config)
    historical_context = await memory.get_historical_context(state["user_id"]) if memory else ""

    db = _get_db(state, config)
    result = await run_complaint(
        db=db,
        user_id=state["user_id"],
        conversation_id=state["conversation_id"],
        user_message=state["user_message"],
        chat_history=chat_history,
        historical_context=historical_context,
        stream_callback=stream_cb,
        token_callback=token_cb,
    )

    state["agent_results"]["complaint"] = result["response"]

    await _emit_node_status(config, "complaint", "completed")

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "complaint", "status": "completed"}),
    })

    return {
        "agent_results": state["agent_results"],
        "node_status": {"complaint": "completed"},
        "requires_human": result.get("requires_human", False),
    }


async def human_review_node(state: AgentState, config: RunnableConfig) -> dict:
    await _emit_node_status(config, "human_review", "running", "等待人工审核...")

    db = _get_db(state, config)

    intent = state.get("intent", "")
    if intent == "complaint":
        action_type = "takeover"
    else:
        action_type = "refund_approval"

    review = HumanReview(
        checkpoint_id=state["conversation_id"],
        action_type=action_type,
        status="pending",
    )
    if db:
        db.add(review)
        await db.commit()
        await db.refresh(review)

    review_info = {
        "id": review.id if db else 0,
        "conversation_id": state["conversation_id"],
        "user_id": state["user_id"],
        "user_message": state["user_message"],
        "agent_results": state.get("agent_results", {}),
        "intent": intent,
        "action_type": action_type,
        "requires_human": state.get("requires_human", False),
    }
    add_pending_review(review_info)

    decision = interrupt(review_info)

    state["human_action"] = decision.get("action", "close")
    state["human_message"] = decision.get("message", "")

    await _emit_node_status(config, "human_review", "completed", f"人工操作: {decision.get('action', 'close')}")

    return {
        "human_action": decision.get("action", "close"),
        "human_message": decision.get("message", ""),
        "human_review_id": review.id if db else 0,
    }


async def finalize_node(state: AgentState, config: RunnableConfig) -> dict:
    agent_results = state.get("agent_results", {})

    parts = []
    for agent_name in state.get("agents_to_call", []):
        if agent_name in agent_results:
            parts.append(agent_results[agent_name])

    if state.get("human_action") == "takeover" and state.get("human_message"):
        final = state["human_message"]
    elif state.get("human_action") == "reject":
        final = "您提交的申请已被管理员驳回。如有疑问，请联系人工客服。"
    elif parts:
        final = "\n\n".join(parts)
    else:
        final = "抱歉，我暂时无法处理您的请求，正在为您转接人工坐席..."

    memory = _get_memory(state, config)
    if memory:
        await memory.append_short_term(state["conversation_id"], "user", state["user_message"])
        await memory.append_short_term(state["conversation_id"], "assistant", final)
        await memory.generate_and_save_summary(
            state["conversation_id"], state["user_message"], final
        )

    await _emit_node_status(config, "finalize", "completed")

    state["messages"].append({
        "role": "node_status",
        "content": json.dumps({"node": "finalize", "status": "completed"}),
    })

    return {"final_response": final}


def route_to_first_agent(state: AgentState) -> str:
    agents = state.get("agents_to_call", ["presales"])
    return agents[0]


def route_after_agent(state: AgentState) -> str:
    if state.get("requires_human", False):
        return "human_review"

    agents = state.get("agents_to_call", [])
    agent_results = state.get("agent_results", {})
    remaining = [a for a in agents if a not in agent_results]

    if remaining:
        return remaining[0]

    return "finalize"


def route_after_human(state: AgentState) -> str:
    return "finalize"


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("presales", presales_node)
    workflow.add_node("aftersales", aftersales_node)
    workflow.add_node("complaint", complaint_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges("supervisor", route_to_first_agent, {
        "presales": "presales",
        "aftersales": "aftersales",
        "complaint": "complaint",
    })

    workflow.add_conditional_edges("presales", route_after_agent, {
        "aftersales": "aftersales",
        "complaint": "complaint",
        "human_review": "human_review",
        "finalize": "finalize",
    })
    workflow.add_conditional_edges("aftersales", route_after_agent, {
        "presales": "presales",
        "complaint": "complaint",
        "human_review": "human_review",
        "finalize": "finalize",
    })
    workflow.add_conditional_edges("complaint", route_after_agent, {
        "presales": "presales",
        "aftersales": "aftersales",
        "human_review": "human_review",
        "finalize": "finalize",
    })

    workflow.add_edge("human_review", "finalize")

    workflow.add_edge("finalize", END)

    return workflow


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile(checkpointer=MemorySaver())
    return _compiled_graph
