"""Write Markdown and JSON reports for Graph route cases."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from tests.harness import CaseResult

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def write_reports(results: list[CaseResult], reports_dir: Path | None = None) -> dict[str, Path]:
    out_dir = reports_dir or REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = _payload(results, generated)
    json_path = out_dir / "latest.json"
    md_path = out_dir / "latest.md"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    stamped_json = out_dir / f"graph-routes-{stamp}.json"
    stamped_md = out_dir / f"graph-routes-{stamp}.md"
    json_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    md_text = _render_markdown(payload)
    for path in (json_path, stamped_json):
        path.write_text(json_text, encoding="utf-8")
    for path in (md_path, stamped_md):
        path.write_text(md_text, encoding="utf-8")
    return {
        "json": json_path,
        "markdown": md_path,
        "json_stamped": stamped_json,
        "markdown_stamped": stamped_md,
    }


def _payload(results: list[CaseResult], generated: str) -> dict:
    passed = sum(1 for item in results if item.ok)
    failed = len(results) - passed
    by_route: dict[str, dict] = defaultdict(lambda: {"title": "", "total": 0, "passed": 0, "failed": 0})
    cases = []
    for item in results:
        route = by_route[item.spec.route_id]
        route["title"] = item.spec.route_title
        route["total"] += 1
        route["passed" if item.ok else "failed"] += 1
        cases.append(
            {
                "id": item.spec.id,
                "route_id": item.spec.route_id,
                "route_title": item.spec.route_title,
                "description": item.spec.description,
                "source": str(item.spec.source).replace("\\", "/"),
                "ok": item.ok,
                "expected_path": item.spec.expect.get("path") or item.spec.path,
                "actual_path": item.actual_path,
                "last_node": item.actual_state.get("last_node"),
                "reply": item.actual_state.get("reply"),
                "errors": item.errors,
                "elapsed_ms": item.elapsed_ms,
            }
        )
    return {
        "generated_at": generated,
        "summary": {"total": len(results), "passed": passed, "failed": failed},
        "routes": [
            {"route_id": route_id, **stats}
            for route_id, stats in sorted(by_route.items())
        ],
        "cases": cases,
    }


def _render_markdown(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# Graph route test report",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Total: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "",
        "## Route summary",
        "",
        "| Folder | Title | Passed | Failed | Total |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for route in payload["routes"]:
        lines.append(
            f"| `{route['route_id']}` | {route['title']} | {route['passed']} | "
            f"{route['failed']} | {route['total']} |"
        )
    lines.extend(["", "## Case details", ""])
    for case in payload["cases"]:
        status = "PASS" if case["ok"] else "FAIL"
        expected = " -> ".join(case["expected_path"] or [])
        actual = " -> ".join(case["actual_path"] or [])
        lines.extend(
            [
                f"### {case['id']} — {status}",
                "",
                f"- Description: {case['description']}",
                f"- Expected path: `{expected}`",
                f"- Actual path: `{actual}`",
                f"- last_node: `{case['last_node']}`",
            ]
        )
        if case["reply"]:
            reply = str(case["reply"]).replace("\n", " / ")
            lines.append(f"- reply: {reply}")
        if case["errors"]:
            lines.append("- Errors:")
            for error in case["errors"]:
                lines.append(f"  - {error}")
        lines.append("")
    return "\n".join(lines)
