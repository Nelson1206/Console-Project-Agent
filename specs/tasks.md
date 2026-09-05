# Tasks

Checkable implementation list. Definitions of done follow `spec.md` and `constitution.md`.

Status: `- [ ]` todo; `- [x]` done.

## Phase 0 — Spec freeze

- [x] T-001 `specs/constitution.md`
- [x] T-002 `specs/spec.md`
- [x] T-003 `specs/plan.md`
- [x] T-004 this task list
- [x] T-005 Clarify unspecified assignment details and write decisions back (Ollama only, English verbatim, full bonus, duplicate names allowed, collision disambiguation, optionals if present, new intent cancels draft, ask all missing fields, JSON includes id/created_at)

**Done when:** Specs match the confirmed decisions.

## Phase 1 — Project skeleton

- [x] T-010 Create the `src/project_agent/` package skeleton
- [x] T-011 `requirements.txt`: langchain, langgraph, langchain-ollama, python-dotenv (**no** OpenRouter / OpenAI cloud packages)
- [x] T-012 `.env.example`: `LLM_MODEL`, optional `OLLAMA_BASE_URL`; default provider is Ollama
- [x] T-013 `.gitignore`: `.env`, `__pycache__`, virtualenv

**Done when:** `pip install -r requirements.txt` succeeds.

## Phase 2 — Data layer

- [x] T-020 `Project`: `id`, `project_name`, `customer`, `created_at` + optional fields
- [x] T-021 load / save / add / get_by_name / get_by_id / update / delete
- [x] T-022 Missing file is empty; first write creates `data/projects.json`
- [x] T-023 Corrupt JSON raises `StorageError`; do not overwrite with an empty file

**Done when:** A record can be written by hand, found by name (case-insensitive), updated, deleted, and still present after reload.

## Phase 3 — LangGraph skeleton

- [x] T-030 Define `AgentState` (including draft, updates, pending_action, pending_matches)
- [x] T-031 Build the graph: classify routes create/list/get/update/delete/exit/unknown
- [x] T-032 After extract, branch to follow-up or create using `missing_fields`
- [x] T-033 compile + invoke with stubs without crashing

**Done when:** The graph compiles; a fixed stub input reaches the expected node.

## Phase 4 — create / list / follow-up

- [x] T-040 create success line is **verbatim** `Done. Created project "{name}" for customer {customer}.`
- [x] T-041 Missing fields do not write; list all missing fields (spec 5.2 three sentences)
- [x] T-042 Slot-fill can finish create while collecting; **any new intent** drops the draft
- [x] T-043 list: two golden-path projects match the assignment **verbatim**; empty list uses spec 5.4
- [x] T-044 unknown uses spec 5.8

**Done when:** Stubs can walk AC-1 (structure and copy), AC-2, AC-3, AC-4, AC-6, AC-9.

## Phase 5 — REPL

- [x] T-050 Prompt `> `
- [x] T-051 Ignore empty lines; `quit` / `exit` print `Goodbye.` and exit 0
- [x] T-052 Keep dialog_state, draft, pending_* across turns
- [x] T-053 Print reply; exit when `should_exit`

**Done when:** AC-5 passes.

## Phase 6 — Wire Ollama

- [x] T-060 `llm.py` builds an Ollama ChatModel only
- [x] T-061 classify structured output (including get/update/delete)
- [x] T-062 extract required + optional; do not clear filled fields this turn did not mention
- [x] T-063 Ollama down / missing model → English error, stay in the loop
- [x] T-064 Run AC-1 on a real model; reply bodies match verbatim

**Done when:** Natural language can create and list; missing fields are prompted; no cloud key is required.

## Phase 7 — get / update / delete and optional fields

- [x] T-070 Optional fields: save if present in the sentence (AC-10); create does not ask for optionals
- [x] T-071 get: show one record; not found uses `No project named "<name>" was found.`
- [x] T-072 Same name: list candidates, wait for a number; new intent cancels (AC-12)
- [x] T-073 update: change fields and write; target without changes → follow-up (AC-13)
- [x] T-074 delete: delete immediately once resolved, no confirmation (AC-14)

**Done when:** AC-10–AC-15 pass and AC-1 verbatim output still holds.

## Phase 8 — Robustness

- [ ] T-080 Unparseable LLM output → unknown or one retry; do not crash
- [ ] T-081 StorageError → English message; do not overwrite a bad file
- [ ] T-082 Blank slot strings count as missing; keep asking

**Done when:** The process stays up on bad input / bad model / bad JSON.

## Phase 9 — Submission docs

- [ ] T-090 README: install, **Ollama only**, verified model name, single start command, short LangGraph write-up
- [ ] T-091 README may include 2–3 real sessions (at least AC-1; follow-up and delete disambiguation recommended)
- [ ] T-092 `AI_USAGE.md` (Cursor was used; this file is required)
- [ ] T-093 Walk AC-7 from a clean environment using only the README

**Done when:** A reviewer can accept without a cloud key and without asking questions.

## Completion checklist

- [ ] AC-1 three replies match the assignment example verbatim
- [ ] Missing fields listed together; no partial writes (AC-2, AC-3)
- [ ] Empty-store list uses the fixed English line (AC-4)
- [ ] `quit` / `exit` → `Goodbye.` (AC-5)
- [ ] Vague input does not crash (AC-6)
- [ ] Data survives restart (AC-8)
- [ ] New intent during follow-up cancels the draft (AC-9)
- [ ] Optional fields captured if present (AC-10)
- [ ] get / collision disambiguation / update / delete / not found (AC-11–AC-15)
- [ ] README covers Ollama only; `requirements.txt` and `AI_USAGE.md` exist
- [ ] Routing goes through LangGraph; code is modular
