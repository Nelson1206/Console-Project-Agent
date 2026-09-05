"""LangGraph StateGraph compile and invoke."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from project_agent import nodes
from project_agent.state import AgentState

__all__ = [
    "AgentState",
    "build_graph",
    "compile_graph",
    "get_compiled_graph",
    "invoke",
    "route_after_classify",
    "route_after_extract",
    "route_after_resolve",
]


def route_after_classify(state: AgentState) -> str:
    if state.get("llm_error"):
        return "llm_error"
    intent = state.get("intent") or "unknown"
    if intent in {"create", "follow_up"}:
        return "extract_slots"
    if intent == "list":
        return "list_projects"
    if intent in {"get", "update", "delete"}:
        return "resolve_target"
    if intent == "disambiguation_choice":
        action = state.get("pending_action") or ""
        return {
            "get": "get_project",
            "update": "update_project",
            "delete": "delete_project",
        }.get(action, "clarify_message")
    if intent == "exit":
        return "exit_node"
    return "clarify_message"


def route_after_extract(state: AgentState) -> str:
    if state.get("llm_error"):
        return "llm_error"
    missing = state.get("missing_fields") or []
    return "ask_followup" if missing else "create_project"


def route_after_resolve(state: AgentState) -> str:
    selected_id = state.get("selected_id") or ""
    matches = state.get("pending_matches") or []
    action = state.get("pending_action") or state.get("intent") or ""

    if selected_id:
        if action == "update" and not state.get("updates"):
            return "ask_followup"
        return {
            "get": "get_project",
            "update": "update_project",
            "delete": "delete_project",
        }.get(action, "clarify_message")
    if len(matches) > 1:
        return "ask_disambiguation"
    if len(matches) == 1:
        return {
            "get": "get_project",
            "update": "update_project",
            "delete": "delete_project",
        }.get(action, "clarify_message")
    return "not_found"


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("classify", nodes.classify)
    builder.add_node("extract_slots", nodes.extract_slots)
    builder.add_node("ask_followup", nodes.ask_followup)
    builder.add_node("create_project", nodes.create_project)
    builder.add_node("list_projects", nodes.list_projects)
    builder.add_node("resolve_target", nodes.resolve_target)
    builder.add_node("ask_disambiguation", nodes.ask_disambiguation)
    builder.add_node("get_project", nodes.get_project)
    builder.add_node("update_project", nodes.update_project)
    builder.add_node("delete_project", nodes.delete_project)
    builder.add_node("not_found", nodes.not_found)
    builder.add_node("clarify_message", nodes.clarify_message)
    builder.add_node("llm_error", nodes.llm_error)
    builder.add_node("exit_node", nodes.exit_node)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify",
        route_after_classify,
        [
            "extract_slots",
            "list_projects",
            "resolve_target",
            "get_project",
            "update_project",
            "delete_project",
            "exit_node",
            "clarify_message",
            "llm_error",
        ],
    )
    builder.add_conditional_edges(
        "extract_slots",
        route_after_extract,
        ["create_project", "ask_followup", "llm_error"],
    )
    builder.add_conditional_edges(
        "resolve_target",
        route_after_resolve,
        [
            "get_project",
            "update_project",
            "delete_project",
            "ask_disambiguation",
            "ask_followup",
            "not_found",
            "clarify_message",
        ],
    )
    for terminal in (
        "ask_followup",
        "create_project",
        "list_projects",
        "ask_disambiguation",
        "get_project",
        "update_project",
        "delete_project",
        "not_found",
        "clarify_message",
        "llm_error",
        "exit_node",
    ):
        builder.add_edge(terminal, END)
    return builder


def compile_graph():
    return build_graph().compile()


_compiled = None


def get_compiled_graph():
    global _compiled
    if _compiled is None:
        _compiled = compile_graph()
    return _compiled


def invoke(state: AgentState) -> AgentState:
    return get_compiled_graph().invoke(state)
