"""Shared LangGraph state."""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    dialog_state: str
    intent: str
    draft: dict
    missing_fields: list[str]
    updates: dict
    pending_action: str
    pending_matches: list[dict]
    selected_id: str
    reply: str
    should_exit: bool
    last_node: str
