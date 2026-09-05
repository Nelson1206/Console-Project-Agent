"""Rule-based slot extraction used until the LLM extract node is wired."""

from __future__ import annotations

import re

_REQUIRED = ("project_name", "customer")
_SKIP_NAMES = {"a", "an", "the", "project"}

_CALLED = re.compile(
    r"\bcalled\s+(?P<name>.+?)(?:\s+for(?:\s+customer)?\s+(?P<customer>.+))?$",
    re.IGNORECASE,
)
_PROJECT_FOR = re.compile(
    r"\bproject(?:\s+called)?\s+(?P<name>.+?)\s+for(?:\s+customer)?\s+(?P<customer>.+)$",
    re.IGNORECASE,
)
_FOR_CUSTOMER = re.compile(r"\bfor\s+customer\s+(?P<customer>.+)$", re.IGNORECASE)
_PROJECT_NAME = re.compile(r"\bproject(?:\s+called)?\s+(?P<name>.+)$", re.IGNORECASE)
_BARE_PAIR = re.compile(
    r"^(?P<name>.+?)\s+for(?:\s+customer)?\s+(?P<customer>.+)$",
    re.IGNORECASE,
)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().strip("\"'")
    return text or None


def extract_from_text(text: str) -> dict[str, str]:
    raw = text.strip()
    if not raw:
        return {}

    match = _CALLED.search(raw)
    if match:
        return _payload(match.group("name"), match.group("customer"))

    match = _PROJECT_FOR.search(raw)
    if match:
        return _payload(match.group("name"), match.group("customer"))

    match = _FOR_CUSTOMER.search(raw)
    if match:
        return _payload(None, match.group("customer"))

    match = _PROJECT_NAME.search(raw)
    if match:
        return _payload(match.group("name"), None)

    match = _BARE_PAIR.fullmatch(raw)
    if match:
        return _payload(match.group("name"), match.group("customer"))

    return {}


def merge_draft(draft: dict, extracted: dict[str, str]) -> dict:
    merged = dict(draft)
    for key, value in extracted.items():
        if value:
            merged[key] = value
    return merged


def missing_required(draft: dict) -> list[str]:
    return [name for name in _REQUIRED if not str(draft.get(name) or "").strip()]


def fill_remaining(draft: dict, user_input: str) -> dict:
    """If exactly one required field is missing, treat the whole reply as that value."""
    missing = missing_required(draft)
    if len(missing) != 1:
        return draft
    value = user_input.strip().strip("\"'")
    if not value:
        return draft
    updated = dict(draft)
    updated[missing[0]] = value
    return updated


def _payload(name: str | None, customer: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    cleaned_name = _clean(name)
    if cleaned_name and cleaned_name.casefold() not in _SKIP_NAMES:
        result["project_name"] = cleaned_name
    cleaned_customer = _clean(customer)
    if cleaned_customer:
        result["customer"] = cleaned_customer
    return result
