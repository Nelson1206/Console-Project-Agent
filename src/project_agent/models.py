"""Project dataclass and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

OPTIONAL_FIELDS = ("start_date", "location", "status", "notes")
REQUIRED_FIELDS = ("id", "project_name", "customer", "created_at")
UPDATABLE_FIELDS = ("project_name", "customer") + OPTIONAL_FIELDS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_non_empty(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass
class Project:
    id: str
    project_name: str
    customer: str
    created_at: str
    start_date: str | None = None
    location: str | None = None
    status: str | None = None
    notes: str | None = None

    @classmethod
    def create(
        cls,
        project_name: str,
        customer: str,
        *,
        start_date: str | None = None,
        location: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> Project:
        return cls(
            id=str(uuid4()),
            project_name=_require_non_empty(project_name, "project_name"),
            customer=_require_non_empty(customer, "customer"),
            created_at=utc_now_iso(),
            start_date=_optional_text(start_date),
            location=_optional_text(location),
            status=_optional_text(status),
            notes=_optional_text(notes),
        )

    def to_dict(self) -> dict[str, str]:
        data: dict[str, str] = {
            "id": self.id,
            "project_name": self.project_name,
            "customer": self.customer,
            "created_at": self.created_at,
        }
        for name in OPTIONAL_FIELDS:
            value = getattr(self, name)
            if value is not None:
                data[name] = value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        if not isinstance(data, dict):
            raise ValueError("project record must be an object")
        missing = [name for name in REQUIRED_FIELDS if name not in data]
        if missing:
            raise ValueError(f"project record missing fields: {', '.join(missing)}")
        return cls(
            id=_require_non_empty(data["id"], "id"),
            project_name=_require_non_empty(data["project_name"], "project_name"),
            customer=_require_non_empty(data["customer"], "customer"),
            created_at=_require_non_empty(data["created_at"], "created_at"),
            start_date=_optional_text(data.get("start_date")),
            location=_optional_text(data.get("location")),
            status=_optional_text(data.get("status")),
            notes=_optional_text(data.get("notes")),
        )

    def apply_updates(self, fields_to_update: dict[str, Any]) -> Project:
        values = {item.name: getattr(self, item.name) for item in fields(self)}
        for key, raw in fields_to_update.items():
            if key not in UPDATABLE_FIELDS:
                continue
            if key in ("project_name", "customer"):
                values[key] = _require_non_empty(raw, key)
            else:
                values[key] = _optional_text(raw)
        return Project(**values)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("optional fields must be strings")
    stripped = value.strip()
    return stripped or None
