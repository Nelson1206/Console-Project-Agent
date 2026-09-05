"""Graph nodes: classify, extract, follow-up, CRUD, list, clarify."""

from __future__ import annotations

from project_agent import replies
from project_agent.llm import LLMError, classify_with_llm, extract_with_llm
from project_agent.models import OPTIONAL_FIELDS, Project
from project_agent.slots import (
    extract_from_text,
    extract_target_name,
    extract_updates,
    fill_remaining,
    merge_draft,
    missing_required,
    user_omitted_required,
)
from project_agent.state import AgentState
from project_agent.storage import StorageError, add_project, get_by_id, get_by_name, load_projects
from project_agent.storage import delete_project as remove_project
from project_agent.storage import update_project as save_project_updates

_EXACT_COMMANDS = {
    "quit": "exit",
    "exit": "exit",
    "list projects": "list",
}
_NEW_INTENTS = {"create", "list", "get", "update", "delete", "exit", "unknown"}


def _keyword_intent(text: str) -> str | None:
    return _EXACT_COMMANDS.get(text.casefold().strip())


def classify_intent(user_input: str, dialog_state: str = "idle") -> str:
    text = user_input.strip()
    if dialog_state == "disambiguating" and text.isdigit():
        return "disambiguation_choice"
    keyword = _keyword_intent(text)
    if keyword is not None:
        return keyword
    if dialog_state == "collecting":
        return "follow_up"
    return classify_with_llm(text)


def classify(state: AgentState) -> dict:
    dialog_state = state.get("dialog_state") or "idle"
    user_input = state.get("user_input") or ""
    try:
        intent = classify_intent(user_input, dialog_state)
    except LLMError as exc:
        return {
            "intent": "unknown",
            "llm_error": True,
            "last_node": "classify",
            "reply": exc.user_message,
        }
    result: dict = {"intent": intent, "llm_error": False, "last_node": "classify"}
    if intent == "disambiguation_choice":
        matches = state.get("pending_matches") or []
        try:
            index = int(user_input.strip()) - 1
        except ValueError:
            index = -1
        result["pending_action"] = state.get("pending_action") or ""
        result["pending_matches"] = matches
        result["updates"] = state.get("updates") or {}
        result["lookup_name"] = state.get("lookup_name") or ""
        if 0 <= index < len(matches):
            result["selected_id"] = matches[index]["id"]
        else:
            result["selected_id"] = ""
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
    extracted = extract_from_text(user_input)
    follow_up = state.get("intent") == "follow_up"
    if follow_up:
        extracted = _llm_slots_for_follow_up(draft, extracted, user_input)
    else:
        try:
            llm_slots = extract_with_llm(user_input)
            for field in ("project_name", "customer"):
                if field not in extracted and user_omitted_required(user_input, field):
                    llm_slots.pop(field, None)
            extracted = merge_draft(llm_slots, extracted)
        except LLMError as exc:
            return {
                "draft": draft,
                "llm_error": True,
                "last_node": "extract_slots",
                "reply": exc.user_message,
            }
    merged = merge_draft(draft, extracted)
    if follow_up:
        merged = fill_remaining(merged, user_input)
    missing = missing_required(merged)
    return {
        "draft": merged,
        "missing_fields": missing,
        "llm_error": False,
        "last_node": "extract_slots",
    }


def _llm_slots_for_follow_up(
    draft: dict,
    extracted: dict[str, str],
    user_input: str,
) -> dict[str, str]:
    """Fill still-missing fields from the LLM; never overwrite a filled required slot."""
    preview = merge_draft(draft, extracted)
    still_missing = missing_required(preview)
    if not still_missing:
        return extracted
    try:
        llm_slots = extract_with_llm(user_input)
    except LLMError:
        return extracted
    allowed = set(still_missing) | set(OPTIONAL_FIELDS)
    return merge_draft({key: value for key, value in llm_slots.items() if key in allowed}, extracted)


def ask_followup(state: AgentState) -> dict:
    if state.get("pending_action") == "update":
        return {
            "last_node": "ask_followup",
            "dialog_state": "collecting",
            "pending_action": "update",
            "selected_id": state.get("selected_id") or "",
            "pending_matches": state.get("pending_matches") or [],
            "updates": state.get("updates") or {},
            "lookup_name": state.get("lookup_name") or "",
            "reply": replies.UPDATE_WHICH_FIELDS,
        }
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
    extras = {
        field: getattr(project, field)
        for field in OPTIONAL_FIELDS
        if getattr(project, field)
    }
    return {
        "last_node": "create_project",
        "dialog_state": "idle",
        "draft": {},
        "missing_fields": [],
        "reply": replies.created(project.project_name, project.customer, extras),
    }


def list_projects(state: AgentState) -> dict:
    try:
        projects = load_projects()
    except StorageError:
        return {"last_node": "list_projects", "reply": replies.STORAGE_READ_ERROR}
    return {"last_node": "list_projects", "reply": replies.listed(projects)}


def _match_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "project_name": project.project_name,
        "customer": project.customer,
    }


def _clear_target() -> dict:
    return {
        "dialog_state": "idle",
        "pending_action": "",
        "pending_matches": [],
        "selected_id": "",
        "updates": {},
        "lookup_name": "",
    }


def resolve_target(state: AgentState) -> dict:
    intent = state.get("intent") or ""
    action = state.get("pending_action") or intent
    user_input = state.get("user_input") or ""
    selected_id = state.get("selected_id") or ""
    updates = dict(state.get("updates") or {})

    if action == "update":
        updates.update(extract_updates(user_input))
        if selected_id and intent == "follow_up":
            return {
                "last_node": "resolve_target",
                "pending_action": "update",
                "selected_id": selected_id,
                "pending_matches": state.get("pending_matches") or [],
                "updates": updates,
                "lookup_name": state.get("lookup_name") or "",
            }

    name = extract_target_name(user_input)
    if not name:
        try:
            name = extract_with_llm(user_input).get("project_name")
        except LLMError as exc:
            return {
                "last_node": "resolve_target",
                "llm_error": True,
                "reply": exc.user_message,
            }

    try:
        matches = get_by_name(name) if name else []
    except StorageError:
        return {
            "last_node": "resolve_target",
            "reply": replies.STORAGE_READ_ERROR,
            "llm_error": True,
        }

    if name and updates.get("project_name", "").casefold() == name.casefold():
        updates.pop("project_name", None)

    selected = matches[0].id if len(matches) == 1 else ""
    return {
        "last_node": "resolve_target",
        "pending_action": action if action in {"get", "update", "delete"} else intent,
        "pending_matches": [_match_dict(item) for item in matches],
        "selected_id": selected,
        "lookup_name": name or "",
        "updates": updates,
        "llm_error": False,
    }


def ask_disambiguation(state: AgentState) -> dict:
    name = state.get("lookup_name") or "that project"
    return {
        "last_node": "ask_disambiguation",
        "dialog_state": "disambiguating",
        "pending_action": state.get("pending_action") or "",
        "pending_matches": state.get("pending_matches") or [],
        "selected_id": "",
        "updates": state.get("updates") or {},
        "lookup_name": name,
        "reply": replies.disambiguation(name, state.get("pending_matches") or []),
    }


def get_project(state: AgentState) -> dict:
    try:
        project = get_by_id(state.get("selected_id") or "")
        if project is None:
            matches = state.get("pending_matches") or []
            if len(matches) == 1:
                project = get_by_id(matches[0]["id"])
    except StorageError:
        return {
            "last_node": "get_project",
            **_clear_target(),
            "reply": replies.STORAGE_READ_ERROR,
        }
    if project is None:
        return {
            "last_node": "not_found",
            **_clear_target(),
            "reply": replies.not_found(state.get("lookup_name") or "that project"),
        }
    return {
        "last_node": "get_project",
        **_clear_target(),
        "reply": replies.got(project),
    }


def update_project(state: AgentState) -> dict:
    project_id = state.get("selected_id") or ""
    if not project_id:
        matches = state.get("pending_matches") or []
        if len(matches) == 1:
            project_id = matches[0]["id"]
    changes = dict(state.get("updates") or {})
    if not project_id:
        return {
            "last_node": "not_found",
            **_clear_target(),
            "reply": replies.not_found(state.get("lookup_name") or "that project"),
        }
    if not changes:
        return ask_followup({**state, "pending_action": "update", "selected_id": project_id})
    try:
        project = save_project_updates(project_id, changes)
    except (StorageError, ValueError):
        return {
            "last_node": "update_project",
            **_clear_target(),
            "reply": replies.STORAGE_WRITE_ERROR,
        }
    return {
        "last_node": "update_project",
        **_clear_target(),
        "reply": replies.updated(project, changes),
    }


def delete_project(state: AgentState) -> dict:
    project_id = state.get("selected_id") or ""
    if not project_id:
        matches = state.get("pending_matches") or []
        if len(matches) == 1:
            project_id = matches[0]["id"]
    if not project_id:
        return {
            "last_node": "not_found",
            **_clear_target(),
            "reply": replies.not_found(state.get("lookup_name") or "that project"),
        }
    try:
        project = remove_project(project_id)
    except StorageError:
        return {
            "last_node": "delete_project",
            **_clear_target(),
            "reply": replies.STORAGE_WRITE_ERROR,
        }
    return {
        "last_node": "delete_project",
        **_clear_target(),
        "reply": replies.deleted(project),
    }


def not_found(state: AgentState) -> dict:
    return {
        "last_node": "not_found",
        **_clear_target(),
        "reply": replies.not_found(state.get("lookup_name") or "that project"),
    }


def clarify_message(state: AgentState) -> dict:
    return {"last_node": "clarify_message", "reply": replies.UNKNOWN}


def llm_error(state: AgentState) -> dict:
    return {"last_node": "llm_error"}


def exit_node(state: AgentState) -> dict:
    return {
        "last_node": "exit_node",
        "should_exit": True,
        "reply": replies.GOODBYE,
    }
