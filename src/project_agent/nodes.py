"""Graph nodes: classify, extract, follow-up, CRUD, list, clarify."""

from __future__ import annotations

from project_agent import replies
from project_agent.models import Project
from project_agent.slots import extract_from_text, fill_remaining, merge_draft, missing_required
from project_agent.state import AgentState
from project_agent.storage import StorageError, add_project, load_projects

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


def _stub(node_name: str, **extra: object) -> dict:
    payload = {"last_node": node_name, "reply": f"[stub: {node_name}]"}
    payload.update(extra)
    return payload


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
    user_input = (state.get("user_input") or "").strip()
    merged = merge_draft(draft, extract_from_text(user_input))
    if state.get("intent") == "follow_up":
        merged = fill_remaining(merged, user_input)
    missing = missing_required(merged)
    return {
        "draft": merged,
        "missing_fields": missing,
        "last_node": "extract_slots",
    }


def ask_followup(state: AgentState) -> dict:
    missing = state.get("missing_fields") or []
    return {
        "last_node": "ask_followup",
        "dialog_state": "collecting",
        "reply": replies.followup(missing),
    }


def create_project(state: AgentState) -> dict:
    draft = state.get("draft") or {}
    try:
        project = Project.create(
            draft["project_name"],
            draft["customer"],
            start_date=draft.get("start_date"),
            location=draft.get("location"),
            status=draft.get("status"),
            notes=draft.get("notes"),
        )
        add_project(project)
    except (KeyError, ValueError):
        return {
            "last_node": "ask_followup",
            "dialog_state": "collecting",
            "reply": replies.followup(missing_required(draft)),
        }
    except StorageError:
        return {
            "last_node": "create_project",
            "dialog_state": "idle",
            "reply": replies.STORAGE_WRITE_ERROR,
        }
    return {
        "last_node": "create_project",
        "dialog_state": "idle",
        "draft": {},
        "missing_fields": [],
        "reply": replies.created(project.project_name, project.customer),
    }


def list_projects(state: AgentState) -> dict:
    try:
        projects = load_projects()
    except StorageError:
        return {"last_node": "list_projects", "reply": replies.STORAGE_READ_ERROR}
    return {"last_node": "list_projects", "reply": replies.listed(projects)}


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
    return {"last_node": "clarify_message", "reply": replies.UNKNOWN}


def exit_node(state: AgentState) -> dict:
    return {
        "last_node": "exit_node",
        "should_exit": True,
        "reply": replies.GOODBYE,
    }
