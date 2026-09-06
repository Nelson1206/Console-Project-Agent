# Plan

Technical design. Behaviour follows `spec.md`. This project talks to Ollama only.

## 1. Architecture

Single-process console: read a stdin line → build State → one LangGraph invoke per turn → print an English reply on stdout → until exit.

```text
main.py (REPL)
    → graph.py (StateGraph compile / invoke)
        → nodes: classify / extract / followup / crud / list / clarify
        → storage.py
        → models.py
    → llm.py (Ollama ChatModel only)
```

Classify, slot extract, follow-up, disambiguation, write, list, and single-record read/update/delete must be identifiable nodes or conditional edges.

## 2. Layout

```text
src/project_agent/
    __init__.py
    main.py
    graph.py
    nodes.py
    models.py
    storage.py
    llm.py
    prompts.py
    slots.py
    replies.py
    state.py
tests/
    cases/
    README.md
data/projects.json
.env.example
requirements.txt
README.md
AI_USAGE.md
specs/
```

Keep one official start command in README, recommended:

```text
python -m project_agent.main
```

## 3. LangGraph workflow

```text
                    ┌─────────────┐
                    │ classify    │
                    └──────┬──────┘
                           │
     create / follow_up    list    get    update    delete    exit    unknown
            │               │       │       │         │        │        │
            ▼               ▼       ▼       ▼         ▼        ▼        ▼
      extract_slots    list_projects  resolve_target ──► action  EXIT  clarify
            │                              │
            ├── complete ──► create_project
            └── missing  ──► ask_followup
```

Shared `resolve_target` for get / update / delete:

- 0 matches → `not_found` reply → END
- 1 match → `get_project` / `update_project` / `delete_project`
- several matches → `ask_disambiguation` → END (next turn carries `pending_action`)

`quit` / `exit` may be handled in the REPL before the graph. All other natural-language lines, including `list projects`, go through the classify node. If `quit` / `exit` enter the graph, set `should_exit=True`.

### 3.1 Nodes

| Node | Responsibility | Side effect |
| --- | --- | --- |
| `classify` | Produce intent; while `collecting` / `disambiguating`, decide new intent vs slot fill / number | none |
| `extract_slots` | LLM-first extract; lock assignment phrases; merge into draft; compute `missing_fields` | none |
| `ask_followup` | List all missing fields (fixed English sentences) | none |
| `create_project` | Build `Project` and append | write JSON |
| `list_projects` | Format from file; empty file uses the fixed empty text | read JSON |
| `resolve_target` | Find projects by name (or disambiguation number) | read JSON |
| `ask_disambiguation` | Fixed collision text | none |
| `get_project` | Show one full record | read |
| `update_project` | Merge fields | write JSON |
| `delete_project` | Remove that `id` | write JSON |
| `clarify_message` | Fixed unknown text | none |
| `llm_error` | Keep the English `reply` already set by classify / extract / resolve | none |
| `exit_node` | `should_exit=True`, reply `Goodbye.` | none |

### 3.2 Conditional edges

From `classify`:

- `create` / `follow_up` → `extract_slots` (`follow_up` only while collecting and the input is a slot fill)
- `list` → `list_projects`
- `get` / `update` / `delete` → `resolve_target`
- `disambiguation_choice` → get/update/delete according to `pending_action`
- `exit` → `exit_node`
- `unknown` → `clarify_message`
- `llm_error` → `llm_error` (classify / extract / resolve already set the English reply)

From `extract_slots`: empty `missing_fields` → `create_project`, else `ask_followup`.

From `resolve_target`: three-way 0 / 1 / many. If `update` has a locked target but empty `updates` → `ask_followup` (ask which fields to change).

Cancel draft on new intent: if `classify` sees `dialog_state` of `collecting` or `disambiguating`, and the intent is create/list/get/update/delete/exit/unknown (and not a bare value or bare number), clear `draft` / `pending_action` first, then route.

## 4. State

```python
class AgentState(TypedDict, total=False):
    user_input: str
    dialog_state: str          # idle | collecting | disambiguating
    intent: str                # create | list | get | update | delete | exit | unknown | follow_up | disambiguation_choice
    draft: dict                # create draft: name/customer/optionals
    missing_fields: list[str]
    updates: dict              # fields to change on update
    pending_action: str        # get | update | delete
    pending_matches: list[dict]
    selected_id: str
    reply: str
    should_exit: bool
```

Persist across turns only: `dialog_state`, `draft`, `updates`, `pending_action`, `pending_matches`, `selected_id`, `lookup_name`, `missing_fields`.  
The project list is owned by the JSON file, not long-lived in State.

## 5. JSON schema

Default path `data/projects.json`, overridable with `PROJECTS_JSON_PATH`.

```json
{
  "projects": [
    {
      "id": "01HZXEXAMPLE00000000000000",
      "project_name": "Alpha",
      "customer": "Acme",
      "created_at": "2026-09-05T12:00:00+00:00",
      "start_date": "2026-09-01",
      "location": "London",
      "status": "active",
      "notes": "kickoff pending"
    }
  ]
}
```

| Field | Always stored | Notes |
| --- | --- | --- |
| `id` | yes | Generated at create; stable string (ULID or uuid4) |
| `project_name` | yes | non-empty |
| `customer` | yes | non-empty |
| `created_at` | yes | ISO-8601 UTC |
| `start_date` | only if set | string |
| `location` | only if set | string |
| `status` | only if set | string |
| `notes` | only if set | string |

- Missing file → `{ "projects": [] }`
- Write: load → mutate in memory → write whole file
- `list` order = array order
- On corruption raise `StorageError`; nodes turn it into an English reply; **do not** overwrite with an empty file
- Never store API keys

## 6. LLM (Ollama only)

| Variable | Purpose | Example |
| --- | --- | --- |
| `LLM_PROVIDER` | Fixed `ollama` (optional; code defaults to ollama) | `ollama` |
| `LLM_MODEL` | Ollama model name | The verified model documented in README |
| `OLLAMA_BASE_URL` | optional | `http://localhost:11434` |

Do not implement an `OPENROUTER_API_KEY` path. `.env.example` and README list Ollama only.

`llm.py` builds the ChatModel with `langchain-ollama` (or equivalent) only.

### 6.1 Calls

- `classify`: structured output, enum `create`, `list`, `get`, `update`, `delete`, `exit`, `unknown`, `follow_up`. There is no keyword table for `list projects` / `quit` / `exit`. The system prompt includes `dialog_state`, `missing_fields`, and `pending_action`. While collecting a create draft, a bare value (short, no intent verb or field label) is forced to `follow_up` even if the model returns `get`, `delete`, `create`, or `unknown`. While collecting an update (or a `selected_id` is already locked), a labeled field change such as `customer to X` is `follow_up` before the LLM is called; a model `update` is also treated as `follow_up` so the target is kept.
- `extract_slots`: structured output is the primary extractor; required fields may be null; optionals only when present. A regex lock applies only to the assignment phrases `called X for customer Y`, `project X for Y`, and labeled `field is/to` updates; on those keys the lock wins. When merging into draft, do not clear already-filled fields that this turn did not mention. `fill_remaining` may write a bare follow-up value into the one missing required field; it must not swallow commands, labeled clauses, or questions.
- Prompts live in `prompts.py`, English, short, intents and fields only.

### 6.2 Failure

Catch connection refused, missing model, timeout. Set an English `reply`. Do not raise out of the REPL.

## 7. Module contracts

### `models.py`

`Project`: `id`, `project_name`, `customer`, `created_at`; optional fields default `None`. `to_dict` omits `None` optionals.

### `storage.py`

- `load_projects() -> list[Project]`
- `save_projects(projects: list[Project]) -> None`
- `add_project(project: Project) -> None`
- `get_by_name(name: str) -> list[Project]` (case-insensitive)
- `get_by_id(id: str) -> Project | None`
- `update_project(id: str, fields: dict) -> Project`
- `delete_project(id: str) -> Project`

Corruption → `StorageError`.

### `main.py`

```text
loop:
    line = input("> ").strip()
    if not line: continue
    if line.lower() in {"quit", "exit"}:
        print("Goodbye.")
        break
    state = graph.invoke({...cross-turn fields + user_input})
    print(state["reply"])
    if state.get("should_exit"): break
```

Prompt is `> `.

### create success line

```text
Done. Created project "{project_name}" for customer {customer}.
```

This must produce the two AC-1 lines verbatim (no quotes around customer; quotes around project name; match the assignment).

## 8. Dependencies

`requirements.txt`:

- `langchain`
- `langgraph`
- `langchain-ollama`
- `python-dotenv`

Do not list OpenAI / OpenRouter packages. Test libraries are not required to run the app.

## 9. Test strategy

Graph-route cases live under `tests/cases/`. Each folder is one LangGraph path; each JSON file is one turn. The runner mocks classify and extract (does **not** call Ollama), invokes the compiled graph, and writes `tests/reports/latest.md`. Official command: `python -m tests`. Optional pytest extra: `pip install -e ".[test]"`. Tests must not block running the app. Live model behaviour is checked by hand against README sessions.

## 10. README workflow blurb

> Each line of input is one LangGraph turn. A classify node (Ollama structured output) routes to create, list, get, update, delete, follow_up, exit, or unknown. Slot extraction is LLM-first; a small lock keeps the assignment phrases. Missing required fields are listed in one follow-up; a new intent cancels an unfinished draft. Get/update/delete look up by project name; duplicates are disambiguated by number. Successful writes go to data/projects.json. The model is served by local Ollama.

## 11. Implementation order

Skeleton → JSON → graph (stubs OK) → create/list/REPL → wire Ollama → get/update/delete and optional fields → lock English copy to AC-1 → follow-up classify guards → graph-route tests → docs. See `tasks.md`.
