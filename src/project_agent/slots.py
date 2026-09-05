"""Rule-based slot, target, and update extraction."""

from __future__ import annotations

import re

_REQUIRED = ("project_name", "customer")
_SKIP_NAMES = {"a", "an", "the", "project"}
_FIELD_LABELS = {
    "project name": "project_name",
    "project_name": "project_name",
    "name": "project_name",
    "customer": "customer",
    "start date": "start_date",
    "start_date": "start_date",
    "location": "location",
    "status": "status",
    "notes": "notes",
    "note": "notes",
}

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
_STATUS = re.compile(r"\bwith\s+status\s+(?P<status>.+?)(?=\s+in\b|\s+start|\s+notes?\b|$)", re.I)
_LOCATION = re.compile(r"\bin\s+(?P<location>.+?)(?=\s+with\s+status\b|\s+start|\s+notes?\b|$)", re.I)
_START = re.compile(
    r"\b(?:start(?:ing)?(?:\s+date)?|on)\s+(?P<start_date>\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    re.I,
)
_NOTES = re.compile(r"\bnotes?\s*[:=]\s*(?P<notes>.+)$", re.I)
_TARGET = re.compile(
    r"\b(?:show|get|update|change|delete|remove)(?:\s+project)?\s+(?P<name>.+?)"
    r"(?=\s+(?:customer|status|location|notes?|start\s*date|project\s*name|set|to)\b|$)",
    re.I,
)
_UPDATE = re.compile(
    r"\b(?P<field>project\s*name|project_name|name|customer|start\s*date|start_date|location|status|notes?)"
    r"\s*(?:to|is|=|:)\s*(?P<value>.+?)"
    r"(?=\s+(?:and|,)\s+(?:project\s*name|customer|status|location|notes?|start)|$)",
    re.I,
)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().strip("\"'")
    return text or None


def extract_optionals(text: str) -> tuple[dict[str, str], str]:
    remaining = text.strip()
    found: dict[str, str] = {}
    for pattern, key in (
        (_STATUS, "status"),
        (_LOCATION, "location"),
        (_START, "start_date"),
        (_NOTES, "notes"),
    ):
        match = pattern.search(remaining)
        if not match:
            continue
        value = _clean(match.group(key))
        if value:
            found[key] = value
            remaining = (remaining[: match.start()] + " " + remaining[match.end() :]).strip()
    return found, remaining


def extract_from_text(text: str) -> dict[str, str]:
    raw = text.strip()
    if not raw:
        return {}
    optionals, remaining = extract_optionals(raw)
    required = _extract_required(remaining)
    return {**optionals, **required}


def extract_target_name(text: str) -> str | None:
    match = _TARGET.search(text.strip())
    if not match:
        return None
    name = _clean(match.group("name"))
    if name and name.casefold() not in _SKIP_NAMES:
        return name
    return None


def extract_updates(text: str) -> dict[str, str]:
    updates: dict[str, str] = {}
    for match in _UPDATE.finditer(text.strip()):
        field = _FIELD_LABELS.get(re.sub(r"\s+", " ", match.group("field").strip().casefold()))
        value = _clean(match.group("value"))
        if field and value:
            updates[field] = value
    return updates


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


def _extract_required(raw: str) -> dict[str, str]:
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


def _payload(name: str | None, customer: str | None) -> dict[str, str]:
    result: dict[str, str] = {}
    cleaned_name = _clean(name)
    if cleaned_name and cleaned_name.casefold() not in _SKIP_NAMES:
        result["project_name"] = cleaned_name
    cleaned_customer = _clean(customer)
    if cleaned_customer:
        result["customer"] = cleaned_customer
    return result
