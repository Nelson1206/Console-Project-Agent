# Graph route tests

Data-driven tests for LangGraph paths. Each folder under `tests/cases/` is one graph route. Each JSON file in that folder is one turn on that route.

These tests **do not call Ollama**. Classify and extract results come from the case file. You do not need a running model.

They do invoke the compiled graph, mock the LLM, and use a temporary `projects.json`. That checks routing, replies, dialog state, and writes.

## Requirements

From the project root, with the virtualenv active and the package installed (`pip install -e .`):

```bash
python -m tests
```

pytest is optional:

```bash
pip install -e ".[test]"
python -m pytest
```

## Run

| Command | What it does |
| --- | --- |
| `python -m tests` | Run every case and write a report |
| `python -m tests --list` | Print the case catalog |
| `python -m tests --help` | Show CLI flags |

Exit codes: `0` all selected cases passed, `1` at least one failed, `2` no cases matched the filters.

### Select a subset

Selectors are route folders, case names, or `route/case` ids. A route prefix such as `01` matches `01_create_complete`.

```bash
python -m tests --list
python -m tests 01_create_complete
python -m tests 01 05
python -m tests 01_create_complete/alpha
python -m tests --route 06_update --case unique_customer
```

`--route` and `--case` can be repeated. Positional selectors are OR; `--route` plus `--case` is AND.

pytest equivalents:

```bash
python -m pytest
python -m pytest --route 01_create_complete
python -m pytest --case alpha
python -m pytest -k create_complete
```

## Reports

After a run, the runner writes:

- `tests/reports/latest.md`
- `tests/reports/latest.json`
- a timestamped copy of each (`graph-routes-YYYYMMDD-HHMMSS.*`)

The report covers **only the cases that ran**. Generated reports are gitignored.

## Layout

```text
tests/
  cases/
    01_create_complete/
      _route.json          # expected node path for this folder
      alpha.json           # one case
      beta.json
    02_create_followup/
      ...
  harness.py               # load cases, mock LLM, invoke the graph
  runner.py                # python -m tests
  report.py                # Markdown + JSON report
```

`_route.json` names the route and the default node path:

```json
{
  "route_id": "01_create_complete",
  "title": "Create success: classify -> extract_slots -> create_project",
  "path": ["classify", "extract_slots", "create_project"]
}
```

## Case file

A case is one graph turn. Required pieces are `state.user_input` and enough `llm` data to stand in for the model.

```json
{
  "id": "alpha",
  "description": "Create Alpha / Acme in one sentence (assignment golden path)",
  "state": {
    "user_input": "create a project called Alpha for customer Acme",
    "dialog_state": "idle"
  },
  "llm": {
    "classify": "create",
    "extract": {
      "project_name": "Alpha",
      "customer": "Acme"
    }
  },
  "expect": {
    "last_node": "create_project",
    "reply": "Done. Created project \"Alpha\" for customer Acme.",
    "storage_count": 1
  }
}
```

| Field | Meaning |
| --- | --- |
| `state` | Starting `AgentState` for this turn (`user_input`, `dialog_state`, `draft`, `pending_*`, …) |
| `llm.classify` | Intent returned instead of calling the model |
| `llm.extract` | Slots returned instead of calling the model |
| `llm.classify_error` / `extract_error` | Simulate an LLM failure (optional message fields) |
| `seed_projects` | Records written to the temp store before the turn |
| `corrupt_store` | Write invalid JSON so storage error paths can run |
| `expect` | Assertions after the turn |

If `expect.path` is omitted, the folder `_route.json` path is used.

Useful `expect` keys: `path`, `last_node`, `intent`, `dialog_state`, `reply`, `reply_contains`, `reply_startswith`, `should_exit`, `llm_error`, `selected_id`, `pending_action`, `lookup_name`, `missing_fields`, `draft`, `updates`, `storage_count`, `storage_has`, `storage_not_has`.

## Add a case

1. Pick the folder whose `_route.json` path matches the route you want to test.
2. Add a new `*.json` next to the other cases. Use a new folder (and `_route.json`) only for a new node path.
3. Run that case first: `python -m tests path/to_id` or `python -m tests --route FOLDER --case NAME`.

The next `python -m tests` or `python -m pytest` run picks up new files automatically.

## What is not covered

These tests do not check that a live Ollama model classifies or extracts correctly. For that, run the app against a real model:

```bash
python -m project_agent.main
```
