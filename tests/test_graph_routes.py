"""pytest entry: one test per JSON case under tests/cases/."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.harness import load_cases, run_case
from tests import results as results_mod

CASES = load_cases()


@pytest.mark.parametrize("spec", CASES, ids=[item.id for item in CASES])
def test_graph_route_case(spec, tmp_path: Path) -> None:
    result = run_case(spec, tmp_path)
    results_mod.SESSION_RESULTS.append(result)
    assert result.ok, "\n".join(result.errors)
