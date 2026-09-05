"""Graph nodes: classify, extract, follow-up, CRUD, list, clarify.

Phase 3 uses stub logic so the graph can compile and route. Later phases
replace stubs with real LLM, storage, and fixed English copy.
"""

from __future__ import annotations

from project_agent.state import AgentState

_INTENT_KEYWORDS = (
    ("create", "create"),
    ("list", "list"),
    ("show", "get"),
    ("get", "get"),
    ("update", "update"),
    ("delete", "delete"),
    ("remove", "delete"),
    ("quit", "exit"),
    ("exit", "exit"),
)
_NEW_INTENTS = {"create", "list", "get", "update", "delete", "exit", "unknown"}
_REQUIRED_SLOTS = ("project_name", "customer")


def _stub(node_name: str, **extra: object) -> dict:
    payload = {"last_node": node_name, "reply": f"[stub: {node_name}]"}
    payload.update(extra)
    return payload


def _first_word(text: str) -> str:
    parts = text.strip().split()
    return parts[0].casefold() if parts else ""


def _keyword_intent(text: str) -> str | None:
    lowered = text.casefold()
    for keyword, intent in _INTENT_KEYWORDS:
        if lowered == keyword or lowered.startswith(f"{keyword} "):
            return intent
        if f" {keyword} " in f" {lowered} ":
            return intent
    return None


def classify_intent(user_input: str, dialog_state: str = "idle") -> str:
    text = user_input.strip()
    if dialog_state == "disambiguating" and text.isdigit():
        return "disambiguation_choice"
    keyword = _keyword_intent(text)
    if dialog_state == "collecting" and keyword is None:
        return "follow_up"
    return keyword or "unknown"


def classify(state: AgentState) -> dict:
    dialog_state = state.get("dialog_state") or "idle"
    user_input = state.get("user_input") or ""
    intent = classify_intent(user_input, dialog_state)
    result: dict = {"intent": intent, "last_node": "classify"}
    if dialog_state in {"collecting", "disambiguating"} and intent in _NEW_INTENTS:
        result.update(
            {
                "dialog_state": "idle",
                "draft": {},
                "updates": {},
                "pending_action": "",
                "pending_matches": [],
                "selected_id": "",
                "missing_fields": [],
            }
        )
    return result


def extract_slots(state: AgentState) -> dict:
    draft = dict(state.get("draft") or {})
    missing = [name for name in _REQUIRED_SLOTS if not str(draft.get(name) or "").strip()]
    return {
        "draft": draft,
        "missing_fields": missing,
        "last_node": "extract_slots",
    }


def ask_followup(state: AgentState) -> dict:
    return _stub("ask_followup", dialog_state="collecting")


def create_project(state: AgentState) -> dict:
    return _stub("create_project", dialog_state="idle", draft={}, missing_fields=[])


def list_projects(state: AgentState) -> dict:
    return _stub("list_projects")


def resolve_target(state: AgentState) -> dict:
    result = _stub("resolve_target")
    if "pending_action" not in state or not state.get("pending_action"):
        result["pending_action"] = state.get("intent") or ""
    if "pending_matches" not in state:
        result["pending_matches"] = []
    return result


def ask_disambiguation(state: AgentState) -> dict:
    return _stub("ask_disambiguation", dialog_state="disambiguating")


def get_project(state: AgentState) -> dict:
    return _stub("get_project", dialog_state="idle")


def update_project(state: AgentState) -> dict:
    return _stub("update_project", dialog_state="idle")


def delete_project(state: AgentState) -> dict:
    return _stub("delete_project", dialog_state="idle")


def not_found(state: AgentState) -> dict:
    return _stub("not_found", dialog_state="idle")


def clarify_message(state: AgentState) -> dict:
    return _stub("clarify_message")


def exit_node(state: AgentState) -> dict:
    return {
        "last_node": "exit_node",
        "should_exit": True,
        "reply": "Goodbye.",
    }
