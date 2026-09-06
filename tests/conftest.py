"""pytest hooks for Graph route cases."""

from __future__ import annotations

from pathlib import Path

from tests.harness import filter_cases
from tests.report import write_reports
from tests.results import SESSION_RESULTS


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--route",
        action="append",
        default=[],
        help="Run only this Graph route folder. Repeat to select more than one.",
    )
    parser.addoption(
        "--case",
        action="append",
        default=[],
        help="Run only this case name or route/case id. Repeat to select more.",
    )


def pytest_collection_modifyitems(config, items) -> None:
    routes = list(config.getoption("--route") or [])
    names = list(config.getoption("--case") or [])
    if not routes and not names:
        return
    kept = []
    deselected = []
    for item in items:
        spec = _case_spec(item)
        if spec is None:
            kept.append(item)
            continue
        if filter_cases([spec], routes=routes, names=names):
            kept.append(item)
        else:
            deselected.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = kept


def _case_spec(item):
    callspec = getattr(item, "callspec", None)
    if callspec is None:
        return None
    return callspec.params.get("spec")


def pytest_sessionfinish(session, exitstatus) -> None:
    del session, exitstatus
    if SESSION_RESULTS:
        write_reports(SESSION_RESULTS)


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    del exitstatus, config
    report = Path(__file__).resolve().parent / "reports" / "latest.md"
    if report.exists():
        terminalreporter.write_sep("-", f"Graph route report: {report}")
