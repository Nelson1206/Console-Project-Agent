"""Load route-folder cases, mock the LLM, and invoke one LangGraph turn."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

from project_agent.graph import compile_graph
from project_agent.llm import LLMError
from project_agent.storage import StorageError, load_projects

CASES_ROOT = Path(__file__).resolve().parent / "cases"
ROUTE_META_NAME = "_route.json"
DEFAULT_LLM_ERROR = "The language model request failed. Please try again."


@dataclass
class CaseSpec:
    id: str
    route_id: str
    route_title: str
    description: str
    path: list[str]
    state: dict[str, Any]
    llm: dict[str, Any]
    seed_projects: list[dict[str, Any]]
    corrupt_store: bool
    expect: dict[str, Any]
    source: Path


@dataclass
class CaseResult:
    spec: CaseSpec
    ok: bool
    actual_path: list[str] = field(default_factory=list)
    actual_state: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def load_cases(cases_root: Path | None = None) -> list[CaseSpec]:
    root = cases_root or CASES_ROOT
    cases: list[CaseSpec] = []
    for folder in sorted(path for path in root.iterdir() if path.is_dir()):
        meta_path = folder / ROUTE_META_NAME
        if not meta_path.exists():
            raise FileNotFoundError(f"Route folder missing {ROUTE_META_NAME}: {folder}")
        meta = _read_json(meta_path)
        route_id = str(meta.get("route_id") or folder.name)
        route_title = str(meta.get("title") or route_id)
        default_path = list(meta.get("path") or [])
        for case_path in sorted(folder.glob("*.json")):
            if case_path.name == ROUTE_META_NAME:
                continue
            payload = _read_json(case_path)
            case_id = str(payload.get("id") or case_path.stem)
            cases.append(
                CaseSpec(
                    id=f"{route_id}/{case_id}",
                    route_id=route_id,
                    route_title=route_title,
                    description=str(payload.get("description") or case_id),
                    path=list(payload.get("path") or default_path),
                    state=dict(payload.get("state") or {}),
                    llm=dict(payload.get("llm") or {}),
                    seed_projects=list(payload.get("seed_projects") or []),
                    corrupt_store=bool(payload.get("corrupt_store")),
                    expect=dict(payload.get("expect") or {}),
                    source=case_path,
                )
            )
    return cases


def case_name(spec: CaseSpec) -> str:
    return spec.id.rsplit("/", 1)[-1]


def filter_cases(
    cases: list[CaseSpec],
    *,
    selectors: list[str] | None = None,
    routes: list[str] | None = None,
    names: list[str] | None = None,
) -> list[CaseSpec]:
    selected = list(cases)
    if selectors:
        selected = [spec for spec in selected if any(_matches_selector(spec, item) for item in selectors)]
    if routes:
        selected = [spec for spec in selected if any(_matches_route(spec, item) for item in routes)]
    if names:
        selected = [spec for spec in selected if any(_matches_name(spec, item) for item in names)]
    return selected


def format_case_catalog(cases: list[CaseSpec]) -> str:
    lines: list[str] = []
    current = ""
    for spec in cases:
        if spec.route_id != current:
            current = spec.route_id
            lines.append(f"{spec.route_id}  {spec.route_title}")
        lines.append(f"  {case_name(spec)}  {spec.description}")
    return "\n".join(lines)


def _matches_selector(spec: CaseSpec, selector: str) -> bool:
    needle = selector.strip()
    if not needle:
        return False
    return _matches_route(spec, needle) or _matches_name(spec, needle)


def _matches_route(spec: CaseSpec, selector: str) -> bool:
    needle = selector.strip()
    return spec.route_id == needle or spec.route_id.startswith(f"{needle}_")


def _matches_name(spec: CaseSpec, selector: str) -> bool:
    needle = selector.strip()
    return spec.id == needle or case_name(spec) == needle


def run_case(spec: CaseSpec, tmp_dir: Path) -> CaseResult:
    store_path = tmp_dir / "projects.json"
    _prepare_store(store_path, spec)
    env = {**os.environ, "PROJECTS_JSON_PATH": str(store_path)}

    def fake_classify(*_args: Any, **_kwargs: Any) -> str:
        if spec.llm.get("classify_error"):
            raise LLMError(str(spec.llm.get("classify_error_message") or DEFAULT_LLM_ERROR))
        intent = spec.llm.get("classify")
        if not isinstance(intent, str) or not intent:
            raise AssertionError(f"{spec.id}: llm.classify is required unless classify_error is set")
        return intent

    def fake_extract(*_args: Any, **_kwargs: Any) -> dict[str, str]:
        if spec.llm.get("extract_error"):
            raise LLMError(str(spec.llm.get("extract_error_message") or DEFAULT_LLM_ERROR))
        raw = spec.llm.get("extract") or {}
        return {key: value for key, value in raw.items() if isinstance(value, str) and value.strip()}

    with (
        patch.dict(os.environ, env, clear=True),
        patch("project_agent.nodes.classify_with_llm", side_effect=fake_classify),
        patch("project_agent.nodes.extract_with_llm", side_effect=fake_extract),
    ):
        actual_state, actual_path = _invoke_turn(spec.state)

    errors = _check_expect(spec, actual_state, actual_path, store_path)
    return CaseResult(
        spec=spec,
        ok=not errors,
        actual_path=actual_path,
        actual_state=actual_state,
        errors=errors,
    )


def _invoke_turn(state: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    graph = compile_graph()
    path: list[str] = []
    merged = dict(state)
    for chunk in graph.stream(state, stream_mode="updates"):
        for node_name, update in chunk.items():
            path.append(node_name)
            if isinstance(update, dict):
                merged.update(update)
    return merged, path


def _prepare_store(store_path: Path, spec: CaseSpec) -> None:
    store_path.parent.mkdir(parents=True, exist_ok=True)
    if spec.corrupt_store:
        store_path.write_text("{not-json", encoding="utf-8")
        return
    if spec.seed_projects:
        store_path.write_text(
            json.dumps({"projects": spec.seed_projects}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def _check_expect(
    spec: CaseSpec,
    state: dict[str, Any],
    path: list[str],
    store_path: Path,
) -> list[str]:
    expect = spec.expect
    errors: list[str] = []
    expected_path = list(expect.get("path") or spec.path)
    if expected_path and path != expected_path:
        errors.append(f"path: expected {expected_path}, got {path}")
    _eq(errors, "last_node", expect, state.get("last_node"))
    _eq(errors, "intent", expect, state.get("intent"))
    _eq(errors, "dialog_state", expect, state.get("dialog_state"))
    _eq(errors, "should_exit", expect, bool(state.get("should_exit")))
    _eq(errors, "llm_error", expect, bool(state.get("llm_error")))
    _eq(errors, "selected_id", expect, state.get("selected_id") or "")
    _eq(errors, "pending_action", expect, state.get("pending_action") or "")
    _eq(errors, "lookup_name", expect, state.get("lookup_name") or "")
    if "reply" in expect and state.get("reply") != expect["reply"]:
        errors.append(f"reply: expected {expect['reply']!r}, got {state.get('reply')!r}")
    if "reply_contains" in expect:
        needle = str(expect["reply_contains"])
        reply = str(state.get("reply") or "")
        if needle not in reply:
            errors.append(f"reply_contains: {needle!r} not in {reply!r}")
    if "reply_startswith" in expect:
        prefix = str(expect["reply_startswith"])
        reply = str(state.get("reply") or "")
        if not reply.startswith(prefix):
            errors.append(f"reply_startswith: {reply!r} does not start with {prefix!r}")
    if "missing_fields" in expect and list(state.get("missing_fields") or []) != list(
        expect["missing_fields"]
    ):
        errors.append(
            f"missing_fields: expected {expect['missing_fields']}, got {state.get('missing_fields')}"
        )
    if "draft" in expect and dict(state.get("draft") or {}) != dict(expect["draft"]):
        errors.append(f"draft: expected {expect['draft']}, got {state.get('draft')}")
    if "updates" in expect and dict(state.get("updates") or {}) != dict(expect["updates"]):
        errors.append(f"updates: expected {expect['updates']}, got {state.get('updates')}")
    _check_storage(errors, expect, store_path)
    return errors


def _check_storage(errors: list[str], expect: dict[str, Any], store_path: Path) -> None:
    needs_store = any(
        key in expect for key in ("storage_count", "storage_has", "storage_not_has")
    )
    if not needs_store:
        return
    try:
        projects = load_projects(store_path)
    except StorageError:
        errors.append("storage: expected a readable JSON store")
        return
    if "storage_count" in expect and len(projects) != int(expect["storage_count"]):
        errors.append(f"storage_count: expected {expect['storage_count']}, got {len(projects)}")
    records = [
        {"project_name": project.project_name, "customer": project.customer} for project in projects
    ]
    for wanted in expect.get("storage_has") or []:
        if wanted not in records:
            errors.append(f"storage_has: missing {wanted}")
    for unwanted in expect.get("storage_not_has") or []:
        if unwanted in records:
            errors.append(f"storage_not_has: still present {unwanted}")


def _eq(errors: list[str], key: str, expect: dict[str, Any], actual: Any) -> None:
    if key in expect and actual != expect[key]:
        errors.append(f"{key}: expected {expect[key]!r}, got {actual!r}")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Case file must be a JSON object: {path}")
    return payload
