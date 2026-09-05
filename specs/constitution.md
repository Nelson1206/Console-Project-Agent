# Constitution

This document locks immutable constraints. If spec, design, and implementation conflict, this file and `Take Home Assignment.md` win.

The “project decisions” below come from spec clarification and override earlier draft assumptions.

## 0. Confirmed project decisions

| Item | Decision |
| --- | --- |
| Scope | Required create / list **plus** bonus: optional fields and get / update / delete |
| LLM | **Ollama only**. Do not implement OpenRouter or any other cloud API path |
| Reply language | **English only** |
| Golden-path wording | create / list success output must match the assignment example **verbatim** |
| Duplicate names | **Allowed**. get / update / delete look up by name; on collision, list candidates and ask the user to specify |
| Optional fields | Capture them on create if present in the sentence; do not prompt when absent |
| Follow-up interrupt | **Any new intent** cancels an unfinished draft |
| Follow-up style | List **all** missing fields in one follow-up |
| JSON record | Required fields + optional fields when set + `id` + `created_at` |

## 1. Evaluation principles (what reviewers will check)

Implementation must pass these five areas independently. Do not sacrifice one minimum standard for another.

| Rank | Area | Non-negotiable definition of done |
| --- | --- | --- |
| 1 | LangGraph | Natural-language requests must be classified, routed, and executed through LangGraph. Intent routing must not be done only with handwritten if/else string matching. |
| 2 | Functionality | create / list / get / update / delete work correctly; missing required fields trigger follow-up; `quit` / `exit` end the app. |
| 3 | Code Quality | Readable modules with separated responsibilities (graph, nodes, storage, models, entrypoint). |
| 4 | Documentation | README lets a reviewer install, configure Ollama, and run without asking questions. AI use must be disclosed honestly in `AI_USAGE.md`. |
| 5 | Robustness | Vague, invalid, or empty input must not crash the app. Replies must be understandable English. |

## 2. Stack constraints

| Layer | Required | Forbidden |
| --- | --- | --- |
| Language | Python 3.10+ | Any other language as the main program |
| Orchestration | LangChain + LangGraph | Prompt-only API calls or a single-file script with no graph as the main path |
| LLM | **Ollama only** | OpenRouter or other cloud APIs as a runtime path |
| Storage | JSON file | Database, cloud table, or memory-only (lost on restart) |
| Interface | Console stdin/stdout | Web / GUI / TUI as the primary interface |

README describes only Ollama install, model pull, and environment variables. Do not require reviewers to obtain a cloud API key.

## 3. Functional constraints

- Intents: `create`, `list`, `get`, `update`, `delete`, plus `exit` and `unknown`.
- `create` must capture at least `project_name` and `customer`. If either is missing, list all missing fields in one follow-up until the project can be saved. Do not persist a partial record.
- Optional fields (`start_date`, `location`, `status`, `notes`) are captured only when present in the input. Do not prompt for them.
- `list` must show all projects in a readable format. If none exist, say so clearly. Golden-path list wording must match the assignment example verbatim.
- `get` / `update` / `delete` look up by `project_name` (case-insensitive). Zero matches: say not found. Multiple matches: list candidates and wait; never silently act on the first match.
- The app runs until the user enters `quit` or `exit` (case-insensitive, surrounding whitespace allowed).
- Unclassifiable input must be handled gracefully: explain in English, hint at available capabilities, then wait for the next line.
- All user-visible replies are English.

## 4. Scope boundary

- **Done for this project:** create, list, get, update, delete, optional fields (capture if present), missing-field follow-up, name disambiguation, JSON persistence, REPL, unknown input, README, `requirements.txt`, `AI_USAGE.md`.
- Build create / list / follow-up / persistence / REPL first, then get / update / delete and optional fields, so the assignment acceptance path is always demonstrable.
- Out of scope: accounts and permissions, Web, databases, cloud LLMs, enforcing unique project names.

## 5. Documentation and AI use

- Submission must include complete source, `README.md`, and `requirements.txt` (or equivalent).
- If any AI tool was used, include `AI_USAGE.md` with: tools, main prompts or chat transcripts, and how AI helped.
- Hiding AI use is worse than honest disclosure.
- README must cover: install, Ollama setup and the model used, how to run, and a short LangGraph workflow. Optional: 2–3 example sessions.
- A reviewer must be able to accept the project from the README alone. Do not depend on verbal extras. Do not require an OpenRouter key.

## 6. Behaviour and quality constraints

- A single bad input must not end the process (`SystemExit` only on an explicit quit/exit path).
- LLM / Ollama failures must produce a readable English error and return to the input loop. Do not die on a traceback.
- The three success lines in the assignment example must be reproducible verbatim (see `spec.md` AC-1).
- Persist immediately after a successful create, update, or delete. After restart, `list` must still show prior data.

## 7. Conflict resolution

1. Required needs and the example session in `Take Home Assignment.md` beat any extra idea.
2. Section 0 of this constitution beats older drafts and implementation convenience.
3. The rest of this constitution beats `plan.md` / `tasks.md`.
4. Behaviour contracts in `spec.md` beat code comments or ad-hoc implementation.
5. To change intents or fields, edit `spec.md` and `plan.md` first, then the code.
