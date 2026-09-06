"""Read route-folder cases, run them, and export a report."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.harness import (
    CaseResult,
    filter_cases,
    format_case_catalog,
    load_cases,
    run_case,
)
from tests.report import write_reports


def run_cases(specs) -> list[CaseResult]:
    results: list[CaseResult] = []
    for spec in specs:
        started = time.perf_counter()
        with TemporaryDirectory(prefix="project-agent-case-") as tmp:
            result = run_case(spec, Path(tmp))
        result.elapsed_ms = (time.perf_counter() - started) * 1000
        results.append(result)
        mark = "PASS" if result.ok else "FAIL"
        print(f"[{mark}] {spec.id} — {spec.description}")
        for error in result.errors:
            print(f"       {error}")
    return results


def run_all(cases_root: Path | None = None) -> list[CaseResult]:
    return run_cases(load_cases(cases_root))


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tests",
        description="Run Graph route cases and write tests/reports/latest.md.",
    )
    parser.add_argument(
        "selectors",
        nargs="*",
        help="Route folder, case name, or route/case id (repeatable).",
    )
    parser.add_argument(
        "-r",
        "--route",
        action="append",
        default=[],
        metavar="ROUTE",
        help="Run only this route folder. Repeat to select more than one.",
    )
    parser.add_argument(
        "-c",
        "--case",
        action="append",
        default=[],
        metavar="CASE",
        help="Run only this case name or route/case id. Repeat to select more.",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List matching cases and exit without running them.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    args = _parse_args(argv)
    available = load_cases()
    selected = filter_cases(
        available,
        selectors=args.selectors,
        routes=args.route,
        names=args.case,
    )
    if not selected:
        print("No cases matched the given filters.", file=sys.stderr)
        print(file=sys.stderr)
        print("Available cases:", file=sys.stderr)
        print(format_case_catalog(available), file=sys.stderr)
        return 2
    if args.list:
        print(format_case_catalog(selected))
        return 0
    results = run_cases(selected)
    paths = write_reports(results)
    summary_passed = sum(1 for item in results if item.ok)
    print()
    print(f"{summary_passed}/{len(results)} passed")
    print(f"Markdown report: {paths['markdown']}")
    print(f"JSON report: {paths['json']}")
    return 0 if summary_passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
