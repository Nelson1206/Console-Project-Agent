"""JSON persistence for the project list."""

from __future__ import annotations

import json
import os
from pathlib import Path

from project_agent.models import Project

DEFAULT_STORAGE_PATH = Path("data/projects.json")


class StorageError(Exception):
    """Raised when the JSON store cannot be read or a record is missing."""


def get_storage_path() -> Path:
    raw = os.getenv("PROJECTS_JSON_PATH")
    return Path(raw) if raw else DEFAULT_STORAGE_PATH


def load_projects(path: Path | None = None) -> list[Project]:
    store_path = path or get_storage_path()
    if not store_path.exists():
        return []
    try:
        text = store_path.read_text(encoding="utf-8")
        payload = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"Project data file is corrupt or unreadable: {store_path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("projects"), list):
        raise StorageError(f"Project data file is corrupt or unreadable: {store_path}")
    try:
        return [Project.from_dict(item) for item in payload["projects"]]
    except (TypeError, ValueError) as exc:
        raise StorageError(f"Project data file is corrupt or unreadable: {store_path}") from exc


def save_projects(projects: list[Project], path: Path | None = None) -> None:
    store_path = path or get_storage_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"projects": [project.to_dict() for project in projects]}
    store_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_project(project: Project, path: Path | None = None) -> Project:
    store_path = path or get_storage_path()
    projects = load_projects(store_path)
    projects.append(project)
    save_projects(projects, store_path)
    return project


def get_by_name(name: str, path: Path | None = None) -> list[Project]:
    needle = name.strip().casefold()
    return [project for project in load_projects(path) if project.project_name.casefold() == needle]


def get_by_id(project_id: str, path: Path | None = None) -> Project | None:
    for project in load_projects(path):
        if project.id == project_id:
            return project
    return None


def update_project(project_id: str, fields: dict, path: Path | None = None) -> Project:
    store_path = path or get_storage_path()
    projects = load_projects(store_path)
    for index, project in enumerate(projects):
        if project.id != project_id:
            continue
        updated = project.apply_updates(fields)
        projects[index] = updated
        save_projects(projects, store_path)
        return updated
    raise StorageError(f"No project found with id {project_id}")


def delete_project(project_id: str, path: Path | None = None) -> Project:
    store_path = path or get_storage_path()
    projects = load_projects(store_path)
    for index, project in enumerate(projects):
        if project.id != project_id:
            continue
        deleted = projects.pop(index)
        save_projects(projects, store_path)
        return deleted
    raise StorageError(f"No project found with id {project_id}")
